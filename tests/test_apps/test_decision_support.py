"""
Comprehensive Automated Test Suite for AgriLens Decision Support & Impact Tracking.
Validates multi-stakeholder rule engine, action plan lifecycles, outcome measurements,
role-based geographic scoping, security audit logging, and formula-injection-safe exports.
"""
from decimal import Decimal
from datetime import date
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.geography.models import Province, District
from apps.agriculture.models import AgriculturalSeason, Crop, CropCategory
from apps.data_management.models import DataSource, ImportBatch, ValidatedObservation
from apps.accounts.models import AuditLog
from apps.decision_support.models import (
    RecommendationRule,
    Recommendation,
    ActionPlan,
    OutcomeMeasurement,
    StakeholderType,
    PriorityLevel,
    RecommendationStatus,
    ActionStatus,
)
from apps.decision_support.engine import DecisionEngine

User = get_user_model()


class DecisionSupportTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # Geography
        self.prov_north = Province.objects.create(name='Northern Province', code='01')
        self.dist_musanze = District.objects.create(name='Musanze', code='0101', province=self.prov_north)
        self.dist_burera = District.objects.create(name='Burera', code='0102', province=self.prov_north)

        self.prov_south = Province.objects.create(name='Southern Province', code='02')
        self.dist_huye = District.objects.create(name='Huye', code='0201', province=self.prov_south)

        # Seasons
        self.season2024a = AgriculturalSeason.objects.create(
            year=2024, season='A',
            start_date=date(2023, 9, 1), end_date=date(2024, 2, 28)
        )
        self.season2025a = AgriculturalSeason.objects.create(
            year=2025, season='A',
            start_date=date(2024, 9, 1), end_date=date(2025, 2, 28)
        )

        # Crops
        cat = CropCategory.objects.create(name='Cereals')
        self.crop_maize = Crop.objects.create(name='Maize', category=cat, is_priority_crop=True)

        # Users
        self.admin = User.objects.create_superuser(
            username='admin_ds', email='admin@agrilens.rw', password='AdminPass123!'
        )
        self.national_officer = User.objects.create_user(
            username='nat_officer', email='minagri@agrilens.rw', password='OfficerPass123!',
            role=User.Role.NATIONAL_OFFICER
        )
        self.musanze_officer = User.objects.create_user(
            username='musanze_officer', email='musanze@agrilens.rw', password='OfficerPass123!',
            role=User.Role.DISTRICT_OFFICER
        )
        self.musanze_officer.assigned_districts.add(self.dist_musanze)

        self.huye_officer = User.objects.create_user(
            username='huye_officer', email='huye@agrilens.rw', password='OfficerPass123!',
            role=User.Role.DISTRICT_OFFICER
        )
        self.huye_officer.assigned_districts.add(self.dist_huye)

        # Seed Observations
        self.ds = DataSource.objects.create(name='SAS 2025', source_type='NISR_SAS_2025', is_official_survey=True)
        self.batch = ImportBatch.objects.create(source=self.ds, filename='sas25.sav')

        # Musanze Maize: high yield
        ValidatedObservation.objects.create(
            batch=self.batch, provenance='NISR_SAS_2025', season=self.season2025a,
            district=self.dist_musanze, crop=self.crop_maize, source_record_id='REC_M1',
            plot_area_ha=Decimal('1.0'), total_production_kg=Decimal('3500.0'),
            calculated_yield_kg_per_ha=Decimal('3500.0'), sampling_weight=Decimal('1.0'),
            is_improved_seed=True, uses_inorganic_fertilizer=True
        )
        ValidatedObservation.objects.create(
            batch=self.batch, provenance='NISR_SAS_2025', season=self.season2025a,
            district=self.dist_musanze, crop=self.crop_maize, source_record_id='REC_M2',
            plot_area_ha=Decimal('1.0'), total_production_kg=Decimal('3500.0'),
            calculated_yield_kg_per_ha=Decimal('3500.0'), sampling_weight=Decimal('1.0'),
            is_improved_seed=True, uses_inorganic_fertilizer=True
        )
        ValidatedObservation.objects.create(
            batch=self.batch, provenance='NISR_SAS_2025', season=self.season2025a,
            district=self.dist_musanze, crop=self.crop_maize, source_record_id='REC_M3',
            plot_area_ha=Decimal('1.0'), total_production_kg=Decimal('3500.0'),
            calculated_yield_kg_per_ha=Decimal('3500.0'), sampling_weight=Decimal('1.0'),
            is_improved_seed=True, uses_inorganic_fertilizer=True
        )

        # Burera Maize: lower yield (gap > 40%)
        for i in range(4):
            ValidatedObservation.objects.create(
                batch=self.batch, provenance='NISR_SAS_2025', season=self.season2025a,
                district=self.dist_burera, crop=self.crop_maize, source_record_id=f'REC_B{i}',
                plot_area_ha=Decimal('1.0'), total_production_kg=Decimal('1400.0'),
                calculated_yield_kg_per_ha=Decimal('1400.0'), sampling_weight=Decimal('1.0'),
                is_improved_seed=False, uses_inorganic_fertilizer=False,
                total_loss_kg=Decimal('350.0') # 20% loss rate for bank/agribusiness flags
            )

    def test_ensure_default_rules(self):
        """Validates bootstrapping of all default stakeholder rules."""
        rules = DecisionEngine.ensure_default_rules()
        self.assertGreaterEqual(len(rules), 4)

        codes = [r.code for r in rules]
        self.assertIn('MINAGRI_INPUT_GAP_ALERT', codes)
        self.assertIn('BANK_PORTFOLIO_EXPOSURE', codes)
        self.assertIn('INSURER_HARVEST_RISK', codes)
        self.assertIn('AGRIBUS_SUPPLY_DEFICIT', codes)

    def test_decision_engine_generation_and_idempotency(self):
        """Validates that engine generates recommendations deterministically and idempotently."""
        count = DecisionEngine.generate_recommendations(year=2025, season_code='A', source_policy='official')
        self.assertGreater(count, 0)

        # Re-running must generate 0 duplicates
        count_repeat = DecisionEngine.generate_recommendations(year=2025, season_code='A', source_policy='official')
        self.assertEqual(count_repeat, 0)

        # Verify MINAGRI gap recommendation was created for Burera
        burera_rec = Recommendation.objects.filter(
            district=self.dist_burera, crop=self.crop_maize, rule__code='MINAGRI_INPUT_GAP_ALERT'
        ).first()
        self.assertIsNotNone(burera_rec)
        self.assertEqual(burera_rec.target_stakeholder, StakeholderType.GOVERNMENT)
        self.assertIn('Burera', burera_rec.title)
        self.assertIn('yield deficit', burera_rec.problem_statement)
        self.assertIn('gap_percentage', burera_rec.evidence_json)
        self.assertTrue(hasattr(burera_rec, 'recommended_action'))

    def test_decision_hub_view(self):
        """Tests decision hub dashboard rendering and KPI metrics."""
        DecisionEngine.generate_recommendations(year=2025, season_code='A')
        self.client.force_login(self.admin)

        resp = self.client.get(reverse('decision_support:hub'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('total_recommendations', resp.context)
        self.assertGreater(resp.context['total_recommendations'], 0)
        self.assertIn('gov_count', resp.context)
        self.assertContains(resp, 'Decision Support')
        self.assertContains(resp, 'MINAGRI')

    def test_recommendation_list_filters(self):
        """Tests filtering recommendations by stakeholder and priority."""
        DecisionEngine.generate_recommendations(year=2025, season_code='A')
        self.client.force_login(self.national_officer)

        # Filter by GOVERNMENT
        resp = self.client.get(reverse('decision_support:recommendation_list') + '?stakeholder=GOVERNMENT')
        self.assertEqual(resp.status_code, 200)
        recs = resp.context['recommendations']
        for r in recs:
            self.assertEqual(r.target_stakeholder, StakeholderType.GOVERNMENT)

        # Filter by BANK
        resp_bank = self.client.get(reverse('decision_support:recommendation_list') + '?stakeholder=BANK')
        self.assertEqual(resp_bank.status_code, 200)
        for r in resp_bank.context['recommendations']:
            self.assertEqual(r.target_stakeholder, StakeholderType.BANK)

    def test_recommendation_detail_and_geographic_scoping(self):
        """District Officers can only view recommendations within their assigned districts."""
        DecisionEngine.generate_recommendations(year=2025, season_code='A')

        burera_rec = Recommendation.objects.filter(district=self.dist_burera).first()
        self.assertIsNotNone(burera_rec)

        # 1. Musanze officer attempts to view Burera recommendation -> 403 Forbidden
        self.client.force_login(self.musanze_officer)
        resp_forbidden = self.client.get(reverse('decision_support:recommendation_detail', kwargs={'pk': burera_rec.id}))
        self.assertEqual(resp_forbidden.status_code, 403)

        # 2. National Officer has nationwide clearance -> 200 OK
        self.client.force_login(self.national_officer)
        resp_ok = self.client.get(reverse('decision_support:recommendation_detail', kwargs={'pk': burera_rec.id}))
        self.assertEqual(resp_ok.status_code, 200)
        self.assertContains(resp_ok, burera_rec.title)
        self.assertContains(resp_ok, "Structured Statistical Evidence")

    def test_recommendation_status_transition_with_audit_trail(self):
        """Tests transitioning recommendation status and verifying tamper-evident audit logging."""
        DecisionEngine.generate_recommendations(year=2025, season_code='A')
        rec = Recommendation.objects.first()

        self.client.force_login(self.national_officer)
        transition_url = reverse('decision_support:recommendation_transition', kwargs={'pk': rec.id})

        post_data = {
            'status': RecommendationStatus.APPROVED,
            'review_notes': 'Endorsed for immediate Track 1 agricultural action.',
        }
        resp = self.client.post(transition_url, post_data)
        self.assertEqual(resp.status_code, 302)

        rec.refresh_from_db()
        self.assertEqual(rec.status, RecommendationStatus.APPROVED)
        self.assertEqual(rec.reviewer, self.national_officer)
        self.assertIn('Endorsed for immediate', rec.review_notes)

        # Verify AuditLog
        log = AuditLog.objects.filter(action=AuditLog.Action.RECOMMENDATION_TRANSITION, target_id=str(rec.id)).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.actor, self.national_officer)
        self.assertIn('"new_status": "APPROVED"', log.details)

    def test_action_plan_creation_and_lifecycle(self):
        """Tests attaching operational ActionPlan to an approved recommendation and updating its status."""
        DecisionEngine.generate_recommendations(year=2025, season_code='A')
        rec = Recommendation.objects.filter(district=self.dist_burera).first()
        rec.status = RecommendationStatus.APPROVED
        rec.save()

        self.client.force_login(self.admin)
        create_url = reverse('decision_support:action_plan_create', kwargs={'pk': rec.id})

        plan_data = {
            'title': 'Burera Soil Amendment Program',
            'assigned_organization': 'Rwanda Agriculture Board (RAB)',
            'target_date': '2026-06-30',
            'action_details': 'Distribute agricultural lime and blended fertilizers to 500 smallholder farmers.',
        }
        resp = self.client.post(create_url, plan_data)
        self.assertEqual(resp.status_code, 302)

        # Verify ActionPlan created
        plan = ActionPlan.objects.filter(recommendation=rec).first()
        self.assertIsNotNone(plan)
        self.assertEqual(plan.title, 'Burera Soil Amendment Program')
        self.assertEqual(plan.status, ActionStatus.PLANNED)

        # Recommendation should auto-transition to ASSIGNED
        rec.refresh_from_db()
        self.assertEqual(rec.status, RecommendationStatus.ASSIGNED)

        # Test ActionPlan Update
        update_url = reverse('decision_support:action_plan_update', kwargs={'pk': plan.id})
        resp_update = self.client.post(update_url, {'status': ActionStatus.ONGOING})
        self.assertEqual(resp_update.status_code, 302)

        plan.refresh_from_db()
        self.assertEqual(plan.status, ActionStatus.ONGOING)

    def test_impact_dashboard_and_outcome_measurements(self):
        """Tests Track 1 implementation & impact monitoring dashboard with outcome metrics."""
        rec = Recommendation.objects.create(
            rule=RecommendationRule.objects.create(
                code='RULE_TEST', title='Test Rule', target_stakeholder=StakeholderType.GOVERNMENT
            ),
            target_stakeholder=StakeholderType.GOVERNMENT,
            district=self.dist_burera,
            crop=self.crop_maize,
            season=self.season2025a,
            priority=PriorityLevel.HIGH,
            title='Burera Maize Gap Action',
            problem_statement='Gap observed',
            recommendation_text='Extend subsidies',
        )
        plan = ActionPlan.objects.create(
            recommendation=rec,
            title='Burera Fertilizer Rollout',
            assigned_to=self.admin,
            assigned_organization='RAB',
            status=ActionStatus.COMPLETED
        )
        OutcomeMeasurement.objects.create(
            action_plan=plan,
            district=self.dist_burera,
            crop=self.crop_maize,
            baseline_season=self.season2024a,
            evaluation_season=self.season2025a,
            baseline_yield_kg_per_ha=Decimal('1200.0'),
            evaluation_yield_kg_per_ha=Decimal('1560.0'),
            observed_yield_change_pct=Decimal('30.0'),
            notes='Observational survey evaluation.'
        )

        self.client.force_login(self.admin)
        resp = self.client.get(reverse('decision_support:impact_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Track 1')
        self.assertContains(resp, 'Burera Fertilizer Rollout')
        self.assertContains(resp, '+30.0%') # (1560 - 1200)/1200 * 100 = +30.0%
        self.assertContains(resp, 'Positive Trajectory')
        self.assertContains(resp, 'Methodological Disclosure')

    def test_recommendation_export_csv_and_formula_safety(self):
        """Validates CSV export formatting, geographic scoping, and CWE-1236 formula sanitization."""
        # Create recommendation with formula-like title to verify CWE-1236 mitigation
        rec = Recommendation.objects.create(
            target_stakeholder=StakeholderType.GOVERNMENT,
            district=self.dist_musanze,
            crop=self.crop_maize,
            season=self.season2025a,
            priority=PriorityLevel.HIGH,
            title='=CMD|"/C calc"!A0 Dangerous Formula Title',
            problem_statement='Formula injection test.',
            recommendation_text='Safe advisory.',
        )

        self.client.force_login(self.admin)
        resp = self.client.get(reverse('decision_support:recommendation_export_csv'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/csv; charset=utf-8')

        content = resp.content.decode('utf-8')
        self.assertIn("AGRILENS RWANDA • EVIDENCE-BASED RECOMMENDATIONS DOSSIER", content)
        # Verify formula was sanitized by prefixing with single quote
        self.assertIn("'=CMD", content)

    def test_recommendation_export_excel(self):
        """Validates openpyxl Excel spreadsheet generation and binary response headers."""
        DecisionEngine.generate_recommendations(year=2025, season_code='A')
        self.client.force_login(self.admin)

        resp = self.client.get(reverse('decision_support:recommendation_export_excel'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('.xlsx', resp['Content-Disposition'])
        self.assertGreater(len(resp.content), 2000)
