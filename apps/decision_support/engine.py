"""
AgriLens Decision Support Rule Engine.
Deterministic, multi-stakeholder agricultural decision generator grounded in verified NISR/MINAGRI microdata.
Strictly eliminates synthetic scores and enforces data provenance lineage.
"""
from decimal import Decimal
from django.utils import timezone
from apps.agriculture.models import Crop, AgriculturalSeason
from apps.geography.models import District
from apps.indicators.services import IndicatorService
from .models import (
    RecommendationRule,
    Recommendation,
    StakeholderType,
    PriorityLevel,
    RecommendationStatus,
)


class DecisionEngine:
    @staticmethod
    def ensure_default_rules():
        """Bootstraps default institutional decision rules if not present."""
        rules_data = [
            {
                'code': 'MINAGRI_INPUT_GAP_ALERT',
                'title': 'Yield Gap & Input Subsidy Investigation',
                'target_stakeholder': StakeholderType.GOVERNMENT,
                'description': 'Identifies districts lagging significantly behind benchmark yields and evaluates input adoption deficits.',
                'parameters': {'gap_threshold_pct': -30.0, 'min_plots': 3},
            },
            {
                'code': 'BANK_PORTFOLIO_EXPOSURE',
                'title': 'Agricultural Lending Risk & Harvest Loss Notice',
                'target_stakeholder': StakeholderType.BANK,
                'description': 'Flags severe post-harvest losses and seasonal contractions for agricultural lenders. Underwriting notice, not automated denial.',
                'parameters': {'yoy_drop_threshold_pct': -20.0, 'loss_rate_threshold_pct': 15.0},
            },
            {
                'code': 'INSURER_HARVEST_RISK',
                'title': 'Area-Yield Variance & Parametric Verification Flag',
                'target_stakeholder': StakeholderType.INSURER,
                'description': 'Flags severe area-yield deviations from provincial averages for parametric insurance loss verification.',
                'parameters': {'provincial_variance_threshold_pct': -25.0},
            },
            {
                'code': 'AGRIBUS_SUPPLY_DEFICIT',
                'title': 'Supply Chain & Raw Commodity Deficit Notice',
                'target_stakeholder': StakeholderType.AGRIBUSINESS,
                'description': 'Notifies food processors and commodity aggregators of elevated losses and production deficits in supply shed.',
                'parameters': {'loss_rate_threshold_pct': 12.0},
            },
        ]
        created_rules = []
        for r_spec in rules_data:
            rule, _ = RecommendationRule.objects.get_or_create(
                code=r_spec['code'],
                defaults={
                    'title': r_spec['title'],
                    'target_stakeholder': r_spec['target_stakeholder'],
                    'description': r_spec['description'],
                    'parameters': r_spec['parameters'],
                    'version': 1,
                    'is_active': True,
                }
            )
            created_rules.append(rule)
        return created_rules

    @classmethod
    def generate_recommendations(cls, year=2025, season_code='A', source_policy='official', limit_per_rule=5):
        """
        Executes active rules across verified survey microdata and generates structured recommendations.
        Guarantees idempotency via unique natural key checks.
        """
        cls.ensure_default_rules()
        season = AgriculturalSeason.objects.filter(year=year, season=season_code).first()

        priority_crops = Crop.objects.filter(is_priority_crop=True)
        if not priority_crops.exists():
            priority_crops = Crop.objects.all()[:5]

        generated_count = 0
        active_rules = {r.code: r for r in RecommendationRule.objects.filter(is_active=True)}

        for crop in priority_crops:
            rankings = IndicatorService.get_district_rankings(
                crop_name=crop.name, year=year, season_code=season_code, min_plots=1, source_policy=source_policy
            )
            if len(rankings) < 2:
                continue

            top_district = rankings[0]
            top_yield = top_district['yield_kg_per_ha']
            if top_yield <= 0:
                continue

            national_sum = IndicatorService.get_national_summary(
                year=year, season_code=season_code, crop_name=crop.name, source_policy=source_policy
            )
            yoy = IndicatorService.get_year_over_year_comparison(
                crop_name=crop.name, season_code=season_code, source_policy=source_policy
            )
            yoy_growth = yoy.get('yield_growth_percentage', 0.0) if yoy.get('is_comparable') else 0.0

            # ------------------------------------------------------------------
            # 1. MINAGRI Rule: Yield Gap & Input Subsidy Investigation
            # ------------------------------------------------------------------
            rule_minagri = active_rules.get('MINAGRI_INPUT_GAP_ALERT')
            if rule_minagri:
                gap_thresh = rule_minagri.parameters.get('gap_threshold_pct', -30.0)
                min_plots = rule_minagri.parameters.get('min_plots', 3)
                rule_count = 0

                for dist_row in reversed(rankings):
                    if rule_count >= limit_per_rule:
                        break
                    plots = dist_row['plots_sampled']
                    if plots < min_plots:
                        continue

                    d_yield = dist_row['yield_kg_per_ha']
                    gap_pct = round(((d_yield - top_yield) / top_yield) * 100.0, 1)

                    if gap_pct <= gap_thresh:
                        district = District.objects.filter(id=dist_row['district_id']).first()
                        if not district:
                            continue

                        seed_rate = dist_row.get('improved_seed_rate', 0.0)
                        fert_rate = dist_row.get('fertilizer_rate', 0.0)
                        priority = PriorityLevel.CRITICAL if gap_pct <= -45.0 else PriorityLevel.HIGH

                        title = f"Productivity Gap Investigation: {district.name} {crop.name}"
                        problem = (
                            f"{district.name} District recorded an average {crop.name} yield of {d_yield:.0f} kg/ha "
                            f"(based on {plots} survey plots), presenting a {abs(gap_pct):.1f}% yield deficit "
                            f"relative to benchmark district {top_district['district_name']} ({top_yield:.0f} kg/ha). "
                            f"Current recorded technology adoption in {district.name}: improved seed at {seed_rate:.1f}% "
                            f"and inorganic fertilizer at {fert_rate:.1f}%."
                        )
                        rec_text = (
                            f"Deploy MINAGRI and district agronomists to audit Smart Nkunganire subsidy redemption in {district.name}. "
                            f"Initiate soil acidity testing to evaluate lime distribution requirements, and coordinate extension "
                            f"demonstration plots focused on certified {crop.name} varieties adapted to the local agroecological zone."
                        )
                        evidence = {
                            'rule_code': rule_minagri.code,
                            'crop': crop.name,
                            'district_id': district.id,
                            'district_name': district.name,
                            'survey_year': year,
                            'season': season_code,
                            'district_yield_kg_per_ha': d_yield,
                            'benchmark_district': top_district['district_name'],
                            'benchmark_yield_kg_per_ha': top_yield,
                            'gap_percentage': gap_pct,
                            'plots_sampled': plots,
                            'improved_seed_rate': seed_rate,
                            'fertilizer_rate': fert_rate,
                            'provenance': source_policy,
                        }

                        obj, created = Recommendation.objects.get_or_create(
                            rule=rule_minagri,
                            target_stakeholder=rule_minagri.target_stakeholder,
                            district=district,
                            crop=crop,
                            season=season,
                            defaults={
                                'priority': priority,
                                'title': title,
                                'problem_statement': problem,
                                'evidence_json': evidence,
                                'recommendation_text': rec_text,
                                'status': RecommendationStatus.GENERATED,
                            }
                        )
                        if created:
                            generated_count += 1
                        rule_count += 1

            # ------------------------------------------------------------------
            # 2. Bank Rule: Agricultural Lending Risk Notice
            # ------------------------------------------------------------------
            rule_bank = active_rules.get('BANK_PORTFOLIO_EXPOSURE')
            if rule_bank:
                loss_thresh = rule_bank.parameters.get('loss_rate_threshold_pct', 15.0)
                rule_count = 0

                for dist_row in rankings:
                    if rule_count >= limit_per_rule:
                        break
                    loss_rate = dist_row.get('loss_rate', 0.0)
                    if loss_rate >= loss_thresh or yoy_growth <= -20.0:
                        district = District.objects.filter(id=dist_row['district_id']).first()
                        if not district:
                            continue

                        priority = PriorityLevel.HIGH if loss_rate >= 20.0 else PriorityLevel.MEDIUM
                        title = f"Agricultural Lending Exposure Alert: {district.name} {crop.name}"
                        problem = (
                            f"Elevated agricultural credit risk flagged in {district.name} for {crop.name}: "
                            f"Survey-measured post-harvest loss is {loss_rate:.1f}% "
                            f"(national average: {national_sum.get('loss_rate_percentage', 0.0):.1f}%). "
                            f"{f'National seasonal yield contracted by {abs(yoy_growth):.1f}% YoY.' if yoy_growth < 0 else ''} "
                            f"Farmer cash flow and loan repayment capacity may face seasonal compression."
                        )
                        rec_text = (
                            f"Commercial lending institutions (Bank of Kigali, Development Bank of Rwanda, SACCOs) "
                            f"should require agronomist field verification before loan disbursement in {district.name}. "
                            f"Explore mandatory crop insurance integration and structured off-taker contracts to de-risk "
                            f"{crop.name} loans. This notice provides underwriting context and MUST NOT be used for automated loan denial."
                        )
                        evidence = {
                            'rule_code': rule_bank.code,
                            'crop': crop.name,
                            'district_name': district.name,
                            'district_loss_rate': loss_rate,
                            'national_loss_rate': national_sum.get('loss_rate_percentage', 0.0),
                            'yoy_growth_percentage': yoy_growth,
                            'plots_sampled': dist_row['plots_sampled'],
                        }

                        obj, created = Recommendation.objects.get_or_create(
                            rule=rule_bank,
                            target_stakeholder=rule_bank.target_stakeholder,
                            district=district,
                            crop=crop,
                            season=season,
                            defaults={
                                'priority': priority,
                                'title': title,
                                'problem_statement': problem,
                                'evidence_json': evidence,
                                'recommendation_text': rec_text,
                                'status': RecommendationStatus.GENERATED,
                            }
                        )
                        if created:
                            generated_count += 1
                        rule_count += 1

            # ------------------------------------------------------------------
            # 3. Insurer Rule: Area-Yield Parametric Variance Alert
            # ------------------------------------------------------------------
            rule_insurer = active_rules.get('INSURER_HARVEST_RISK')
            if rule_insurer:
                var_thresh = rule_insurer.parameters.get('provincial_variance_threshold_pct', -25.0)
                rule_count = 0

                # Group by province to find provincial average yields
                prov_yields = {}
                for r in rankings:
                    pname = r.get('province_name')
                    if pname not in prov_yields:
                        prov_yields[pname] = []
                    prov_yields[pname].append(r['yield_kg_per_ha'])

                prov_means = {p: sum(vals) / len(vals) for p, vals in prov_yields.items() if vals}

                for dist_row in rankings:
                    if rule_count >= limit_per_rule:
                        break
                    pname = dist_row.get('province_name')
                    p_mean = prov_means.get(pname, 0.0)
                    if p_mean <= 0:
                        continue

                    d_yield = dist_row['yield_kg_per_ha']
                    var_pct = round(((d_yield - p_mean) / p_mean) * 100.0, 1)

                    if var_pct <= var_thresh and dist_row['plots_sampled'] >= 2:
                        district = District.objects.filter(id=dist_row['district_id']).first()
                        if not district:
                            continue

                        title = f"Area-Yield Parametric Verification: {district.name} {crop.name}"
                        problem = (
                            f"Potential insured loss condition identified: {district.name} recorded a {crop.name} "
                            f"yield of {d_yield:.0f} kg/ha, which is {abs(var_pct):.1f}% below the {pname} "
                            f"provincial average ({p_mean:.0f} kg/ha). Suggests localized agronomic or climate stress."
                        )
                        rec_text = (
                            f"Agriculture insurance underwriters should deploy independent loss adjusters to {district.name} "
                            f"to inspect weather station rainfall data and verify potential insured peril triggers. "
                            f"Cross-reference satellite vegetation indices (NDVI) before authorizing indemnity settlements."
                        )
                        evidence = {
                            'rule_code': rule_insurer.code,
                            'crop': crop.name,
                            'district_name': district.name,
                            'province': pname,
                            'district_yield_kg_per_ha': d_yield,
                            'provincial_mean_yield_kg_per_ha': round(p_mean, 1),
                            'variance_percentage': var_pct,
                            'plots_sampled': dist_row['plots_sampled'],
                        }

                        obj, created = Recommendation.objects.get_or_create(
                            rule=rule_insurer,
                            target_stakeholder=rule_insurer.target_stakeholder,
                            district=district,
                            crop=crop,
                            season=season,
                            defaults={
                                'priority': PriorityLevel.HIGH,
                                'title': title,
                                'problem_statement': problem,
                                'evidence_json': evidence,
                                'recommendation_text': rec_text,
                                'status': RecommendationStatus.GENERATED,
                            }
                        )
                        if created:
                            generated_count += 1
                        rule_count += 1

            # ------------------------------------------------------------------
            # 4. Agribusiness Rule: Supply Deficit & Procurement Notice
            # ------------------------------------------------------------------
            rule_agribus = active_rules.get('AGRIBUS_SUPPLY_DEFICIT')
            if rule_agribus:
                loss_thresh = rule_agribus.parameters.get('loss_rate_threshold_pct', 12.0)
                rule_count = 0

                for dist_row in rankings:
                    if rule_count >= limit_per_rule:
                        break
                    loss_rate = dist_row.get('loss_rate', 0.0)
                    if loss_rate >= loss_thresh:
                        district = District.objects.filter(id=dist_row['district_id']).first()
                        if not district:
                            continue

                        title = f"Commodity Supply Deficit Notice: {district.name} {crop.name}"
                        problem = (
                            f"High harvest loss in {district.name} ({loss_rate:.1f}%) reduces marketable surplus of {crop.name}. "
                            f"Food processors and grain mills sourcing from this district face potential supply deficits."
                        )
                        rec_text = (
                            f"Agribusiness aggregators and processing plants should partner with local cooperatives in {district.name} "
                            f"to deploy post-harvest handling equipment (hermetic storage, mobile dryers). "
                            f"Establish contingency procurement channels in higher-yielding districts such as {top_district['district_name']}."
                        )
                        evidence = {
                            'rule_code': rule_agribus.code,
                            'crop': crop.name,
                            'district_name': district.name,
                            'loss_rate_percentage': loss_rate,
                            'plots_sampled': dist_row['plots_sampled'],
                        }

                        obj, created = Recommendation.objects.get_or_create(
                            rule=rule_agribus,
                            target_stakeholder=rule_agribus.target_stakeholder,
                            district=district,
                            crop=crop,
                            season=season,
                            defaults={
                                'priority': PriorityLevel.MEDIUM,
                                'title': title,
                                'problem_statement': problem,
                                'evidence_json': evidence,
                                'recommendation_text': rec_text,
                                'status': RecommendationStatus.GENERATED,
                            }
                        )
                        if created:
                            generated_count += 1
                        rule_count += 1

        return generated_count
