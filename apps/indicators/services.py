"""
AgriLens Statistical Indicator Service.
Calculates statistically valid, survey-weighted agricultural indicators,
productivity gap analysis, practice adoption rates, and multi-year comparisons.
Enforces strict provenance segregation between official NISR microdata and manual submissions.
"""
from decimal import Decimal
from django.db.models import Sum, Avg, Count, F, ExpressionWrapper, DecimalField, Q
from apps.data_management.models import ValidatedObservation, ManualObservation
from apps.geography.models import District, Province
from apps.agriculture.models import Crop, AgriculturalSeason


class IndicatorService:
    @staticmethod
    def get_national_summary(season_code=None, year=None, crop_name=None, source_policy='official', include_manual=False):
        """
        Calculates high-level national summary indicators.
        Enforces a 3-way source selection policy:
          - 'official': Verified official NISR survey microdata only (survey-weighted ratio estimator)
          - 'manual': Approved authorized manual entries only (unweighted sample aggregation)
          - 'combined': Combined official and approved manual records with explicit provenance accounting
        Supports filtering by crop, agricultural season, and survey year.
        """
        # Backward-compatibility for include_manual boolean
        if include_manual and source_policy == 'official':
            source_policy = 'combined'

        official_qs = ValidatedObservation.objects.filter(provenance__startswith='NISR_')
        manual_qs = ManualObservation.objects.filter(review_status=ManualObservation.ReviewStatus.APPROVED)

        if year:
            official_qs = official_qs.filter(season__year=year)
            manual_qs = manual_qs.filter(season__year=year)
        if season_code:
            official_qs = official_qs.filter(season__season=season_code)
            manual_qs = manual_qs.filter(season__season=season_code)
        if crop_name:
            official_qs = official_qs.filter(crop__name__iexact=crop_name)
            manual_qs = manual_qs.filter(crop__name__iexact=crop_name)

        official_count = official_qs.count()
        manual_count = manual_qs.count()

        if source_policy == 'manual':
            return IndicatorService._calculate_manual_summary(manual_qs, manual_count, official_count)
        elif source_policy == 'combined':
            return IndicatorService._calculate_combined_summary(official_qs, manual_qs, official_count, manual_count)
        else:
            return IndicatorService._calculate_official_summary(official_qs, official_count, manual_count)

    @staticmethod
    def _calculate_official_summary(qs, official_count, manual_count):
        """Official NISR microdata aggregation using survey expansion weights: sum(W*P) / sum(W*A)."""
        total_plots = official_count
        if total_plots == 0:
            return IndicatorService._empty_summary(
                source_policy='official',
                provenance_label='Official NISR Survey Microdata',
                methodological_note='Survey-weighted ratio estimator sum(W*P)/sum(W*A). No observations found for criteria.',
                official_count=0,
                manual_count=manual_count
            )

        prod_weight = ExpressionWrapper(
            F('total_production_kg') * F('sampling_weight'),
            output_field=DecimalField(max_digits=18, decimal_places=4)
        )
        area_weight = ExpressionWrapper(
            F('plot_area_ha') * F('sampling_weight'),
            output_field=DecimalField(max_digits=18, decimal_places=4)
        )
        loss_weight = ExpressionWrapper(
            F('total_loss_kg') * F('sampling_weight'),
            output_field=DecimalField(max_digits=18, decimal_places=4)
        )

        aggs = qs.annotate(
            weighted_prod=prod_weight,
            weighted_area=area_weight,
            weighted_loss=loss_weight
        ).aggregate(
            sum_weighted_prod=Sum('weighted_prod'),
            sum_weighted_area=Sum('weighted_area'),
            sum_weighted_loss=Sum('weighted_loss'),
            improved_seed_count=Count('id', filter=Q(is_improved_seed=True)),
            inorganic_fert_count=Count('id', filter=Q(uses_inorganic_fertilizer=True)),
            organic_fert_count=Count('id', filter=Q(uses_organic_fertilizer=True)),
            irrigation_count=Count('id', filter=Q(is_irrigated=True)),
            mechanization_count=Count('id', filter=Q(uses_mechanization=True)),
            crops_count=Count('crop', distinct=True),
            districts_count=Count('district', distinct=True),
        )

        sum_prod = float(aggs['sum_weighted_prod'] or 0.0)
        sum_area = float(aggs['sum_weighted_area'] or 0.0)
        sum_loss = float(aggs['sum_weighted_loss'] or 0.0)

        weighted_yield = round(sum_prod / sum_area, 2) if sum_area > 0 else 0.0
        total_prod_mt = round(sum_prod / 1000.0, 2)
        total_area_ha = round(sum_area, 2)
        loss_rate = round((sum_loss / (sum_prod + sum_loss)) * 100.0, 2) if (sum_prod + sum_loss) > 0 else 0.0

        return {
            'source_policy': 'official',
            'is_official_only': True,
            'is_manual_only': False,
            'is_combined': False,
            'provenance_label': 'Official NISR Survey Microdata',
            'methodological_note': 'Survey-weighted ratio estimator sum(W*P)/sum(W*A) using official NISR sampling weights.',
            'total_plots': total_plots,
            'official_plots_count': total_plots,
            'manual_plots_count': 0,
            'total_production_mt': total_prod_mt,
            'total_area_ha': total_area_ha,
            'weighted_yield_kg_per_ha': weighted_yield,
            'adoption_rates': {
                'improved_seed': round((aggs['improved_seed_count'] / total_plots) * 100.0, 1),
                'inorganic_fertilizer': round((aggs['inorganic_fert_count'] / total_plots) * 100.0, 1),
                'organic_fertilizer': round((aggs['organic_fert_count'] / total_plots) * 100.0, 1),
                'irrigation': round((aggs['irrigation_count'] / total_plots) * 100.0, 1),
                'mechanization': round((aggs['mechanization_count'] / total_plots) * 100.0, 1),
            },
            'practice_availability': {
                'improved_seed': 'AVAILABLE',
                'inorganic_fertilizer': 'AVAILABLE',
                'organic_fertilizer': 'AVAILABLE',
                'irrigation': 'AVAILABLE' if aggs['irrigation_count'] > 0 else 'UNAVAILABLE_PENDING_REIMPORT',
                'mechanization': 'AVAILABLE' if aggs['mechanization_count'] > 0 else 'UNAVAILABLE_PENDING_REIMPORT',
                'anti_erosion': 'UNAVAILABLE_PENDING_REIMPORT',
            },
            'loss_rate_percentage': loss_rate,
            'priority_crops_count': aggs['crops_count'],
            'districts_covered': aggs['districts_count'],
        }

    @staticmethod
    def _calculate_manual_summary(qs, manual_count, official_count):
        """Approved manual observations summary (unweighted sample aggregation)."""
        total_plots = manual_count
        if total_plots == 0:
            return IndicatorService._empty_summary(
                source_policy='manual',
                provenance_label='Approved Manual Agricultural Entries',
                methodological_note='Unweighted sample aggregation of verified manual entries. No records found.',
                official_count=official_count,
                manual_count=0
            )

        aggs = qs.aggregate(
            sum_prod=Sum('total_production_kg'),
            sum_area=Sum('plot_area_ha'),
            sum_loss=Sum('loss_quantity_kg'),
            improved_seed_count=Count('id', filter=Q(is_improved_seed=True)),
            inorganic_fert_count=Count('id', filter=Q(uses_inorganic_fertilizer=True)),
            organic_fert_count=Count('id', filter=Q(uses_organic_fertilizer=True)),
            irrigation_count=Count('id', filter=Q(is_irrigated=True)),
            mechanization_count=Count('id', filter=Q(uses_mechanization=True)),
            crops_count=Count('crop', distinct=True),
            districts_count=Count('district', distinct=True),
        )

        sum_prod = float(aggs['sum_prod'] or 0.0)
        sum_area = float(aggs['sum_area'] or 0.0)
        sum_loss = float(aggs['sum_loss'] or 0.0)

        weighted_yield = round(sum_prod / sum_area, 2) if sum_area > 0 else 0.0
        total_prod_mt = round(sum_prod / 1000.0, 2)
        total_area_ha = round(sum_area, 2)
        loss_rate = round((sum_loss / (sum_prod + sum_loss)) * 100.0, 2) if (sum_prod + sum_loss) > 0 else 0.0

        return {
            'source_policy': 'manual',
            'is_official_only': False,
            'is_manual_only': True,
            'is_combined': False,
            'provenance_label': 'Approved Manual Agricultural Entries',
            'methodological_note': 'Unweighted observed sample ratio sum(P)/sum(A) from authorized extension submissions.',
            'total_plots': total_plots,
            'official_plots_count': 0,
            'manual_plots_count': total_plots,
            'total_production_mt': total_prod_mt,
            'total_area_ha': total_area_ha,
            'weighted_yield_kg_per_ha': weighted_yield,
            'adoption_rates': {
                'improved_seed': round((aggs['improved_seed_count'] / total_plots) * 100.0, 1),
                'inorganic_fertilizer': round((aggs['inorganic_fert_count'] / total_plots) * 100.0, 1),
                'organic_fertilizer': round((aggs['organic_fert_count'] / total_plots) * 100.0, 1),
                'irrigation': round((aggs['irrigation_count'] / total_plots) * 100.0, 1),
                'mechanization': round((aggs['mechanization_count'] / total_plots) * 100.0, 1),
            },
            'loss_rate_percentage': loss_rate,
            'priority_crops_count': aggs['crops_count'],
            'districts_covered': aggs['districts_count'],
        }

    @staticmethod
    def _calculate_combined_summary(official_qs, manual_qs, official_count, manual_count):
        """Combined official and approved manual data with clear provenance separation."""
        total_plots = official_count + manual_count
        if total_plots == 0:
            return IndicatorService._empty_summary(
                source_policy='combined',
                provenance_label='Combined Analysis (Official NISR + Approved Manual)',
                methodological_note='Dual-source analysis. No observations found for criteria.',
                official_count=0,
                manual_count=0
            )

        # Official weighted aggregates
        prod_weight = ExpressionWrapper(
            F('total_production_kg') * F('sampling_weight'),
            output_field=DecimalField(max_digits=18, decimal_places=4)
        )
        area_weight = ExpressionWrapper(
            F('plot_area_ha') * F('sampling_weight'),
            output_field=DecimalField(max_digits=18, decimal_places=4)
        )
        loss_weight = ExpressionWrapper(
            F('total_loss_kg') * F('sampling_weight'),
            output_field=DecimalField(max_digits=18, decimal_places=4)
        )

        off_aggs = official_qs.annotate(
            weighted_prod=prod_weight,
            weighted_area=area_weight,
            weighted_loss=loss_weight
        ).aggregate(
            sum_prod=Sum('weighted_prod'),
            sum_area=Sum('weighted_area'),
            sum_loss=Sum('weighted_loss'),
            seed=Count('id', filter=Q(is_improved_seed=True)),
            inorg=Count('id', filter=Q(uses_inorganic_fertilizer=True)),
            org=Count('id', filter=Q(uses_organic_fertilizer=True)),
            irrig=Count('id', filter=Q(is_irrigated=True)),
            mech=Count('id', filter=Q(uses_mechanization=True)),
        )

        # Manual unweighted aggregates
        man_aggs = manual_qs.aggregate(
            sum_prod=Sum('total_production_kg'),
            sum_area=Sum('plot_area_ha'),
            sum_loss=Sum('loss_quantity_kg'),
            seed=Count('id', filter=Q(is_improved_seed=True)),
            inorg=Count('id', filter=Q(uses_inorganic_fertilizer=True)),
            org=Count('id', filter=Q(uses_organic_fertilizer=True)),
            irrig=Count('id', filter=Q(is_irrigated=True)),
            mech=Count('id', filter=Q(uses_mechanization=True)),
        )

        total_prod = float(off_aggs['sum_prod'] or 0.0) + float(man_aggs['sum_prod'] or 0.0)
        total_area = float(off_aggs['sum_area'] or 0.0) + float(man_aggs['sum_area'] or 0.0)
        total_loss = float(off_aggs['sum_loss'] or 0.0) + float(man_aggs['sum_loss'] or 0.0)

        seed_total = (off_aggs['seed'] or 0) + (man_aggs['seed'] or 0)
        inorg_total = (off_aggs['inorg'] or 0) + (man_aggs['inorg'] or 0)
        org_total = (off_aggs['org'] or 0) + (man_aggs['org'] or 0)
        irrig_total = (off_aggs['irrig'] or 0) + (man_aggs['irrig'] or 0)
        mech_total = (off_aggs['mech'] or 0) + (man_aggs['mech'] or 0)

        weighted_yield = round(total_prod / total_area, 2) if total_area > 0 else 0.0
        total_prod_mt = round(total_prod / 1000.0, 2)
        total_area_ha = round(total_area, 2)
        loss_rate = round((total_loss / (total_prod + total_loss)) * 100.0, 2) if (total_prod + total_loss) > 0 else 0.0

        crops_count = official_qs.values('crop').distinct().count()
        districts_count = official_qs.values('district').distinct().count()

        return {
            'source_policy': 'combined',
            'is_official_only': False,
            'is_manual_only': False,
            'is_combined': True,
            'provenance_label': 'Combined Analysis (Official NISR + Approved Manual)',
            'methodological_note': f'Combined analysis across {official_count} official NISR records and {manual_count} approved manual submissions.',
            'total_plots': total_plots,
            'official_plots_count': official_count,
            'manual_plots_count': manual_count,
            'total_production_mt': total_prod_mt,
            'total_area_ha': total_area_ha,
            'weighted_yield_kg_per_ha': weighted_yield,
            'adoption_rates': {
                'improved_seed': round((seed_total / total_plots) * 100.0, 1),
                'inorganic_fertilizer': round((inorg_total / total_plots) * 100.0, 1),
                'organic_fertilizer': round((org_total / total_plots) * 100.0, 1),
                'irrigation': round((irrig_total / total_plots) * 100.0, 1),
                'mechanization': round((mech_total / total_plots) * 100.0, 1),
            },
            'practice_availability': {
                'improved_seed': 'AVAILABLE',
                'inorganic_fertilizer': 'AVAILABLE',
                'organic_fertilizer': 'AVAILABLE',
                'irrigation': 'AVAILABLE' if irrig_total > 0 else 'UNAVAILABLE_PENDING_REIMPORT',
                'mechanization': 'AVAILABLE' if mech_total > 0 else 'UNAVAILABLE_PENDING_REIMPORT',
                'anti_erosion': 'UNAVAILABLE_PENDING_REIMPORT',
            },
            'loss_rate_percentage': loss_rate,
            'priority_crops_count': crops_count,
            'districts_covered': districts_count,
        }

    @staticmethod
    def _empty_summary(source_policy, provenance_label, methodological_note, official_count=0, manual_count=0):
        return {
            'source_policy': source_policy,
            'is_official_only': (source_policy == 'official'),
            'is_manual_only': (source_policy == 'manual'),
            'is_combined': (source_policy == 'combined'),
            'provenance_label': provenance_label,
            'methodological_note': methodological_note,
            'total_plots': 0,
            'official_plots_count': official_count,
            'manual_plots_count': manual_count,
            'total_production_mt': 0.0,
            'total_area_ha': 0.0,
            'weighted_yield_kg_per_ha': 0.0,
            'adoption_rates': {
                'improved_seed': 0.0,
                'inorganic_fertilizer': 0.0,
                'organic_fertilizer': 0.0,
                'irrigation': 0.0,
                'mechanization': 0.0,
            },
            'practice_availability': {
                'improved_seed': 'AVAILABLE',
                'inorganic_fertilizer': 'AVAILABLE',
                'organic_fertilizer': 'AVAILABLE',
                'irrigation': 'UNAVAILABLE_PENDING_REIMPORT',
                'mechanization': 'UNAVAILABLE_PENDING_REIMPORT',
                'anti_erosion': 'UNAVAILABLE_PENDING_REIMPORT',
            },
            'loss_rate_percentage': 0.0,
            'priority_crops_count': 0,
            'districts_covered': 0,
        }

    @staticmethod
    def get_district_rankings(crop_name=None, year=2025, season_code='A', min_plots=1, source_policy='official'):
        """
        Ranks districts by crop yield and input adoption rates.
        Applies min_plots threshold to guard against outlier bias from tiny sample sizes.
        Honors source_policy ('official', 'manual', 'combined').
        """
        official_qs = ValidatedObservation.objects.filter(
            provenance__startswith='NISR_',
            season__year=year,
            season__season=season_code
        )
        manual_qs = ManualObservation.objects.filter(
            review_status=ManualObservation.ReviewStatus.APPROVED,
            season__year=year,
            season__season=season_code
        )

        if crop_name and crop_name.strip().lower() not in ('all', 'all priority crops'):
            official_qs = official_qs.filter(crop__name__iexact=crop_name.strip())
            manual_qs = manual_qs.filter(crop__name__iexact=crop_name.strip())

        prod_weight = ExpressionWrapper(
            F('total_production_kg') * F('sampling_weight'),
            output_field=DecimalField(max_digits=18, decimal_places=4)
        )
        area_weight = ExpressionWrapper(
            F('plot_area_ha') * F('sampling_weight'),
            output_field=DecimalField(max_digits=18, decimal_places=4)
        )

        districts_data = []
        if source_policy == 'manual':
            aggs = manual_qs.values(
                'district_id', 'district__name', 'district__code', 'district__province__name'
            ).annotate(
                plots_sampled=Count('id'),
                prod_sum=Sum('total_production_kg'),
                area_sum=Sum('plot_area_ha'),
                loss_sum=Sum('loss_quantity_kg'),
                irrig_cnt=Count('id', filter=Q(is_irrigated=True)),
                seed_cnt=Count('id', filter=Q(is_improved_seed=True)),
                fert_cnt=Count('id', filter=Q(uses_inorganic_fertilizer=True)),
            ).filter(plots_sampled__gte=min_plots)

            for row in aggs:
                plot_count = row['plots_sampled']
                p_tot = float(row['prod_sum'] or 0.0)
                a_tot = float(row['area_sum'] or 0.0)
                l_sum = float(row['loss_sum'] or 0.0)
                districts_data.append({
                    'district_id': row['district_id'],
                    'district_name': row['district__name'],
                    'district_code': row['district__code'],
                    'province_name': row['district__province__name'],
                    'plots_sampled': plot_count,
                    'yield_kg_per_ha': round(p_tot / a_tot, 1) if a_tot > 0 else 0.0,
                    'irrigation_rate': round((row['irrig_cnt'] / plot_count) * 100.0, 1),
                    'improved_seed_rate': round((row['seed_cnt'] / plot_count) * 100.0, 1),
                    'fertilizer_rate': round((row['fert_cnt'] / plot_count) * 100.0, 1),
                    'loss_rate': round((l_sum / (p_tot + l_sum)) * 100.0, 1) if (p_tot + l_sum) > 0 else 0.0,
                })

        elif source_policy == 'combined':
            off_map = {}
            for row in official_qs.annotate(
                weighted_prod=prod_weight, weighted_area=area_weight
            ).values(
                'district_id', 'district__name', 'district__code', 'district__province__name'
            ).annotate(
                cnt=Count('id'),
                p_w=Sum('weighted_prod'),
                a_w=Sum('weighted_area'),
                l_s=Sum('total_loss_kg'),
                irrig=Count('id', filter=Q(is_irrigated=True)),
                seed=Count('id', filter=Q(is_improved_seed=True)),
                fert=Count('id', filter=Q(uses_inorganic_fertilizer=True)),
            ):
                off_map[row['district_id']] = row

            man_map = {}
            for row in manual_qs.values(
                'district_id', 'district__name', 'district__code', 'district__province__name'
            ).annotate(
                cnt=Count('id'),
                p_tot=Sum('total_production_kg'),
                a_tot=Sum('plot_area_ha'),
                l_s=Sum('loss_quantity_kg'),
                irrig=Count('id', filter=Q(is_irrigated=True)),
                seed=Count('id', filter=Q(is_improved_seed=True)),
                fert=Count('id', filter=Q(uses_inorganic_fertilizer=True)),
            ):
                man_map[row['district_id']] = row

            all_dist_ids = set(off_map.keys()) | set(man_map.keys())
            for did in all_dist_ids:
                o = off_map.get(did)
                m = man_map.get(did)
                plot_count = (o['cnt'] if o else 0) + (m['cnt'] if m else 0)
                if plot_count < min_plots:
                    continue

                d_name = (o or m)['district__name']
                d_code = (o or m)['district__code']
                p_name = (o or m)['district__province__name']

                p_tot = float(o['p_w'] or 0.0 if o else 0.0) + float(m['p_tot'] or 0.0 if m else 0.0)
                a_tot = float(o['a_w'] or 0.0 if o else 0.0) + float(m['a_tot'] or 0.0 if m else 0.0)
                l_sum = float(o['l_s'] or 0.0 if o else 0.0) + float(m['l_s'] or 0.0 if m else 0.0)

                irrig_cnt = (o['irrig'] if o else 0) + (m['irrig'] if m else 0)
                seed_cnt = (o['seed'] if o else 0) + (m['seed'] if m else 0)
                fert_cnt = (o['fert'] if o else 0) + (m['fert'] if m else 0)

                districts_data.append({
                    'district_id': did,
                    'district_name': d_name,
                    'district_code': d_code,
                    'province_name': p_name,
                    'plots_sampled': plot_count,
                    'yield_kg_per_ha': round(p_tot / a_tot, 1) if a_tot > 0 else 0.0,
                    'irrigation_rate': round((irrig_cnt / plot_count) * 100.0, 1),
                    'improved_seed_rate': round((seed_cnt / plot_count) * 100.0, 1),
                    'fertilizer_rate': round((fert_cnt / plot_count) * 100.0, 1),
                    'loss_rate': round((l_sum / (p_tot + l_sum)) * 100.0, 1) if (p_tot + l_sum) > 0 else 0.0,
                })

        else:
            # Official NISR microdata (single grouped query)
            aggs = official_qs.annotate(
                weighted_prod=prod_weight,
                weighted_area=area_weight
            ).values(
                'district_id', 'district__name', 'district__code', 'district__province__name'
            ).annotate(
                plots_sampled=Count('id'),
                sum_weighted_prod=Sum('weighted_prod'),
                sum_weighted_area=Sum('weighted_area'),
                irrig_cnt=Count('id', filter=Q(is_irrigated=True)),
                seed_cnt=Count('id', filter=Q(is_improved_seed=True)),
                fert_cnt=Count('id', filter=Q(uses_inorganic_fertilizer=True)),
                loss_sum=Sum('total_loss_kg'),
                prod_sum=Sum('total_production_kg'),
            ).filter(plots_sampled__gte=min_plots)

            for row in aggs:
                plot_count = row['plots_sampled']
                p_weighted = float(row['sum_weighted_prod'] or 0.0)
                a_weighted = float(row['sum_weighted_area'] or 0.0)
                l_sum = float(row['loss_sum'] or 0.0)
                p_raw = float(row['prod_sum'] or 0.0)

                yield_val = round(p_weighted / a_weighted, 1) if a_weighted > 0 else 0.0
                districts_data.append({
                    'district_id': row['district_id'],
                    'district_name': row['district__name'],
                    'district_code': row['district__code'],
                    'province_name': row['district__province__name'],
                    'plots_sampled': plot_count,
                    'yield_kg_per_ha': yield_val,
                    'irrigation_rate': round((row['irrig_cnt'] / plot_count) * 100.0, 1),
                    'improved_seed_rate': round((row['seed_cnt'] / plot_count) * 100.0, 1),
                    'fertilizer_rate': round((row['fert_cnt'] / plot_count) * 100.0, 1),
                    'loss_rate': round((l_sum / (p_raw + l_sum)) * 100.0, 1) if (p_raw + l_sum) > 0 else 0.0,
                })

        # Sort descending by yield
        districts_data.sort(key=lambda x: x['yield_kg_per_ha'], reverse=True)
        return districts_data

    @staticmethod
    def get_productivity_gap(crop_name='Maize', year=2025, season_code='A', min_plots=1, source_policy='official', rankings=None):
        """
        Calculates empirical productivity gap between the top performing district (benchmark)
        and the lagging district for a given crop.
        Requires at least min_plots observations to qualify as an authoritative benchmark.
        Strict policy: if fewer than 2 districts qualify for the requested min_plots threshold,
        returns structured insufficient data result rather than silently degrading to single-plot outliers.
        """
        if rankings is None:
            rankings = IndicatorService.get_district_rankings(
                crop_name=crop_name, year=year, season_code=season_code, min_plots=min_plots, source_policy=source_policy
            )
        elif min_plots > 1:
            rankings = [r for r in rankings if r.get('plots_sampled', 0) >= min_plots]

        if len(rankings) < 2:
            return {
                'is_sufficient_data': False,
                'crop_name': crop_name,
                'year': year,
                'season': season_code,
                'min_plots_threshold': min_plots,
                'qualifying_districts_count': len(rankings),
                'benchmark': None,
                'lagging': None,
                'gap_percentage': 0.0,
                'yield_difference_kg_per_ha': 0.0,
                'reason': f"Insufficient data: fewer than 2 districts have >= {min_plots} plot observations for {crop_name}.",
            }

        benchmark = rankings[0]
        lagging = rankings[-1]

        b_yield = benchmark['yield_kg_per_ha']
        l_yield = lagging['yield_kg_per_ha']

        gap_pct = round(((l_yield - b_yield) / b_yield) * 100.0, 1) if b_yield > 0 else 0.0

        return {
            'is_sufficient_data': True,
            'crop_name': crop_name,
            'year': year,
            'season': season_code,
            'min_plots_threshold': min_plots,
            'qualifying_districts_count': len(rankings),
            'benchmark': benchmark,
            'lagging': lagging,
            'gap_percentage': gap_pct,
            'yield_difference_kg_per_ha': round(b_yield - l_yield, 1),
            'reason': None,
        }

    @staticmethod
    def get_year_over_year_comparison(crop_name='Maize', season_code='A', source_policy='official'):
        """
        Harmonized 2024 vs 2025 comparison for the same agricultural season and crop.
        Enforces statistical comparability check.
        """
        summary_2024 = IndicatorService.get_national_summary(
            season_code=season_code, year=2024, crop_name=crop_name, source_policy=source_policy
        )
        summary_2025 = IndicatorService.get_national_summary(
            season_code=season_code, year=2025, crop_name=crop_name, source_policy=source_policy
        )

        has_data_2024 = summary_2024['total_plots'] > 0
        has_data_2025 = summary_2025['total_plots'] > 0

        if not has_data_2024 or not has_data_2025:
            return {
                'crop': crop_name,
                'season': season_code,
                'is_comparable': False,
                'reason': f"Missing observations in {'2024' if not has_data_2024 else '2025'} for {crop_name} Season {season_code}.",
                'year_2024': summary_2024,
                'year_2025': summary_2025,
                'yield_growth_percentage': 0.0,
            }

        y2024 = summary_2024['weighted_yield_kg_per_ha']
        y2025 = summary_2025['weighted_yield_kg_per_ha']

        growth_pct = round(((y2025 - y2024) / y2024) * 100.0, 1) if y2024 > 0 else 0.0

        return {
            'crop': crop_name,
            'season': season_code,
            'is_comparable': True,
            'reason': None,
            'year_2024': summary_2024,
            'year_2025': summary_2025,
            'yield_growth_percentage': growth_pct,
        }

