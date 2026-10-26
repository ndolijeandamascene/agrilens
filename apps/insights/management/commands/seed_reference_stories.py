"""
AgriLens Reference Agricultural Insights Seed Command.
Aligns database data stories with the approved visual design specification.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.agriculture.models import Crop, AgriculturalSeason
from apps.geography.models import District, Province
from apps.insights.models import AgriculturalInsight


class Command(BaseCommand):
    help = "Seeds the exact reference data stories from the approved AgriLens visual design."

    def handle(self, *args, **options):
        s25a = AgriculturalSeason.objects.filter(year=2025, season='A').first()
        s24a = AgriculturalSeason.objects.filter(year=2024, season='A').first()
        if not s25a or not s24a:
            self.stdout.write(self.style.ERROR("Seasons 2024A and 2025A required."))
            return

        maize = Crop.objects.filter(name__iexact='maize').first()
        beans = Crop.objects.filter(name__iexact='bush beans').first()
        rice = Crop.objects.filter(name__icontains='rice').first()
        cassava = Crop.objects.filter(name__iexact='cassava').first()

        muhanga = District.objects.filter(name__iexact='muhanga').first()
        nyabihu = District.objects.filter(name__iexact='nyabihu').first()
        bugesera = District.objects.filter(name__iexact='bugesera').first()
        rubavu = District.objects.filter(name__iexact='rubavu').first()
        gicumbi = District.objects.filter(name__iexact='gicumbi').first()
        karongi = District.objects.filter(name__iexact='karongi').first()
        south_prov = Province.objects.filter(name__icontains='south').first()

        # Unset featured on all others
        AgriculturalInsight.objects.update(is_featured=False)

        # 0. Featured Insight: Maize in Muhanga
        AgriculturalInsight.objects.update_or_create(
            fingerprint="ref-featured-maize-muhanga-2025a",
            defaults={
                'title': "Maize yield increased by 12.4% in Muhanga District between 2024A and 2025A",
                'headline': "The average maize yield in Muhanga District increased from 3.2 t/ha in 2024A to 3.6 t/ha in 2025A, representing a 12.4% improvement, based on validated agricultural observations.",
                'summary': "The average maize yield in Muhanga District increased from 3.2 t/ha in 2024A to 3.6 t/ha in 2025A, representing a 12.4% improvement, based on validated agricultural observations across surveyed farming plots in Southern Province.",
                'category': AgriculturalInsight.Category.PRODUCTIVITY_CHANGE,
                'crop': maize,
                'district': muhanga,
                'province': muhanga.province if muhanga else None,
                'current_season': s25a,
                'comparison_season': s24a,
                'indicator_name': "Maize Yield",
                'indicator_unit': "t/ha",
                'current_value': Decimal('3.60'),
                'previous_value': Decimal('3.20'),
                'absolute_change': Decimal('0.40'),
                'percentage_change': Decimal('12.40'),
                'direction': AgriculturalInsight.Direction.INCREASE,
                'source': "Official data",
                'data_quality_status': AgriculturalInsight.DataQualityStatus.SUFFICIENT_DATA,
                'data_quality_notes': "Sufficient sample size (n=18 plots). Calculated using official NISR survey weights.",
                'sample_size_current': 18,
                'sample_size_comparison': 16,
                'investigation_next_steps': "1. Verify whether improved seed and fertilizer adoption rates in Muhanga explain the yield gain.\n2. Cross-reference with rainfall station data in Southern Province.",
                'is_featured': True,
                'status': AgriculturalInsight.Status.PUBLISHED,
                'published_at': timezone.now(),
            }
        )

        base_ts = timezone.now() + timezone.timedelta(days=1)

        # Card 1: Bean in Nyabihu (Production)
        AgriculturalInsight.objects.update_or_create(
            fingerprint="ref-card1-beans-nyabihu-2025a",
            defaults={
                'title': "Bean production declined by 8.2% in Nyabihu District",
                'headline': "Total bean production decreased from 4,850 t in 2024A to 4,450 t in 2025A, an 8.2% reduction, mainly due to lower harvested area.",
                'summary': "Total bean production decreased from 4,850 t in 2024A to 4,450 t in 2025A, an 8.2% reduction, mainly due to lower harvested area in Nyabihu District.",
                'category': AgriculturalInsight.Category.PRODUCTION_CHANGE,
                'crop': beans,
                'district': nyabihu,
                'province': nyabihu.province if nyabihu else None,
                'current_season': s25a,
                'comparison_season': s24a,
                'indicator_name': "Total Production",
                'indicator_unit': "t",
                'current_value': Decimal('4450.00'),
                'previous_value': Decimal('4850.00'),
                'absolute_change': Decimal('-400.00'),
                'percentage_change': Decimal('-8.20'),
                'direction': AgriculturalInsight.Direction.DECREASE,
                'source': "NISR Seasonal Agricultural Survey (SAS)",
                'data_quality_status': AgriculturalInsight.DataQualityStatus.SUFFICIENT_DATA,
                'data_quality_notes': "Survey-weighted production estimate based on verified SAS sample plots in Western Province.",
                'sample_size_current': 22,
                'sample_size_comparison': 24,
                'investigation_next_steps': "Inspect whether land was substituted for alternative crops or if rainfall onset delayed planting.",
                'status': AgriculturalInsight.Status.PUBLISHED,
                'published_at': base_ts - timezone.timedelta(minutes=10),
            }
        )

        # Card 2: Rice in Bugesera (Cultivated Area)
        AgriculturalInsight.objects.update_or_create(
            fingerprint="ref-card2-rice-bugesera-2025a",
            defaults={
                'title': "Rice cultivated area increased by 15% in Bugesera District",
                'headline': "The cultivated area for rice expanded from 1,200 ha in 2024A to 1,380 ha in 2025A, representing a 15% increase.",
                'summary': "The cultivated area for rice expanded from 1,200 ha in 2024A to 1,380 ha in 2025A, representing a 15% increase across Bugesera marshlands.",
                'category': AgriculturalInsight.Category.CULTIVATED_AREA_CHANGE,
                'crop': rice,
                'district': bugesera,
                'province': bugesera.province if bugesera else None,
                'current_season': s25a,
                'comparison_season': s24a,
                'indicator_name': "Cultivated Area",
                'indicator_unit': "ha",
                'current_value': Decimal('1380.00'),
                'previous_value': Decimal('1200.00'),
                'absolute_change': Decimal('180.00'),
                'percentage_change': Decimal('15.00'),
                'direction': AgriculturalInsight.Direction.INCREASE,
                'source': "NISR Seasonal Agricultural Survey (SAS)",
                'data_quality_status': AgriculturalInsight.DataQualityStatus.SUFFICIENT_DATA,
                'data_quality_notes': "Aggregated from verified marshland perimeter boundaries.",
                'sample_size_current': 20,
                'sample_size_comparison': 18,
                'investigation_next_steps': "Review marshland irrigation expansion projects in Eastern Province.",
                'status': AgriculturalInsight.Status.PUBLISHED,
                'published_at': base_ts - timezone.timedelta(minutes=20),
            }
        )

        # Card 3: Rubavu District Performance (Maize)
        AgriculturalInsight.objects.update_or_create(
            fingerprint="ref-card3-rubavu-maize-benchmark-2025a",
            defaults={
                'title': "Rubavu District outperforms national maize yield by 28%",
                'headline': "Maize yield in Rubavu District (4.2 t/ha) is 28% higher than the national average (3.3 t/ha) in 2025A.",
                'summary': "Maize yield in Rubavu District (4.2 t/ha) is 28% higher than the national average (3.3 t/ha) in 2025A.",
                'category': AgriculturalInsight.Category.DISTRICT_PERFORMANCE,
                'crop': maize,
                'district': rubavu,
                'province': rubavu.province if rubavu else None,
                'current_season': s25a,
                'comparison_season': None,
                'indicator_name': "Yield Benchmark vs National Average",
                'indicator_unit': "t/ha",
                'current_value': Decimal('4.20'),
                'previous_value': Decimal('3.30'),
                'absolute_change': Decimal('0.90'),
                'percentage_change': Decimal('28.00'),
                'direction': AgriculturalInsight.Direction.BENCHMARK_LEADER,
                'source': "NISR Seasonal Agricultural Survey (SAS)",
                'data_quality_status': AgriculturalInsight.DataQualityStatus.SUFFICIENT_DATA,
                'data_quality_notes': "Benchmark comparison against national weighted average baseline of 3.3 t/ha.",
                'sample_size_current': 25,
                'sample_size_comparison': 500,
                'investigation_next_steps': "Examine volcanic soil fertility and cooperative farming models in Rubavu.",
                'status': AgriculturalInsight.Status.PUBLISHED,
                'published_at': base_ts - timezone.timedelta(minutes=30),
            }
        )

        # Card 4: Cassava in Southern Province (Crop Performance)
        AgriculturalInsight.objects.update_or_create(
            fingerprint="ref-card4-cassava-southern-2025a",
            defaults={
                'title': "Cassava production increased by 18.7% in Southern Province",
                'headline': "Total cassava production rose from 96,000 t in 2024A to 113,900 t in 2025A, an 18.7% increase driven by higher yields.",
                'summary': "Total cassava production rose from 96,000 t in 2024A to 113,900 t in 2025A, an 18.7% increase driven by higher yields in Southern Province.",
                'category': AgriculturalInsight.Category.CROP_PERFORMANCE,
                'crop': cassava,
                'district': None,
                'province': south_prov,
                'current_season': s25a,
                'comparison_season': s24a,
                'indicator_name': "Cassava Production",
                'indicator_unit': "t",
                'current_value': Decimal('113900.00'),
                'previous_value': Decimal('96000.00'),
                'absolute_change': Decimal('17900.00'),
                'percentage_change': Decimal('18.70'),
                'direction': AgriculturalInsight.Direction.INCREASE,
                'source': "NISR Seasonal Agricultural Survey (SAS)",
                'data_quality_status': AgriculturalInsight.DataQualityStatus.SUFFICIENT_DATA,
                'data_quality_notes': "Aggregated across all 8 districts of Southern Province.",
                'sample_size_current': 64,
                'sample_size_comparison': 60,
                'investigation_next_steps': "Check disease-tolerant cassava cuttings distribution records in Ruhango and Nyanza.",
                'status': AgriculturalInsight.Status.PUBLISHED,
                'published_at': base_ts - timezone.timedelta(minutes=40),
            }
        )

        # Card 5: Data Quality in Gicumbi
        AgriculturalInsight.objects.update_or_create(
            fingerprint="ref-card5-data-quality-gicumbi-2025a",
            defaults={
                'title': "Missing observations detected in Gicumbi District",
                'headline': "12% of expected observations for the 2025A season are missing for rice in Gicumbi District. This may affect reliability of trend analysis.",
                'summary': "12% of expected observations for the 2025A season are missing for rice in Gicumbi District. This may affect reliability of trend analysis.",
                'category': AgriculturalInsight.Category.DATA_QUALITY,
                'crop': rice,
                'district': gicumbi,
                'province': gicumbi.province if gicumbi else None,
                'current_season': s25a,
                'comparison_season': None,
                'indicator_name': "Data Quality Status",
                'indicator_unit': "% missing",
                'current_value': Decimal('12.00'),
                'previous_value': Decimal('0.00'),
                'absolute_change': Decimal('12.00'),
                'percentage_change': Decimal('12.00'),
                'direction': AgriculturalInsight.Direction.ANOMALY,
                'source': "AgriLens Quality Audit Engine",
                'data_quality_status': AgriculturalInsight.DataQualityStatus.LIMITED_DATA,
                'data_quality_notes': "Sample size below completeness threshold. Findings should be interpreted as indicative.",
                'sample_size_current': 4,
                'sample_size_comparison': 15,
                'investigation_next_steps': "Follow up with NISR Northern Province field coordinator for segment non-response reports.",
                'status': AgriculturalInsight.Status.PUBLISHED,
                'published_at': base_ts - timezone.timedelta(minutes=50),
            }
        )

        # Card 6: Cross-Indicator in Karongi
        AgriculturalInsight.objects.update_or_create(
            fingerprint="ref-card6-cross-karongi-2025a",
            defaults={
                'title': "Production increased while area remained stable in Karongi",
                'headline': "Maize production increased by 14.3% in 2025A while cultivated area remained nearly unchanged (+1.2%), indicating improved yields.",
                'summary': "Maize production increased by 14.3% in 2025A while cultivated area remained nearly unchanged (+1.2%), indicating improved yields.",
                'category': AgriculturalInsight.Category.CROSS_INDICATOR,
                'crop': maize,
                'district': karongi,
                'province': karongi.province if karongi else None,
                'current_season': s25a,
                'comparison_season': s24a,
                'indicator_name': "Production vs Area Dynamic",
                'indicator_unit': "Multi-metric",
                'current_value': Decimal('3200.00'),
                'previous_value': Decimal('2800.00'),
                'absolute_change': Decimal('400.00'),
                'percentage_change': Decimal('14.30'),
                'direction': AgriculturalInsight.Direction.DIVERGENCE,
                'source': "NISR Seasonal Agricultural Survey (SAS)",
                'data_quality_status': AgriculturalInsight.DataQualityStatus.SUFFICIENT_DATA,
                'data_quality_notes': "Decoupling confirmed: production grew 14.3% with area expanding only 1.2%.",
                'sample_size_current': 19,
                'sample_size_comparison': 18,
                'investigation_next_steps': "Assess whether terracing and anti-erosion measures on slopes boosted soil nutrient retention.",
                'status': AgriculturalInsight.Status.PUBLISHED,
                'published_at': base_ts - timezone.timedelta(minutes=60),
            }
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded reference design data stories!"))
