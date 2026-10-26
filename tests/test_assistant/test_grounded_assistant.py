import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from django.test import Client

from apps.geography.models import Province, District
from apps.agriculture.models import Crop, CropCategory, AgriculturalSeason
from apps.data_management.models import DataSource, ImportBatch, ValidatedObservation
from apps.assistant.services.parser import GroundedAgriculturalAssistant
from apps.assistant.models import AssistantQueryLog


@pytest.fixture(autouse=True)
def seed_assistant_test_data(db):
    """Seeds test observations for Grounded Assistant test suite."""
    prov = Province.objects.create(name='Northern Province', code='NP')
    prov_east = Province.objects.create(name='Eastern Province', code='EP')
    prov_west = Province.objects.create(name='Western Province', code='WP')

    dist_musanze = District.objects.create(name='Musanze', code='11', province=prov)
    dist_nyagatare = District.objects.create(name='Nyagatare', code='21', province=prov_east)
    dist_karongi = District.objects.create(name='Karongi', code='31', province=prov_west)

    cat = CropCategory.objects.create(name='Staples')
    crop_potato = Crop.objects.create(name='Irish Potato', category=cat, is_priority_crop=True)
    crop_maize = Crop.objects.create(name='Maize', category=cat, is_priority_crop=True)
    crop_beans = Crop.objects.create(name='Beans', category=cat, is_priority_crop=True)

    season_2025a = AgriculturalSeason.objects.create(
        year=2025, season='A', start_date='2024-09-01', end_date='2025-02-28'
    )

    ds = DataSource.objects.create(
        name="NISR SAS 2025",
        source_type="NISR_SAS_2025",
        data_kind=DataSource.DataKind.SURVEY,
        year=2025,
        season="A",
        organization="NISR"
    )
    batch = ImportBatch.objects.create(
        source=ds,
        filename="sas_2025a.csv",
        total_rows=10,
        rows_accepted=10
    )

    # 1. Musanze Irish Potato observations
    for i in range(5):
        ValidatedObservation.objects.create(
            batch=batch,
            provenance="NISR_SAS_2025A",
            season=season_2025a,
            district=dist_musanze,
            crop=crop_potato,
            source_record_id=f"musanze_potato_{i}",
            plot_area_ha=Decimal("1.2"),
            total_production_kg=Decimal("11400.0"),
            calculated_yield_kg_per_ha=Decimal("9500.0"),
            is_improved_seed=True,
            uses_inorganic_fertilizer=True,
            loss_rate_percentage=Decimal("8.5"),
            sampling_weight=Decimal("1.0")
        )

    # 2. Nyagatare Maize observations
    for i in range(5):
        ValidatedObservation.objects.create(
            batch=batch,
            provenance="NISR_SAS_2025A",
            season=season_2025a,
            district=dist_nyagatare,
            crop=crop_maize,
            source_record_id=f"nyagatare_maize_{i}",
            plot_area_ha=Decimal("2.0"),
            total_production_kg=Decimal("7000.0"),
            calculated_yield_kg_per_ha=Decimal("3500.0"),
            is_improved_seed=True,
            uses_inorganic_fertilizer=True,
            is_irrigated=(i % 2 == 0),
            loss_rate_percentage=Decimal("6.0"),
            sampling_weight=Decimal("1.0")
        )

    # 3. Beans observations
    for i in range(5):
        ValidatedObservation.objects.create(
            batch=batch,
            provenance="NISR_SAS_2025A",
            season=season_2025a,
            district=dist_nyagatare,
            crop=crop_beans,
            source_record_id=f"beans_{i}",
            plot_area_ha=Decimal("1.0"),
            total_production_kg=Decimal("1800.0"),
            calculated_yield_kg_per_ha=Decimal("1800.0"),
            loss_rate_percentage=Decimal("7.0"),
            sampling_weight=Decimal("1.0")
        )


@pytest.mark.django_db
def test_assistant_yield_query_musanze_potato():
    """Verifies that an Irish Potato yield query produces grounded calculations."""
    res = GroundedAgriculturalAssistant.answer_query("What is the average Irish Potato yield in Musanze?")
    assert res['status'] == 'SUCCESS'
    assert res['intent'] == 'YIELD'
    assert 'Musanze' in res['answer']
    assert 'Irish Potato' in res['answer']
    assert 't/ha' in res['answer']
    assert res['sample_count'] == 5
    assert 'ValidatedObservation' in res['orm_query']
    assert 'indicators' in res['dashboard_link']


@pytest.mark.django_db
def test_assistant_ranking_query_beans():
    """Verifies that ranking queries identify top producer supply sheds."""
    res = GroundedAgriculturalAssistant.answer_query("Which district produces the most beans?")
    assert res['status'] == 'SUCCESS'
    assert res['intent'] == 'RANKING'
    assert 'Top 5' in res['answer']
    assert 'Beans' in res['answer']
    assert 'MT' in res['answer']
    assert 'ValidatedObservation' in res['orm_query']


@pytest.mark.django_db
def test_assistant_input_adoption_query():
    """Verifies that input adoption queries calculate practice proportions."""
    res = GroundedAgriculturalAssistant.answer_query("What percentage of farmers in Nyagatare use fertilizer?")
    assert res['status'] == 'SUCCESS'
    assert res['intent'] == 'INPUT_ADOPTION'
    assert 'Fertilizer' in res['answer']
    assert 'Nyagatare' in res['answer']
    assert '%' in res['answer']


@pytest.mark.django_db
def test_assistant_vulnerability_query():
    """Verifies that vulnerability queries invoke the AVI engine."""
    res = GroundedAgriculturalAssistant.answer_query("What is the vulnerability index for Karongi?")
    assert res['status'] == 'SUCCESS'
    assert res['intent'] == 'VULNERABILITY'
    assert 'Karongi' in res['answer']
    assert 'AVI' in res['answer'] or 'Vulnerability' in res['answer']
    assert 'decision-support' in res['dashboard_link']


@pytest.mark.django_db
def test_assistant_general_guidance():
    """Verifies that ambiguous queries return guidance rather than hallucinations."""
    res = GroundedAgriculturalAssistant.answer_query("Hello, what can you do?")
    assert res['status'] == 'GENERAL_GUIDANCE'
    assert 'AgriLens Grounded Agricultural Data Assistant' in res['answer']
    assert res['sample_count'] == 0


@pytest.mark.django_db
def test_assistant_audit_logging():
    """Verifies that every query is recorded in AssistantQueryLog for Track 1 compliance."""
    initial_cnt = AssistantQueryLog.objects.count()
    GroundedAgriculturalAssistant.answer_query("Average beans yield in Rwanda?")
    assert AssistantQueryLog.objects.count() == initial_cnt + 1

    latest_log = AssistantQueryLog.objects.first()
    assert latest_log.query_text == "Average beans yield in Rwanda?"
    assert latest_log.intent == 'YIELD'
    assert latest_log.execution_time_ms > 0


@pytest.mark.django_db
def test_assistant_api_endpoint():
    """Verifies POST /api/v1/assistant/query/ REST contract."""
    client = APIClient()

    # Valid query
    resp = client.post('/api/v1/assistant/query/', {'query': 'maize production in Nyagatare'}, format='json')
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'SUCCESS'
    assert 'answer' in data
    assert 'orm_query' in data
    assert 'provenance' in data

    # Empty query rejection
    bad_resp = client.post('/api/v1/assistant/query/', {'query': ''}, format='json')
    assert bad_resp.status_code == 400


@pytest.mark.django_db
def test_assistant_web_view():
    """Verifies GET /assistant/ renders successfully."""
    client = Client()
    resp = client.get('/assistant/')
    assert resp.status_code == 200
    assert b"Grounded AI Agricultural Data Assistant" in resp.content
