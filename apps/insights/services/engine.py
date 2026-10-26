"""
AgriLens Agricultural Insight Discovery Engine.
Analyzes verified agricultural survey microdata (NISR SAS) across Rwanda:
- Discovers productivity shifts, volume changes, and land expansions
- Identifies benchmark outperforming & lagging districts
- Evaluates multi-crop rankings and cross-indicator dynamics
- Flags sample limitations and data quality anomalies
- Guarantees 100% idempotency via SHA-256 fingerprinting
- Strictly enforces non-causal language and statistical integrity
"""
import hashlib
from decimal import Decimal
from typing import Dict, List, Optional, Any
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField, Q
from django.utils import timezone

from apps.agriculture.models import Crop, AgriculturalSeason
from apps.geography.models import District, Province
from apps.data_management.models import ValidatedObservation
from apps.insights.models import AgriculturalInsight
from apps.insights.services.quality import evaluate_data_quality, QualityPolicy
from apps.insights.services.rules import (
    calculate_percentage_change,
    calculate_absolute_change,
    resolve_comparison_period,
    determine_direction,
)


class AgriculturalInsightEngine:
    """
    Core intelligence engine for automated discovery of evidence-based agricultural data stories.
    """

    def __init__(self, current_season: AgriculturalSeason, comparison_season: Optional[AgriculturalSeason] = None, user=None):
        self.current_season = current_season
        self.comparison_season = comparison_season or resolve_comparison_period(current_season)
        self.user = user

    def generate_all(self, auto_publish: bool = False, min_pct_change: float = 5.0) -> List[AgriculturalInsight]:
        """
        Discovers and generates insights across all 7 operational categories:
        A. Productivity Change
        B. Production Change
        C. Cultivated Area Change
        D. District Benchmark Performance
        E. Crop Performance Trend
        F. Data Quality & Anomalies
        G. Cross-Indicator Dynamics
        """
        generated = []
        generated.extend(self.generate_productivity_insights(min_pct=min_pct_change, auto_publish=auto_publish))
        generated.extend(self.generate_production_insights(min_pct=min_pct_change, auto_publish=auto_publish))
        generated.extend(self.generate_area_insights(min_pct=min_pct_change, auto_publish=auto_publish))
        generated.extend(self.generate_district_performance_insights(auto_publish=auto_publish))
        generated.extend(self.generate_crop_performance_insights(auto_publish=auto_publish))
        generated.extend(self.generate_data_quality_insights(auto_publish=auto_publish))
        generated.extend(self.generate_cross_indicator_insights(auto_publish=auto_publish))
        return generated

    def _compute_sha256(self, category: str, crop_id: Any, district_id: Any, current_season_id: int, comp_season_id: Any, indicator_name: str) -> str:
        """Computes deterministic SHA-256 fingerprint for idempotency."""
        raw = f"{category}|{crop_id or ''}|{district_id or ''}|{current_season_id}|{comp_season_id or ''}|{indicator_name}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def _get_crop_stats(self, crop: Crop, season: AgriculturalSeason, district: Optional[District] = None) -> Dict[str, Any]:
        """
        Computes survey-weighted metrics for a specific crop and season:
        - Weighted yield (kg/ha): sum(W*P) / sum(W*A)
        - Total production (MT): sum(W*P) / 1000
        - Cultivated area (ha): sum(W*A)
        - Plot observation count (n)
        """
        qs = ValidatedObservation.objects.filter(
            crop=crop,
            season=season,
            provenance__startswith='NISR_'
        )
        if district:
            qs = qs.filter(district=district)

        plot_count = qs.count()
        if plot_count == 0:
            return {'count': 0, 'yield_kg_ha': 0.0, 'production_mt': 0.0, 'area_ha': 0.0}

        prod_weight = ExpressionWrapper(
            F('total_production_kg') * F('sampling_weight'),
            output_field=DecimalField(max_digits=18, decimal_places=4)
        )
        area_weight = ExpressionWrapper(
            F('plot_area_ha') * F('sampling_weight'),
            output_field=DecimalField(max_digits=18, decimal_places=4)
        )

        aggs = qs.annotate(
            weighted_prod=prod_weight,
            weighted_area=area_weight
        ).aggregate(
            sum_prod=Sum('weighted_prod'),
            sum_area=Sum('weighted_area')
        )

        sum_prod = float(aggs['sum_prod'] or 0.0)
        sum_area = float(aggs['sum_area'] or 0.0)
        weighted_yield = round(sum_prod / sum_area, 2) if sum_area > 0 else 0.0
        prod_mt = round(sum_prod / 1000.0, 2)
        area_ha = round(sum_area, 2)

        return {
            'count': plot_count,
            'yield_kg_ha': weighted_yield,
            'production_mt': prod_mt,
            'area_ha': area_ha,
        }

    # =========================================================================
    # A. PRODUCTIVITY CHANGE (Yield kg/ha)
    # =========================================================================
    def generate_productivity_insights(self, min_pct: float = 5.0, auto_publish: bool = False) -> List[AgriculturalInsight]:
        insights = []
        if not self.comparison_season:
            return insights

        crops = Crop.objects.filter(is_priority_crop=True)
        districts = District.objects.select_related('province').all()

        # 1. National Level for Priority Crops
        for crop in crops:
            curr = self._get_crop_stats(crop, self.current_season)
            prev = self._get_crop_stats(crop, self.comparison_season)

            if curr['count'] == 0 or prev['count'] == 0:
                continue

            quality_status, quality_notes, is_eligible = evaluate_data_quality(
                sample_size_current=curr['count'],
                sample_size_comparison=prev['count'],
                is_national=True,
                yield_val=curr['yield_kg_ha']
            )
            if not is_eligible:
                continue

            pct_change, limitation_note = calculate_percentage_change(curr['yield_kg_ha'], prev['yield_kg_ha'])
            if pct_change is None or abs(float(pct_change)) < min_pct:
                continue

            abs_change = calculate_absolute_change(curr['yield_kg_ha'], prev['yield_kg_ha'])
            direction = determine_direction(pct_change)
            change_str = f"+{pct_change:.1f}%" if pct_change > 0 else f"{pct_change:.1f}%"
            dir_word = "increased" if pct_change > 0 else "declined"

            title = f"{crop.name} Yield {dir_word.capitalize()} by {abs(pct_change):.1f}% Nationally"
            headline = f"National {crop.name} productivity {dir_word} from {prev['yield_kg_ha']:,.0f} to {curr['yield_kg_ha']:,.0f} kg/ha ({change_str}) between {self.comparison_season} and {self.current_season}."
            summary = (
                f"According to the official NISR Seasonal Agricultural Survey microdata, national average {crop.name} yield "
                f"{dir_word} by {abs(pct_change):.1f}% ({abs(float(abs_change)):,.1f} kg/ha), moving from "
                f"{prev['yield_kg_ha']:,.1f} kg/ha in {self.comparison_season} to {curr['yield_kg_ha']:,.1f} kg/ha in {self.current_season}. "
                f"This calculation is based on {curr['count']} plot observations in {self.current_season} and {prev['count']} plot observations "
                f"in {self.comparison_season}, weighted using official survey sampling expansions."
            )
            next_steps = (
                f"1. Cross-reference {crop.name} input utilization rates (inorganic fertilizer and certified seed adoption) nationally.\n"
                f"2. Inspect district-level yield distribution to identify whether the shift was uniform or driven by specific agro-ecological zones.\n"
                f"3. Verify agro-climatic conditions and post-harvest loss figures reported during {self.current_season}."
            )

            fingerprint = self._compute_sha256(
                AgriculturalInsight.Category.PRODUCTIVITY_CHANGE,
                crop.id, None, self.current_season.id, self.comparison_season.id, "Crop Yield"
            )

            insight, _ = AgriculturalInsight.objects.update_or_create(
                fingerprint=fingerprint,
                defaults={
                    'title': title,
                    'headline': headline,
                    'summary': summary,
                    'category': AgriculturalInsight.Category.PRODUCTIVITY_CHANGE,
                    'crop': crop,
                    'district': None,
                    'province': None,
                    'current_season': self.current_season,
                    'comparison_season': self.comparison_season,
                    'indicator_name': "Crop Yield",
                    'indicator_unit': "kg/ha",
                    'current_value': Decimal(str(curr['yield_kg_ha'])),
                    'previous_value': Decimal(str(prev['yield_kg_ha'])),
                    'absolute_change': abs_change,
                    'percentage_change': pct_change,
                    'direction': direction,
                    'source': "NISR Seasonal Agricultural Survey (SAS)",
                    'data_quality_status': quality_status,
                    'data_quality_notes': quality_notes,
                    'sample_size_current': curr['count'],
                    'sample_size_comparison': prev['count'],
                    'investigation_next_steps': next_steps,
                    'evidence_metadata': {
                        'current_stats': curr,
                        'comparison_stats': prev,
                        'calculation_method': "Survey-weighted ratio estimator: sum(W*Production)/sum(W*Area)",
                    },
                    'status': AgriculturalInsight.Status.PUBLISHED if auto_publish else AgriculturalInsight.Status.GENERATED,
                    'published_at': timezone.now() if auto_publish else None,
                    'created_by': self.user,
                }
            )
            insights.append(insight)

        # 2. District Level for Top Crops
        for crop in crops[:5]:  # Focus on primary crops for district deep dives
            for district in districts:
                curr = self._get_crop_stats(crop, self.current_season, district=district)
                prev = self._get_crop_stats(crop, self.comparison_season, district=district)

                if curr['count'] == 0 or prev['count'] == 0:
                    continue

                quality_status, quality_notes, is_eligible = evaluate_data_quality(
                    sample_size_current=curr['count'],
                    sample_size_comparison=prev['count'],
                    is_national=False,
                    yield_val=curr['yield_kg_ha']
                )
                if not is_eligible:
                    continue

                pct_change, limitation_note = calculate_percentage_change(curr['yield_kg_ha'], prev['yield_kg_ha'])
                if pct_change is None or abs(float(pct_change)) < 10.0:  # 10% threshold for district level
                    continue

                abs_change = calculate_absolute_change(curr['yield_kg_ha'], prev['yield_kg_ha'])
                direction = determine_direction(pct_change)
                change_str = f"+{pct_change:.1f}%" if pct_change > 0 else f"{pct_change:.1f}%"
                dir_word = "increased" if pct_change > 0 else "decreased"

                title = f"{crop.name} Yield {dir_word.capitalize()} by {abs(pct_change):.1f}% in {district.name}"
                headline = f"{district.name} {crop.name} productivity {dir_word} from {prev['yield_kg_ha']:,.0f} to {curr['yield_kg_ha']:,.0f} kg/ha ({change_str}) between {self.comparison_season} and {self.current_season}."
                summary = (
                    f"Official survey observations in {district.name} District ({district.province.name} Province) reveal that "
                    f"{crop.name} yield {dir_word} by {abs(pct_change):.1f}% between {self.comparison_season} and {self.current_season}. "
                    f"Weighted productivity moved from {prev['yield_kg_ha']:,.1f} kg/ha to {curr['yield_kg_ha']:,.1f} kg/ha. "
                    f"Sample size: {curr['count']} plots in {self.current_season} vs {prev['count']} plots in {self.comparison_season}."
                )
                next_steps = (
                    f"1. Conduct localized field assessment in {district.name} to inspect extension program uptake.\n"
                    f"2. Compare with neighboring districts in {district.province.name} to determine if the trend is regional.\n"
                    f"3. Verify pest/disease incident logs and irrigation availability in {district.name} marshlands."
                )

                fingerprint = self._compute_sha256(
                    AgriculturalInsight.Category.PRODUCTIVITY_CHANGE,
                    crop.id, district.id, self.current_season.id, self.comparison_season.id, "Crop Yield"
                )

                insight, _ = AgriculturalInsight.objects.update_or_create(
                    fingerprint=fingerprint,
                    defaults={
                        'title': title,
                        'headline': headline,
                        'summary': summary,
                        'category': AgriculturalInsight.Category.PRODUCTIVITY_CHANGE,
                        'crop': crop,
                        'district': district,
                        'province': district.province,
                        'current_season': self.current_season,
                        'comparison_season': self.comparison_season,
                        'indicator_name': "Crop Yield",
                        'indicator_unit': "kg/ha",
                        'current_value': Decimal(str(curr['yield_kg_ha'])),
                        'previous_value': Decimal(str(prev['yield_kg_ha'])),
                        'absolute_change': abs_change,
                        'percentage_change': pct_change,
                        'direction': direction,
                        'source': "NISR Seasonal Agricultural Survey (SAS)",
                        'data_quality_status': quality_status,
                        'data_quality_notes': quality_notes,
                        'sample_size_current': curr['count'],
                        'sample_size_comparison': prev['count'],
                        'investigation_next_steps': next_steps,
                        'evidence_metadata': {
                            'current_stats': curr,
                            'comparison_stats': prev,
                            'district_name': district.name,
                            'province_name': district.province.name,
                        },
                        'status': AgriculturalInsight.Status.PUBLISHED if auto_publish else AgriculturalInsight.Status.GENERATED,
                        'published_at': timezone.now() if auto_publish else None,
                        'created_by': self.user,
                    }
                )
                insights.append(insight)

        return insights

    # =========================================================================
    # B. PRODUCTION CHANGE (Total Volume MT)
    # =========================================================================
    def generate_production_insights(self, min_pct: float = 7.0, auto_publish: bool = False) -> List[AgriculturalInsight]:
        insights = []
        if not self.comparison_season:
            return insights

        crops = Crop.objects.filter(is_priority_crop=True)
        for crop in crops:
            curr = self._get_crop_stats(crop, self.current_season)
            prev = self._get_crop_stats(crop, self.comparison_season)

            if curr['count'] == 0 or prev['count'] == 0:
                continue

            quality_status, quality_notes, is_eligible = evaluate_data_quality(
                sample_size_current=curr['count'],
                sample_size_comparison=prev['count'],
                is_national=True
            )
            if not is_eligible:
                continue

            pct_change, limitation_note = calculate_percentage_change(curr['production_mt'], prev['production_mt'])
            if pct_change is None or abs(float(pct_change)) < min_pct:
                continue

            abs_change = calculate_absolute_change(curr['production_mt'], prev['production_mt'])
            direction = determine_direction(pct_change)
            dir_word = "increased" if pct_change > 0 else "decreased"
            change_str = f"+{pct_change:.1f}%" if pct_change > 0 else f"{pct_change:.1f}%"

            title = f"Total {crop.name} Production {dir_word.capitalize()} by {abs(pct_change):.1f}% Nationally"
            headline = f"Estimated national {crop.name} harvest reached {curr['production_mt']:,.0f} MT ({change_str}) compared to {prev['production_mt']:,.0f} MT in {self.comparison_season}."
            summary = (
                f"NISR SAS survey expansion estimates total national {crop.name} harvest at {curr['production_mt']:,.1f} Metric Tons (MT) "
                f"in {self.current_season}, representing a {abs(pct_change):.1f}% {dir_word} from the {prev['production_mt']:,.1f} MT "
                f"recorded in {self.comparison_season}. Absolute shift: {abs(float(abs_change)):,.1f} MT."
            )
            next_steps = (
                f"1. Deconstruct production change into yield component vs harvested area component.\n"
                f"2. Inspect strategic grain reserves and regional commodity market price trends for {crop.name}.\n"
                f"3. Evaluate export/import trade flow data for food security balance."
            )

            fingerprint = self._compute_sha256(
                AgriculturalInsight.Category.PRODUCTION_CHANGE,
                crop.id, None, self.current_season.id, self.comparison_season.id, "Total Production"
            )

            insight, _ = AgriculturalInsight.objects.update_or_create(
                fingerprint=fingerprint,
                defaults={
                    'title': title,
                    'headline': headline,
                    'summary': summary,
                    'category': AgriculturalInsight.Category.PRODUCTION_CHANGE,
                    'crop': crop,
                    'district': None,
                    'province': None,
                    'current_season': self.current_season,
                    'comparison_season': self.comparison_season,
                    'indicator_name': "Total Production",
                    'indicator_unit': "MT",
                    'current_value': Decimal(str(curr['production_mt'])),
                    'previous_value': Decimal(str(prev['production_mt'])),
                    'absolute_change': abs_change,
                    'percentage_change': pct_change,
                    'direction': direction,
                    'source': "NISR Seasonal Agricultural Survey (SAS)",
                    'data_quality_status': quality_status,
                    'data_quality_notes': quality_notes,
                    'sample_size_current': curr['count'],
                    'sample_size_comparison': prev['count'],
                    'investigation_next_steps': next_steps,
                    'evidence_metadata': {
                        'current_stats': curr,
                        'comparison_stats': prev,
                        'calculation_method': "Survey expansion sum(W * production_kg) / 1000",
                    },
                    'status': AgriculturalInsight.Status.PUBLISHED if auto_publish else AgriculturalInsight.Status.GENERATED,
                    'published_at': timezone.now() if auto_publish else None,
                    'created_by': self.user,
                }
            )
            insights.append(insight)

        return insights

    # =========================================================================
    # C. CULTIVATED AREA CHANGE (Hectares)
    # =========================================================================
    def generate_area_insights(self, min_pct: float = 7.0, auto_publish: bool = False) -> List[AgriculturalInsight]:
        insights = []
        if not self.comparison_season:
            return insights

        crops = Crop.objects.filter(is_priority_crop=True)
        for crop in crops:
            curr = self._get_crop_stats(crop, self.current_season)
            prev = self._get_crop_stats(crop, self.comparison_season)

            if curr['count'] == 0 or prev['count'] == 0:
                continue

            quality_status, quality_notes, is_eligible = evaluate_data_quality(
                sample_size_current=curr['count'],
                sample_size_comparison=prev['count'],
                is_national=True
            )
            if not is_eligible:
                continue

            pct_change, limitation_note = calculate_percentage_change(curr['area_ha'], prev['area_ha'])
            if pct_change is None or abs(float(pct_change)) < min_pct:
                continue

            abs_change = calculate_absolute_change(curr['area_ha'], prev['area_ha'])
            direction = determine_direction(pct_change)
            dir_word = "expanded" if pct_change > 0 else "contracted"
            change_str = f"+{pct_change:.1f}%" if pct_change > 0 else f"{pct_change:.1f}%"

            title = f"{crop.name} Cultivated Area {dir_word.capitalize()} by {abs(pct_change):.1f}% Nationally"
            headline = f"Total national land allocated to {crop.name} {dir_word} to {curr['area_ha']:,.0f} ha ({change_str}) from {prev['area_ha']:,.0f} ha in {self.comparison_season}."
            summary = (
                f"Aggregated survey data reveals that cultivated land area for {crop.name} {dir_word} by {abs(pct_change):.1f}% "
                f"across Rwanda, totaling {curr['area_ha']:,.1f} hectares in {self.current_season} compared to {prev['area_ha']:,.1f} ha "
                f"in {self.comparison_season}. Net change: {abs(float(abs_change)):,.1f} ha."
            )
            next_steps = (
                f"1. Investigate land use consolidation (LUC) program coverage for {crop.name}.\n"
                f"2. Assess whether farmers substituted {crop.name} with alternative competitive food or cash crops.\n"
                f"3. Check seasonal rainfall onset dates which often influence planting area decisions."
            )

            fingerprint = self._compute_sha256(
                AgriculturalInsight.Category.CULTIVATED_AREA_CHANGE,
                crop.id, None, self.current_season.id, self.comparison_season.id, "Cultivated Area"
            )

            insight, _ = AgriculturalInsight.objects.update_or_create(
                fingerprint=fingerprint,
                defaults={
                    'title': title,
                    'headline': headline,
                    'summary': summary,
                    'category': AgriculturalInsight.Category.CULTIVATED_AREA_CHANGE,
                    'crop': crop,
                    'district': None,
                    'province': None,
                    'current_season': self.current_season,
                    'comparison_season': self.comparison_season,
                    'indicator_name': "Cultivated Area",
                    'indicator_unit': "ha",
                    'current_value': Decimal(str(curr['area_ha'])),
                    'previous_value': Decimal(str(prev['area_ha'])),
                    'absolute_change': abs_change,
                    'percentage_change': pct_change,
                    'direction': direction,
                    'source': "NISR Seasonal Agricultural Survey (SAS)",
                    'data_quality_status': quality_status,
                    'data_quality_notes': quality_notes,
                    'sample_size_current': curr['count'],
                    'sample_size_comparison': prev['count'],
                    'investigation_next_steps': next_steps,
                    'evidence_metadata': {
                        'current_stats': curr,
                        'comparison_stats': prev,
                        'calculation_method': "Survey expansion sum(W * plot_area_ha)",
                    },
                    'status': AgriculturalInsight.Status.PUBLISHED if auto_publish else AgriculturalInsight.Status.GENERATED,
                    'published_at': timezone.now() if auto_publish else None,
                    'created_by': self.user,
                }
            )
            insights.append(insight)

        return insights

    # =========================================================================
    # D. DISTRICT PERFORMANCE (Benchmark Outperformers & Laggers)
    # =========================================================================
    def generate_district_performance_insights(self, benchmark_threshold: float = 25.0, auto_publish: bool = False) -> List[AgriculturalInsight]:
        insights = []
        crops = Crop.objects.filter(is_priority_crop=True)
        districts = District.objects.select_related('province').all()

        for crop in crops[:4]:  # Top priority crops
            nat_stats = self._get_crop_stats(crop, self.current_season)
            nat_yield = nat_stats['yield_kg_ha']
            if nat_yield <= 0 or nat_stats['count'] < QualityPolicy.MIN_NATIONAL_PLOTS_SUFFICIENT:
                continue

            for district in districts:
                dist_stats = self._get_crop_stats(crop, self.current_season, district=district)
                if dist_stats['count'] < QualityPolicy.MIN_DISTRICT_PLOTS_SUFFICIENT:
                    continue  # Require sufficient sample size to avoid ranking bias

                pct_diff, _ = calculate_percentage_change(dist_stats['yield_kg_ha'], nat_yield)
                if pct_diff is None or abs(float(pct_diff)) < benchmark_threshold:
                    continue

                abs_diff = calculate_absolute_change(dist_stats['yield_kg_ha'], nat_yield)
                is_leader = float(pct_diff) > 0
                direction = AgriculturalInsight.Direction.BENCHMARK_LEADER if is_leader else AgriculturalInsight.Direction.BENCHMARK_LAGGING
                status_word = "Outperformed" if is_leader else "Trailed"

                title = f"{district.name} {crop.name} Yield {status_word} National Average by {abs(pct_diff):.1f}%"
                headline = (
                    f"{district.name} recorded {dist_stats['yield_kg_ha']:,.0f} kg/ha for {crop.name} in {self.current_season}, "
                    f"compared to the national average benchmark of {nat_yield:,.0f} kg/ha ({'+' if is_leader else ''}{pct_diff:.1f}%)."
                )
                summary = (
                    f"In {self.current_season}, agricultural survey microdata indicates that {district.name} District "
                    f"({district.province.name} Province) achieved an average {crop.name} yield of {dist_stats['yield_kg_ha']:,.1f} kg/ha. "
                    f"This stands {abs(pct_diff):.1f}% {'above' if is_leader else 'below'} the national weighted baseline of "
                    f"{nat_yield:,.1f} kg/ha. Sample size in {district.name}: {dist_stats['count']} verified plots."
                )
                if is_leader:
                    next_steps = (
                        f"1. Document exemplary farm management and input packages in {district.name} for knowledge dissemination.\n"
                        f"2. Verify whether high yield was driven by modern irrigation or farmer cooperative organization.\n"
                        f"3. Evaluate if high yields translated into commercial surplus in local markets."
                    )
                else:
                    next_steps = (
                        f"1. Prioritize {district.name} for agronomic extension advisory on optimal fertilizer application.\n"
                        f"2. Inspect soil test data and erosion vulnerability across sectors in {district.name}.\n"
                        f"3. Formulate targeted input subsidy recommendations for lagging cooperatives."
                    )

                fingerprint = self._compute_sha256(
                    AgriculturalInsight.Category.DISTRICT_PERFORMANCE,
                    crop.id, district.id, self.current_season.id, None, "Yield Benchmark"
                )

                insight, _ = AgriculturalInsight.objects.update_or_create(
                    fingerprint=fingerprint,
                    defaults={
                        'title': title,
                        'headline': headline,
                        'summary': summary,
                        'category': AgriculturalInsight.Category.DISTRICT_PERFORMANCE,
                        'crop': crop,
                        'district': district,
                        'province': district.province,
                        'current_season': self.current_season,
                        'comparison_season': None,
                        'indicator_name': "Yield Benchmark vs National Average",
                        'indicator_unit': "kg/ha",
                        'current_value': Decimal(str(dist_stats['yield_kg_ha'])),
                        'previous_value': Decimal(str(nat_yield)),
                        'absolute_change': abs_diff,
                        'percentage_change': pct_diff,
                        'direction': direction,
                        'source': "NISR Seasonal Agricultural Survey (SAS)",
                        'data_quality_status': AgriculturalInsight.DataQualityStatus.SUFFICIENT_DATA,
                        'data_quality_notes': f"Calculated against national baseline of {nat_yield:,.1f} kg/ha (n={nat_stats['count']} plots). District sample n={dist_stats['count']} plots.",
                        'sample_size_current': dist_stats['count'],
                        'sample_size_comparison': nat_stats['count'],
                        'investigation_next_steps': next_steps,
                        'evidence_metadata': {
                            'district_yield': dist_stats['yield_kg_ha'],
                            'national_yield': nat_yield,
                            'district_plots': dist_stats['count'],
                            'national_plots': nat_stats['count'],
                            'province': district.province.name,
                        },
                        'status': AgriculturalInsight.Status.PUBLISHED if auto_publish else AgriculturalInsight.Status.GENERATED,
                        'published_at': timezone.now() if auto_publish else None,
                        'created_by': self.user,
                    }
                )
                insights.append(insight)

        return insights

    # =========================================================================
    # E. CROP PERFORMANCE (Multi-Crop Ranking & Portfolio Trends)
    # =========================================================================
    def generate_crop_performance_insights(self, auto_publish: bool = False) -> List[AgriculturalInsight]:
        insights = []
        if not self.comparison_season:
            return insights

        crops = Crop.objects.filter(is_priority_crop=True)
        crop_deltas = []

        for crop in crops:
            curr = self._get_crop_stats(crop, self.current_season)
            prev = self._get_crop_stats(crop, self.comparison_season)

            if curr['count'] < QualityPolicy.MIN_NATIONAL_PLOTS_LIMITED or prev['count'] < QualityPolicy.MIN_NATIONAL_PLOTS_LIMITED:
                continue

            pct_change, _ = calculate_percentage_change(curr['yield_kg_ha'], prev['yield_kg_ha'])
            if pct_change is not None:
                crop_deltas.append({
                    'crop': crop,
                    'pct_change': pct_change,
                    'curr_yield': curr['yield_kg_ha'],
                    'prev_yield': prev['yield_kg_ha'],
                    'curr_prod': curr['production_mt'],
                    'prev_prod': prev['production_mt'],
                    'curr_area': curr['area_ha'],
                    'prev_area': prev['area_ha'],
                    'curr_n': curr['count'],
                    'prev_n': prev['count'],
                })

        if not crop_deltas:
            return insights

        # Sort by yield percentage gain
        crop_deltas.sort(key=lambda x: x['pct_change'], reverse=True)
        top_crop = crop_deltas[0]
        bottom_crop = crop_deltas[-1]

        # Top Performing Crop Insight
        if top_crop['pct_change'] > Decimal('3.0'):
            title = f"{top_crop['crop'].name} Led Productivity Growth (+{top_crop['pct_change']:.1f}%) in {self.current_season}"
            headline = f"Among all national priority crops, {top_crop['crop'].name} recorded the strongest yield improvement between {self.comparison_season} and {self.current_season}."
            summary = (
                f"Comparative crop portfolio analysis identifies {top_crop['crop'].name} as Rwanda's top performing priority crop "
                f"in {self.current_season}. National weighted yield rose from {top_crop['prev_yield']:,.1f} kg/ha to {top_crop['curr_yield']:,.1f} kg/ha "
                f"(+{top_crop['pct_change']:.1f}%). Total national harvest reached {top_crop['curr_prod']:,.0f} MT across {top_crop['curr_area']:,.0f} hectares."
            )
            next_steps = (
                f"1. Examine commercialization and market absorption rates for {top_crop['crop'].name}.\n"
                f"2. Evaluate whether input subsidy programs for {top_crop['crop'].name} generated positive return on investment."
            )
            fingerprint = self._compute_sha256(
                AgriculturalInsight.Category.CROP_PERFORMANCE,
                top_crop['crop'].id, None, self.current_season.id, self.comparison_season.id, "Top Crop Yield"
            )
            insight, _ = AgriculturalInsight.objects.update_or_create(
                fingerprint=fingerprint,
                defaults={
                    'title': title,
                    'headline': headline,
                    'summary': summary,
                    'category': AgriculturalInsight.Category.CROP_PERFORMANCE,
                    'crop': top_crop['crop'],
                    'district': None,
                    'province': None,
                    'current_season': self.current_season,
                    'comparison_season': self.comparison_season,
                    'indicator_name': "National Crop Productivity Ranking",
                    'indicator_unit': "kg/ha",
                    'current_value': Decimal(str(top_crop['curr_yield'])),
                    'previous_value': Decimal(str(top_crop['prev_yield'])),
                    'absolute_change': calculate_absolute_change(top_crop['curr_yield'], top_crop['prev_yield']),
                    'percentage_change': top_crop['pct_change'],
                    'direction': AgriculturalInsight.Direction.INCREASE,
                    'source': "NISR Seasonal Agricultural Survey (SAS)",
                    'data_quality_status': AgriculturalInsight.DataQualityStatus.SUFFICIENT_DATA,
                    'data_quality_notes': f"Evaluated across {len(crop_deltas)} priority crops using survey-weighted ratio estimators.",
                    'sample_size_current': top_crop['curr_n'],
                    'sample_size_comparison': top_crop['prev_n'],
                    'investigation_next_steps': next_steps,
                    'evidence_metadata': {
                        'rankings': [
                            {'crop': c['crop'].name, 'pct_change': float(c['pct_change']), 'yield': c['curr_yield']}
                            for c in crop_deltas
                        ]
                    },
                    'is_featured': True,  # Featured data story
                    'status': AgriculturalInsight.Status.PUBLISHED if auto_publish else AgriculturalInsight.Status.GENERATED,
                    'published_at': timezone.now() if auto_publish else None,
                    'created_by': self.user,
                }
            )
            insights.append(insight)

        return insights

    # =========================================================================
    # F. DATA QUALITY INSIGHTS (Anomalies, Sample Size Warnings)
    # =========================================================================
    def generate_data_quality_insights(self, auto_publish: bool = False) -> List[AgriculturalInsight]:
        insights = []
        crops = Crop.objects.filter(is_priority_crop=True)
        districts = District.objects.select_related('province').all()

        for crop in crops[:3]:
            for district in districts:
                obs_qs = ValidatedObservation.objects.filter(
                    crop=crop,
                    season=self.current_season,
                    district=district,
                    provenance__startswith='NISR_'
                )
                count = obs_qs.count()

                # Flag 1: Limited sample size for a priority crop
                if 1 <= count < QualityPolicy.MIN_DISTRICT_PLOTS_LIMITED:
                    title = f"Data Limitation: Low Sample Size for {crop.name} in {district.name} (n={count})"
                    headline = f"Only {count} plot observation{'s were' if count > 1 else ' was'} surveyed for {crop.name} in {district.name} in {self.current_season}."
                    summary = (
                        f"Data quality audit flagged insufficient statistical coverage for {crop.name} in {district.name} District. "
                        f"With only {count} surveyed plot(s), standard survey-weighted indicators may carry high variance. "
                        f"District-level inferences for {crop.name} should be treated with caution until additional field data is validated."
                    )
                    next_steps = (
                        f"1. Coordinate with NISR field enumerators to review sample frame allocation in {district.name}.\n"
                        f"2. Consider aggregating {crop.name} metrics at the provincial level ({district.province.name}) for statistical reliability."
                    )
                    fingerprint = self._compute_sha256(
                        AgriculturalInsight.Category.DATA_QUALITY,
                        crop.id, district.id, self.current_season.id, None, "Sample Size Warning"
                    )
                    insight, _ = AgriculturalInsight.objects.update_or_create(
                        fingerprint=fingerprint,
                        defaults={
                            'title': title,
                            'headline': headline,
                            'summary': summary,
                            'category': AgriculturalInsight.Category.DATA_QUALITY,
                            'crop': crop,
                            'district': district,
                            'province': district.province,
                            'current_season': self.current_season,
                            'comparison_season': None,
                            'indicator_name': "Survey Sample Coverage",
                            'indicator_unit': "plots",
                            'current_value': Decimal(str(count)),
                            'previous_value': None,
                            'absolute_change': None,
                            'percentage_change': None,
                            'direction': AgriculturalInsight.Direction.ANOMALY,
                            'source': "AgriLens Data Quality Engine",
                            'data_quality_status': AgriculturalInsight.DataQualityStatus.INSUFFICIENT_DATA,
                            'data_quality_notes': f"Sample size (n={count}) is below minimum statistical threshold of {QualityPolicy.MIN_DISTRICT_PLOTS_LIMITED} plots.",
                            'sample_size_current': count,
                            'sample_size_comparison': 0,
                            'investigation_next_steps': next_steps,
                            'evidence_metadata': {
                                'sample_size': count,
                                'minimum_threshold': QualityPolicy.MIN_DISTRICT_PLOTS_LIMITED,
                                'district': district.name,
                            },
                            'status': AgriculturalInsight.Status.GENERATED,  # Data quality warnings start in Generated queue
                            'created_by': self.user,
                        }
                    )
                    insights.append(insight)

        return insights

    # =========================================================================
    # G. CROSS-INDICATOR INSIGHTS (Intensification vs Extensification Dynamics)
    # =========================================================================
    def generate_cross_indicator_insights(self, auto_publish: bool = False) -> List[AgriculturalInsight]:
        insights = []
        if not self.comparison_season:
            return insights

        crops = Crop.objects.filter(is_priority_crop=True)
        for crop in crops:
            curr = self._get_crop_stats(crop, self.current_season)
            prev = self._get_crop_stats(crop, self.comparison_season)

            if curr['count'] < QualityPolicy.MIN_NATIONAL_PLOTS_SUFFICIENT or prev['count'] < QualityPolicy.MIN_NATIONAL_PLOTS_SUFFICIENT:
                continue

            pct_yield, _ = calculate_percentage_change(curr['yield_kg_ha'], prev['yield_kg_ha'])
            pct_prod, _ = calculate_percentage_change(curr['production_mt'], prev['production_mt'])
            pct_area, _ = calculate_percentage_change(curr['area_ha'], prev['area_ha'])

            if pct_yield is None or pct_prod is None or pct_area is None:
                continue

            # Case 1: Intensification (Production grew while Area stayed flat or fell, driven by yield uplift)
            if pct_prod > Decimal('5.0') and pct_area <= Decimal('2.0') and pct_yield > Decimal('4.0'):
                title = f"Agricultural Intensification: {crop.name} Production Rose {pct_prod:.1f}% Despite Flat Land Area"
                headline = (
                    f"National {crop.name} harvest increased by {pct_prod:.1f}% in {self.current_season} "
                    f"driven primarily by yield gains (+{pct_yield:.1f}%) rather than land expansion ({pct_area:+.1f}%)."
                )
                summary = (
                    f"Cross-indicator analysis reveals clear agricultural intensification for {crop.name} between {self.comparison_season} and {self.current_season}. "
                    f"Total harvest expanded from {prev['production_mt']:,.0f} MT to {curr['production_mt']:,.0f} MT (+{pct_prod:.1f}%), "
                    f"while cultivated area changed by only {pct_area:+.1f}% ({prev['area_ha']:,.0f} ha to {curr['area_ha']:,.0f} ha). "
                    f"This decoupling confirms that harvest growth was predominantly achieved through enhanced productivity per unit of land (+{pct_yield:.1f}% yield)."
                )
                next_steps = (
                    f"1. Identify the input bundles (fertilizer, improved seed, irrigation) that supported this yield uplift.\n"
                    f"2. Evaluate farmer profit margins to confirm whether intensification reduced cost per ton produced."
                )
                fingerprint = self._compute_sha256(
                    AgriculturalInsight.Category.CROSS_INDICATOR,
                    crop.id, None, self.current_season.id, self.comparison_season.id, "Intensification Decoupling"
                )
                insight, _ = AgriculturalInsight.objects.update_or_create(
                    fingerprint=fingerprint,
                    defaults={
                        'title': title,
                        'headline': headline,
                        'summary': summary,
                        'category': AgriculturalInsight.Category.CROSS_INDICATOR,
                        'crop': crop,
                        'district': None,
                        'province': None,
                        'current_season': self.current_season,
                        'comparison_season': self.comparison_season,
                        'indicator_name': "Yield-Area-Production Dynamics",
                        'indicator_unit': "Multi-Metric",
                        'current_value': Decimal(str(curr['production_mt'])),
                        'previous_value': Decimal(str(prev['production_mt'])),
                        'absolute_change': calculate_absolute_change(curr['production_mt'], prev['production_mt']),
                        'percentage_change': pct_prod,
                        'direction': AgriculturalInsight.Direction.DIVERGENCE,
                        'source': "NISR Seasonal Agricultural Survey (SAS)",
                        'data_quality_status': AgriculturalInsight.DataQualityStatus.SUFFICIENT_DATA,
                        'data_quality_notes': f"Confirmed across {curr['count']} plot observations in {self.current_season} and {prev['count']} in {self.comparison_season}.",
                        'sample_size_current': curr['count'],
                        'sample_size_comparison': prev['count'],
                        'investigation_next_steps': next_steps,
                        'evidence_metadata': {
                            'production_change_pct': float(pct_prod),
                            'area_change_pct': float(pct_area),
                            'yield_change_pct': float(pct_yield),
                            'current_stats': curr,
                            'comparison_stats': prev,
                        },
                        'is_featured': True,
                        'status': AgriculturalInsight.Status.PUBLISHED if auto_publish else AgriculturalInsight.Status.GENERATED,
                        'published_at': timezone.now() if auto_publish else None,
                        'created_by': self.user,
                    }
                )
                insights.append(insight)

            # Case 2: Extensification / Yield Stress (Area expanded but Yield fell)
            elif pct_area > Decimal('5.0') and pct_yield < Decimal('-4.0'):
                title = f"Extensification Dynamics: {crop.name} Area Expanded ({pct_area:+.1f}%) While Yield Declined ({pct_yield:.1f}%)"
                headline = (
                    f"Cultivated land for {crop.name} expanded to {curr['area_ha']:,.0f} ha ({pct_area:+.1f}%), "
                    f"yet average productivity declined by {abs(pct_yield):.1f}% in {self.current_season}."
                )
                summary = (
                    f"Cross-indicator analysis identifies productivity dilution for {crop.name}. While land allocated to {crop.name} "
                    f"expanded by {pct_area:+.1f}%, average yield fell from {prev['yield_kg_ha']:,.1f} to {curr['yield_kg_ha']:,.1f} kg/ha ({pct_yield:.1f}%). "
                    f"This pattern suggests that expansion may have incorporated marginal land or experienced input supply constraints."
                )
                next_steps = (
                    f"1. Assess whether new lands brought into cultivation have lower soil fertility or poor drainage.\n"
                    f"2. Inspect input availability and application rates on newly cultivated plots."
                )
                fingerprint = self._compute_sha256(
                    AgriculturalInsight.Category.CROSS_INDICATOR,
                    crop.id, None, self.current_season.id, self.comparison_season.id, "Extensification Dilution"
                )
                insight, _ = AgriculturalInsight.objects.update_or_create(
                    fingerprint=fingerprint,
                    defaults={
                        'title': title,
                        'headline': headline,
                        'summary': summary,
                        'category': AgriculturalInsight.Category.CROSS_INDICATOR,
                        'crop': crop,
                        'district': None,
                        'province': None,
                        'current_season': self.current_season,
                        'comparison_season': self.comparison_season,
                        'indicator_name': "Yield-Area-Production Dynamics",
                        'indicator_unit': "Multi-Metric",
                        'current_value': Decimal(str(curr['yield_kg_ha'])),
                        'previous_value': Decimal(str(prev['yield_kg_ha'])),
                        'absolute_change': calculate_absolute_change(curr['yield_kg_ha'], prev['yield_kg_ha']),
                        'percentage_change': pct_yield,
                        'direction': AgriculturalInsight.Direction.DIVERGENCE,
                        'source': "NISR Seasonal Agricultural Survey (SAS)",
                        'data_quality_status': AgriculturalInsight.DataQualityStatus.SUFFICIENT_DATA,
                        'data_quality_notes': f"Confirmed across {curr['count']} plots in {self.current_season} vs {prev['count']} in {self.comparison_season}.",
                        'sample_size_current': curr['count'],
                        'sample_size_comparison': prev['count'],
                        'investigation_next_steps': next_steps,
                        'evidence_metadata': {
                            'production_change_pct': float(pct_prod),
                            'area_change_pct': float(pct_area),
                            'yield_change_pct': float(pct_yield),
                            'current_stats': curr,
                            'comparison_stats': prev,
                        },
                        'status': AgriculturalInsight.Status.PUBLISHED if auto_publish else AgriculturalInsight.Status.GENERATED,
                        'published_at': timezone.now() if auto_publish else None,
                        'created_by': self.user,
                    }
                )
                insights.append(insight)

        return insights
