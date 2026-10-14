"""
AgriLens Observation Validation Service.

Authoritative server-side validation for agricultural observations. Produces one of
three outcomes:

  VALID    - no issues detected.
  WARNING  - plausible but unusual; record may be submitted, reviewer must acknowledge.
  INVALID  - logically impossible or out-of-scope; blocked from submission/approval.

Design notes
------------
* Yield anomaly bounds are DATA-DRIVEN, not invented agronomic limits: by default the
  1st and 99th percentiles of plot-level yields observed for the same crop in official
  NISR microdata. Explicit per-crop bounds can be configured by an authorised agronomist
  through ``settings.AGRILENS_VALIDATION['crop_yield_bounds']``.
* If fewer than ``min_reference_obs`` official observations exist for a crop, no yield
  anomaly check is performed and an informational message says so (no fabricated limit).
* Unusual values are never deleted or auto-rejected; they are flagged for human review.
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

# Approximate geographic bounding box of Rwanda (WGS84). Used only to reject coordinates
# that are certainly outside the country; it is not a precise boundary test.
RWANDA_BBOX = {'lat_min': -2.85, 'lat_max': -1.04, 'lon_min': 28.85, 'lon_max': 30.90}

DEFAULTS = {
    'yield_lower_percentile': 1.0,
    'yield_upper_percentile': 99.0,
    'min_reference_obs': 30,
    # {'Maize': {'min': 200, 'max': 9000}} - only set from documented agronomic sources.
    'crop_yield_bounds': {},
}

VALID, WARNING, INVALID = 'VALID', 'WARNING', 'INVALID'
INFO = 'INFO'


def get_config():
    cfg = dict(DEFAULTS)
    cfg.update(getattr(settings, 'AGRILENS_VALIDATION', {}) or {})
    return cfg


def _percentile(sorted_values, pct):
    """Linear-interpolated percentile of a pre-sorted list (pct in 0..100)."""
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    k = (len(sorted_values) - 1) * (pct / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = k - lo
    return float(sorted_values[lo]) + (float(sorted_values[hi]) - float(sorted_values[lo])) * frac


def yield_reference_bounds(crop):
    """
    Returns a dict describing the anomaly bounds for the crop, or a dict with
    ``available=False`` and a reason when no defensible reference exists.
    """
    from apps.data_management.models import ValidatedObservation

    cfg = get_config()
    explicit = (cfg.get('crop_yield_bounds') or {}).get(getattr(crop, 'name', ''))
    if explicit:
        return {
            'available': True,
            'min': float(explicit['min']),
            'max': float(explicit['max']),
            'basis': 'Configured agronomic bounds (AGRILENS_VALIDATION.crop_yield_bounds)',
            'n': None,
        }

    yields = list(
        ValidatedObservation.objects.filter(
            crop=crop, provenance__startswith='NISR_', plot_area_ha__gt=0
        ).order_by('calculated_yield_kg_per_ha').values_list('calculated_yield_kg_per_ha', flat=True)
    )
    n = len(yields)
    if n < cfg['min_reference_obs']:
        return {
            'available': False,
            'n': n,
            'reason': (
                f"Only {n} official observations exist for this crop "
                f"(minimum {cfg['min_reference_obs']}); yield plausibility not assessed."
            ),
        }
    lower = _percentile(yields, cfg['yield_lower_percentile'])
    upper = _percentile(yields, cfg['yield_upper_percentile'])
    return {
        'available': True,
        'min': round(lower, 1),
        'max': round(upper, 1),
        'basis': (
            f"P{cfg['yield_lower_percentile']:g}-P{cfg['yield_upper_percentile']:g} of {n} "
            f"official NISR plot yields for this crop"
        ),
        'n': n,
    }


@dataclass
class ValidationResult:
    messages: list = field(default_factory=list)

    def add(self, level, code, message, field_name=None):
        self.messages.append({'level': level, 'code': code, 'field': field_name, 'message': message})

    @property
    def status(self):
        levels = {m['level'] for m in self.messages}
        if INVALID in levels:
            return INVALID
        if WARNING in levels:
            return WARNING
        return VALID

    @property
    def errors(self):
        return [m for m in self.messages if m['level'] == INVALID]

    @property
    def warnings(self):
        return [m for m in self.messages if m['level'] == WARNING]


def _dec(value):
    if value is None or value == '':
        return None
    return Decimal(str(value))


def validate_observation(data, instance_pk=None):
    """
    Validates a mapping of observation values (form cleaned_data or model attributes).

    Expected keys (missing keys are tolerated): season, district, sector, crop,
    observation_date, plot_area_ha, total_production_kg, loss_quantity_kg,
    quantity_sold_kg, uses_inorganic_fertilizer, inorganic_fertilizer_kg,
    latitude, longitude, observation_reference, created_by.
    """
    from apps.data_management.models import ManualObservation

    result = ValidationResult()
    area = _dec(data.get('plot_area_ha'))
    prod = _dec(data.get('total_production_kg'))
    loss = _dec(data.get('loss_quantity_kg'))
    sold = _dec(data.get('quantity_sold_kg'))
    fert_kg = _dec(data.get('inorganic_fertilizer_kg'))
    lat = _dec(data.get('latitude'))
    lon = _dec(data.get('longitude'))
    obs_date = data.get('observation_date')
    season = data.get('season')
    crop = data.get('crop')
    district = data.get('district')
    sector = data.get('sector')

    # ---- Hard rules (INVALID) -------------------------------------------------
    if area is not None and area <= 0:
        result.add(INVALID, 'AREA_NON_POSITIVE', 'Plot area must be strictly positive (> 0 ha).', 'plot_area_ha')
    if prod is not None and prod < 0:
        result.add(INVALID, 'PRODUCTION_NEGATIVE', 'Production quantity cannot be negative.', 'total_production_kg')
    if loss is not None and loss < 0:
        result.add(INVALID, 'LOSS_NEGATIVE', 'Post-harvest loss quantity cannot be negative.', 'loss_quantity_kg')
    if fert_kg is not None and fert_kg < 0:
        result.add(INVALID, 'FERTILIZER_NEGATIVE', 'Fertilizer quantity cannot be negative.', 'inorganic_fertilizer_kg')
    if isinstance(obs_date, date) and obs_date > timezone.localdate():
        result.add(INVALID, 'DATE_IN_FUTURE', 'Observation date cannot be in the future.', 'observation_date')
    if district is not None and sector is not None and getattr(sector, 'district_id', None) != getattr(district, 'id', None):
        result.add(INVALID, 'SECTOR_DISTRICT_MISMATCH', f"Sector '{sector}' does not belong to {district}.", 'sector')

    if (lat is None) != (lon is None):
        result.add(INVALID, 'GPS_INCOMPLETE', 'Provide both latitude and longitude, or neither.', 'latitude')
    elif lat is not None and lon is not None:
        if not (RWANDA_BBOX['lat_min'] <= float(lat) <= RWANDA_BBOX['lat_max']
                and RWANDA_BBOX['lon_min'] <= float(lon) <= RWANDA_BBOX['lon_max']):
            result.add(INVALID, 'GPS_OUTSIDE_RWANDA',
                       'Coordinates fall outside Rwanda (WGS84 decimal degrees expected, e.g. -1.95, 30.06).',
                       'latitude')

    # ---- Consistency & plausibility (WARNING) ----------------------------------
    if loss is not None and prod is not None and prod > 0 and loss > prod:
        result.add(WARNING, 'LOSS_EXCEEDS_PRODUCTION',
                   f'Reported loss ({loss} kg) exceeds harvested production ({prod} kg). Confirm the loss denominator.',
                   'loss_quantity_kg')
    if sold is not None and prod is not None and sold > prod:
        result.add(WARNING, 'SOLD_EXCEEDS_PRODUCTION',
                   f'Quantity sold ({sold} kg) exceeds harvested production ({prod} kg).', 'quantity_sold_kg')
    if fert_kg and fert_kg > 0 and not data.get('uses_inorganic_fertilizer'):
        result.add(WARNING, 'FERTILIZER_FLAG_INCONSISTENT',
                   'A fertilizer quantity was entered but "inorganic fertilizer used" is not ticked.',
                   'uses_inorganic_fertilizer')
    if prod is not None and prod == 0:
        result.add(WARNING, 'ZERO_PRODUCTION',
                   'Zero harvested production recorded. Confirm crop failure or not-yet-harvested status in remarks.',
                   'total_production_kg')

    if season is not None and isinstance(obs_date, date):
        start, end = getattr(season, 'start_date', None), getattr(season, 'end_date', None)
        if start and end and not (start <= obs_date <= end):
            result.add(WARNING, 'DATE_OUTSIDE_SEASON',
                       f'Observation date {obs_date} is outside the season window ({start} to {end}).',
                       'observation_date')

    if crop is not None and area and area > 0 and prod is not None and prod > 0:
        yld = float(prod / area)
        bounds = yield_reference_bounds(crop)
        if bounds['available']:
            if yld < bounds['min'] or yld > bounds['max']:
                result.add(WARNING, 'YIELD_OUTSIDE_REFERENCE',
                           f"Calculated yield {yld:,.0f} kg/ha is outside the reference range "
                           f"{bounds['min']:,.0f}-{bounds['max']:,.0f} kg/ha ({bounds['basis']}).",
                           'total_production_kg')
        else:
            result.add(INFO, 'YIELD_REFERENCE_UNAVAILABLE', bounds['reason'], 'total_production_kg')

    # ---- Possible duplicates (WARNING) -----------------------------------------
    if season is not None and district is not None and crop is not None and area and prod is not None:
        dup_qs = ManualObservation.objects.filter(
            season=season, district=district, crop=crop,
            plot_area_ha=area, total_production_kg=prod,
        ).exclude(review_status=ManualObservation.ReviewStatus.REJECTED)
        if sector is not None:
            dup_qs = dup_qs.filter(sector=sector)
        if obs_date:
            dup_qs = dup_qs.filter(observation_date=obs_date)
        if instance_pk:
            dup_qs = dup_qs.exclude(pk=instance_pk)
        if dup_qs.exists():
            result.add(WARNING, 'POSSIBLE_DUPLICATE',
                       f'An existing record (#{dup_qs.first().pk}) has identical location, crop, area, production and date.',
                       None)

    ref = (data.get('observation_reference') or '').strip()
    if ref and season is not None:
        ref_qs = ManualObservation.objects.filter(season=season, observation_reference__iexact=ref).exclude(
            review_status=ManualObservation.ReviewStatus.REJECTED)
        if instance_pk:
            ref_qs = ref_qs.exclude(pk=instance_pk)
        if ref_qs.exists():
            result.add(WARNING, 'DUPLICATE_REFERENCE',
                       f"Reference '{ref}' is already used by record #{ref_qs.first().pk} in this season.",
                       'observation_reference')

    return result


def validate_instance(entry):
    """Validates a saved/unsaved ManualObservation instance."""
    data = {
        'season': entry.season if entry.season_id else None,
        'district': entry.district if entry.district_id else None,
        'sector': entry.sector if entry.sector_id else None,
        'crop': entry.crop if entry.crop_id else None,
        'observation_date': entry.observation_date,
        'plot_area_ha': entry.plot_area_ha,
        'total_production_kg': entry.total_production_kg,
        'loss_quantity_kg': entry.loss_quantity_kg,
        'quantity_sold_kg': entry.quantity_sold_kg,
        'uses_inorganic_fertilizer': entry.uses_inorganic_fertilizer,
        'inorganic_fertilizer_kg': entry.inorganic_fertilizer_kg,
        'latitude': entry.latitude,
        'longitude': entry.longitude,
        'observation_reference': entry.observation_reference,
    }
    return validate_observation(data, instance_pk=entry.pk)


def apply_validation(entry):
    """Runs validation and stores the outcome on the instance (does not save)."""
    result = validate_instance(entry)
    entry.validation_status = result.status
    entry.validation_messages = result.messages
    return result
