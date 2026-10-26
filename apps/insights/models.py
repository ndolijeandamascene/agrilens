"""
AgriLens Agricultural Insights & Data Stories Models.
Discovers, persists, and governs evidence-based agricultural patterns in Rwanda:
- Productivity changes (yield uplifts & deficits)
- Production volume shifts (MT)
- Cultivated land area expansions & contractions (ha)
- District benchmark performance (vs national/provincial baselines)
- Multi-crop performance rankings
- Data quality anomalies & insufficient sample warnings
- Cross-indicator dynamics (intensification vs extensification)
"""
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


class InsightQuerySet(models.QuerySet):
    def published(self):
        """Only public approved & published insights."""
        return self.filter(status=AgriculturalInsight.Status.PUBLISHED)

    def review_queue(self):
        """Internal queue requiring analyst/manager verification."""
        return self.filter(status__in=[
            AgriculturalInsight.Status.GENERATED,
            AgriculturalInsight.Status.UNDER_REVIEW
        ])

    def by_category(self, category):
        return self.filter(category=category)

    def featured(self):
        return self.filter(status=AgriculturalInsight.Status.PUBLISHED, is_featured=True)


class AgriculturalInsight(models.Model):
    class Category(models.TextChoices):
        PRODUCTIVITY_CHANGE = 'productivity_change', 'Productivity Change'
        PRODUCTION_CHANGE = 'production_change', 'Production Change'
        CULTIVATED_AREA_CHANGE = 'cultivated_area_change', 'Cultivated Area Change'
        DISTRICT_PERFORMANCE = 'district_performance', 'District Benchmark Performance'
        CROP_PERFORMANCE = 'crop_performance', 'Crop Performance Trend'
        DATA_QUALITY = 'data_quality', 'Data Quality & Anomaly'
        CROSS_INDICATOR = 'cross_indicator', 'Cross-Indicator Dynamics'

    class Direction(models.TextChoices):
        INCREASE = 'increase', 'Increase'
        DECREASE = 'decrease', 'Decrease'
        STABLE = 'stable', 'Stable'
        BENCHMARK_LEADER = 'benchmark_leader', 'Benchmark Leader'
        BENCHMARK_LAGGING = 'benchmark_lagging', 'Lagging District'
        ANOMALY = 'anomaly', 'Data Quality Anomaly'
        DIVERGENCE = 'divergence', 'Indicator Divergence'

    class DataQualityStatus(models.TextChoices):
        SUFFICIENT_DATA = 'sufficient_data', 'Sufficient Data'
        LIMITED_DATA = 'limited_data', 'Limited Data'
        INSUFFICIENT_DATA = 'insufficient_data', 'Insufficient Data'
        UNDER_REVIEW = 'under_review', 'Under Review'

    class Status(models.TextChoices):
        GENERATED = 'generated', 'Generated'
        UNDER_REVIEW = 'under_review', 'Under Review'
        APPROVED = 'approved', 'Approved'
        PUBLISHED = 'published', 'Published'
        REJECTED = 'rejected', 'Rejected'
        SUPERSEDED = 'superseded', 'Superseded'

    objects = InsightQuerySet.as_manager()

    # Core narrative
    title = models.CharField(max_length=255, help_text="Concise, evidence-based data story headline")
    headline = models.CharField(max_length=255, blank=True, help_text="One-sentence executive summary")
    summary = models.TextField(help_text="Detailed narrative answering what is happening, where, and by how much")
    category = models.CharField(max_length=30, choices=Category.choices, db_index=True)

    # Geographic and crop scope
    crop = models.ForeignKey(
        'agriculture.Crop',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='insights',
        help_text="Primary crop affected (null for cross-crop findings)"
    )
    district = models.ForeignKey(
        'geography.District',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='insights',
        help_text="Target district (null for national level)"
    )
    province = models.ForeignKey(
        'geography.Province',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='insights'
    )

    # Reference periods
    current_season = models.ForeignKey(
        'agriculture.AgriculturalSeason',
        on_delete=models.PROTECT,
        related_name='current_insights',
        help_text="Observation season being analyzed"
    )
    comparison_season = models.ForeignKey(
        'agriculture.AgriculturalSeason',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comparison_insights',
        help_text="Baseline season for comparison (e.g. YoY same season)"
    )

    # Quantitative metrics
    indicator_name = models.CharField(max_length=100, default='Crop Yield')
    indicator_unit = models.CharField(max_length=30, default='kg/ha')
    current_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    previous_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    absolute_change = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    percentage_change = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    direction = models.CharField(max_length=25, choices=Direction.choices, default=Direction.STABLE)

    # Data provenance and quality
    source = models.CharField(max_length=120, default='NISR Seasonal Agricultural Survey (SAS)')
    data_quality_status = models.CharField(
        max_length=30,
        choices=DataQualityStatus.choices,
        default=DataQualityStatus.SUFFICIENT_DATA,
        db_index=True
    )
    data_quality_notes = models.TextField(blank=True, help_text="Explanation of sample size, weighting, or data limitations")
    sample_size_current = models.PositiveIntegerField(default=0, help_text="Number of plot observations in current period")
    sample_size_comparison = models.PositiveIntegerField(default=0, help_text="Number of plot observations in comparison period")

    # Actionable intelligence
    investigation_next_steps = models.TextField(
        blank=True,
        help_text="Specific questions and hypotheses for an agricultural analyst or field officer to investigate"
    )
    evidence_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured calculation payload, district rankings, chart series coordinates, and sample distributions"
    )

    # Lifecycle & Governance
    fingerprint = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="SHA-256 hash ensuring idempotency and preventing duplicate generation"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.GENERATED,
        db_index=True
    )
    is_featured = models.BooleanField(default=False, help_text="Featured on the public stories landing page")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_insights'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_insights'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comments = models.TextField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']
        indexes = [
            models.Index(fields=['status', 'category']),
            models.Index(fields=['crop', 'current_season']),
            models.Index(fields=['district', 'current_season']),
        ]

    def __str__(self):
        crop_label = f" - {self.crop.name}" if self.crop else ""
        dist_label = f" in {self.district.name}" if self.district else " (National)"
        return f"[{self.get_category_display()}] {self.title}{crop_label}{dist_label}"

    @property
    def formatted_change(self):
        """Displays formatted percentage change with explicit sign (+/-)."""
        if self.percentage_change is None:
            return "N/A"
        if self.percentage_change > 0:
            return f"+{self.percentage_change:.1f}%"
        return f"{self.percentage_change:.1f}%"

    @property
    def scope_label(self):
        if self.district:
            return f"{self.district.name} District, {self.district.province.name}"
        if self.province:
            return f"{self.province.name} Province"
        return "National (All Rwanda)"

    @property
    def period_label(self):
        if self.comparison_season:
            return f"{self.current_season} vs {self.comparison_season}"
        return f"{self.current_season}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('insights:public_detail', kwargs={'pk': self.pk})
