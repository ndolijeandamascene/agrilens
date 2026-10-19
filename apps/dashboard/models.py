import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class PublishedReport(models.Model):
    """
    Public and official published agricultural intelligence reports and bulletins.
    Published by NISR & MINAGRI, accessible to public citizens, researchers, and officers.
    """
    REPORT_TYPES = [
        ("survey", "Seasonal Agricultural Survey"),
        ("production", "Agricultural Production Report"),
        ("yield", "Crop Yield & Productivity Report"),
        ("land_use", "Land Use & Cultivated Area Report"),
        ("crop", "Crop-Specific Report"),
        ("livestock", "Livestock & Animal Production Report"),
        ("irrigation", "Irrigation & Water Management Report"),
        ("mechanization", "Agricultural Mechanization Report"),
        ("inputs", "Agricultural Inputs & Subsidies Report"),
        ("fertilizer", "Fertilizer Use Report"),
        ("seeds", "Seeds & Planting Materials Report"),
        ("soil", "Soil Health & Conservation Report"),
        ("pest_disease", "Pest & Crop Disease Report"),
        ("climate", "Climate & Weather Impact Report"),
        ("outlook", "Seasonal Agricultural Outlook"),
        ("food_security", "Food Security & Nutrition Report"),
        ("postharvest", "Post-Harvest Losses Report"),
        ("storage", "Agricultural Storage Report"),
        ("processing", "Agro-Processing & Value Addition Report"),
        ("market", "Agricultural Market Analysis"),
        ("prices", "Commodity Prices Report"),
        ("trade", "Agricultural Trade & Export Report"),
        ("supply_chain", "Agricultural Supply Chain Report"),
        ("farm_income", "Farm Income & Economic Analysis"),
        ("cost_benefit", "Agricultural Cost-Benefit Analysis"),
        ("finance", "Agricultural Finance & Credit Report"),
        ("insurance", "Agricultural Insurance & Risk Report"),
        ("district", "District Agricultural Performance Report"),
        ("province", "Provincial Agricultural Performance Report"),
        ("national", "National Agricultural Statistics Report"),
        ("research", "Agricultural Research Report"),
        ("impact", "Agricultural Impact Assessment"),
        ("policy", "Agricultural Policy Analysis"),
        ("brief", "Policy Brief"),
        ("annual", "Annual Agricultural Report"),
        ("quarterly", "Quarterly Agricultural Report"),
        ("monthly", "Monthly Agricultural Report"),
        ("data_quality", "Data Quality & Validation Report"),
        ("methodology", "Survey Methodology & Technical Report"),
        ("other", "Other Agricultural Report"),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    subtitle = models.CharField(max_length=300, blank=True)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES, default='survey')
    report_type_label = models.CharField(max_length=100, default='Seasonal Survey')
    crop = models.CharField(max_length=100, default='All Crops')
    season = models.CharField(max_length=100, default='All Seasons')
    year = models.IntegerField(default=2025)
    publication_date = models.DateField(default=timezone.now)
    date_display = models.CharField(max_length=50, blank=True)
    executive_summary = models.TextField(blank=True)
    key_metrics = models.JSONField(default=dict, blank=True)
    pdf_filename = models.CharField(max_length=255, blank=True)
    downloads_count = models.IntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-publication_date', '-id']
        verbose_name = 'Published Agricultural Report'
        verbose_name_plural = 'Published Agricultural Reports'

    def __str__(self):
        return f"{self.title} ({self.date_display or self.publication_date})"


class ReportSchedule(models.Model):
    """
    Automated reporting schedule configuration for recurring institutional reports.
    Executes in Africa/Kigali reporting timezone with concurrency locks, duplicate
    prevention, period rule computation, and automatic review submission.
    """
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly (Previous Month)'),
        ('quarterly', 'Quarterly (Previous Quarter)'),
        ('seasonal', 'Seasonal (Previous Season)'),
        ('annually', 'Annually (Previous Calendar Year)'),
    ]

    OUTPUT_FORMATS = [
        ('pdf', 'PDF Document'),
        ('xlsx', 'Excel Spreadsheet (XLSX)'),
        ('csv', 'Comma-Separated Values (CSV)'),
    ]

    title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=50, choices=PublishedReport.REPORT_TYPES, default='survey')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    output_format = models.CharField(max_length=10, choices=OUTPUT_FORMATS, default='pdf')

    # Geographic & Domain Scoping
    province = models.ForeignKey(
        'geography.Province', on_delete=models.SET_NULL, null=True, blank=True, related_name='schedules'
    )
    district = models.ForeignKey(
        'geography.District', on_delete=models.SET_NULL, null=True, blank=True, related_name='schedules'
    )
    crop = models.ForeignKey(
        'agriculture.Crop', on_delete=models.SET_NULL, null=True, blank=True, related_name='schedules'
    )
    crop_name = models.CharField(max_length=100, default='All Crops')
    indicator = models.CharField(max_length=100, default='all', blank=True)
    data_source = models.CharField(max_length=50, default='official')
    parameters = models.JSONField(default=dict, blank=True)

    # Ownership & Workflow
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='report_schedules'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_review_schedules'
    )
    auto_submit_for_review = models.BooleanField(
        default=True, help_text="Automatically transitions completed report to 'pending_review'"
    )
    is_active = models.BooleanField(default=True, help_text="Enabled or paused status")

    # Concurrency Lock & Execution Tracking
    is_running = models.BooleanField(default=False, help_text="Execution lock to prevent overlapping runs")
    running_since = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(db_index=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(max_length=30, blank=True, default='pending')
    last_error = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['next_run_at', '-id']
        verbose_name = 'Automated Report Schedule'
        verbose_name_plural = 'Automated Report Schedules'

    def __str__(self):
        return f"{self.title} ({self.get_frequency_display()} - {self.get_output_format_display()})"


class GeneratedReport(models.Model):
    """
    Internal generated agricultural report dossier.
    Tracks generation parameters, verified statistical computations, multi-format artifacts,
    lifecycle audit transitions (draft -> generated -> pending_review -> approved -> published),
    and enforces role & geographic authorization.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft / Queued'),
        ('generated', 'Generated'),
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('published', 'Published'),
        ('rejected', 'Rejected / Returned'),
        ('failed', 'Generation Failed'),
        ('cancelled', 'Cancelled'),
    ]

    OUTPUT_FORMATS = [
        ('pdf', 'PDF Document'),
        ('xlsx', 'Excel Spreadsheet (XLSX)'),
        ('csv', 'Comma-Separated Values (CSV)'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=50, choices=PublishedReport.REPORT_TYPES, default='survey')
    report_type_label = models.CharField(max_length=100, default='Seasonal Survey')
    output_format = models.CharField(max_length=10, choices=OUTPUT_FORMATS, default='pdf')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='generated', db_index=True)

    # Period & Scope
    reporting_period = models.CharField(max_length=100, blank=True)
    season = models.CharField(max_length=100, default='All Seasons')
    year = models.IntegerField(default=2025)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # Geographic Scope
    province = models.ForeignKey(
        'geography.Province', on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_reports'
    )
    district = models.ForeignKey(
        'geography.District', on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_reports'
    )
    crop = models.ForeignKey(
        'agriculture.Crop', on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_reports'
    )
    crop_name = models.CharField(max_length=100, default='All Crops')
    indicator = models.CharField(max_length=100, default='all', blank=True)
    data_source = models.CharField(max_length=50, default='official')

    # Content & Statistical Provenance
    executive_summary = models.TextField(blank=True)
    key_metrics = models.JSONField(default=dict, blank=True)
    methodology_notes = models.TextField(blank=True)
    parameters = models.JSONField(default=dict, blank=True)

    # File Storage
    file_path = models.CharField(max_length=500, blank=True)
    file_size_bytes = models.BigIntegerField(default=0)

    # Attribution & Provenance
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_reports'
    )
    schedule = models.ForeignKey(
        ReportSchedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='executions'
    )

    # Review & Publication Workflow
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_reports'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comments = models.TextField(blank=True)
    published_report = models.ForeignKey(
        PublishedReport, on_delete=models.SET_NULL, null=True, blank=True, related_name='source_reports'
    )
    published_at = models.DateTimeField(null=True, blank=True)

    # Execution Performance & Errors
    error_message = models.TextField(blank=True)
    execution_duration_sec = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']
        verbose_name = 'Internal Generated Report'
        verbose_name_plural = 'Internal Generated Reports'

    def __str__(self):
        return f"{self.title} [{self.output_format.upper()}] - {self.get_status_display()}"

    @property
    def is_approved(self):
        return self.status in ['approved', 'published']

    @property
    def is_published(self):
        return self.status == 'published'
