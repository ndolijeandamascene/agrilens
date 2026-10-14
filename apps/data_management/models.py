"""
AgriLens Data Management, Staging, Provenance, and Quality Models.
Ensures strict lineage, separation of official vs manual records, and auditable ETL batches.
"""
from django.db import models
from django.conf import settings


class DataSource(models.Model):
    """
    Dynamic Data Source & Provenance Registry.
    Tracks official NISR surveys, agricultural censuses, administrative data,
    field extension reports, and manual submissions with full temporal and domain lineage.
    """
    # Standard presets maintained for backward compatibility with tests & scripts
    class SourceType(models.TextChoices):
        NISR_SAS_2024 = 'NISR_SAS_2024', 'NISR Seasonal Agricultural Survey 2024'
        NISR_SAS_2025 = 'NISR_SAS_2025', 'NISR Seasonal Agricultural Survey 2025'
        NISR_AHS_2024 = 'NISR_AHS_2024', 'NISR Agriculture Household Survey 2024'
        MANUAL_ENTRY = 'MANUAL_ENTRY', 'Authorized Manual Entry'
        OTHER = 'OTHER', 'Other Authorized Dataset'

    class DataKind(models.TextChoices):
        SURVEY = 'SURVEY', 'Official Statistical Survey (NISR SAS/AHS)'
        CENSUS = 'CENSUS', 'Agricultural Census'
        ADMINISTRATIVE = 'ADMINISTRATIVE', 'Administrative Records (MINAGRI/RAB)'
        EXTENSION_REPORT = 'EXTENSION_REPORT', 'Field Extension Observation'
        COOPERATIVE_DATA = 'COOPERATIVE_DATA', 'Farmer Cooperative Harvest Record'
        MARKET_SURVEY = 'MARKET_SURVEY', 'Market Price & Commercialization'
        RESEARCH_TRIAL = 'RESEARCH_TRIAL', 'Agronomic Trial / Research Plot'
        MANUAL_ENTRY = 'MANUAL_ENTRY', 'Direct Manual Agricultural Entry'
        OTHER = 'OTHER', 'Other Custom Dataset'

    name = models.CharField(max_length=150)
    source_type = models.CharField(
        max_length=80, 
        unique=True, 
        db_index=True, 
        help_text="Unique dataset slug or provenance identifier"
    )
    data_kind = models.CharField(
        max_length=40, 
        choices=DataKind.choices, 
        default=DataKind.MANUAL_ENTRY, 
        db_index=True,
        help_text="Kind / category of agricultural data"
    )
    year = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        db_index=True, 
        help_text="Reference survey/calendar year (e.g. 2024, 2025, 2026)"
    )
    season = models.CharField(
        max_length=20, 
        blank=True, 
        help_text="Season code (A, B, C, Annual, or All)"
    )
    organization = models.CharField(
        max_length=150, 
        blank=True, 
        help_text="Issuing institution, department, or cooperative"
    )
    description = models.TextField(blank=True)
    citation = models.CharField(max_length=255, blank=True)
    is_official_survey = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year', 'season', 'name']

    def save(self, *args, **kwargs):
        # Auto-generate dynamic source_type if not explicitly set
        if not self.source_type:
            org_slug = self.organization.strip().upper().replace(' ', '_')[:12] if self.organization else self.data_kind
            parts = [org_slug]
            if self.year:
                parts.append(str(self.year))
            if self.season:
                parts.append(str(self.season).upper().replace(' ', '_'))
            base_slug = "_".join(parts) or "DATA_SOURCE"
            slug = base_slug
            counter = 1
            while DataSource.objects.filter(source_type=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}_{counter}"
                counter += 1
            self.source_type = slug[:80]
        super().save(*args, **kwargs)

    def __str__(self):
        meta = []
        if self.year:
            meta.append(str(self.year))
        if self.season:
            meta.append(f"Season {self.season}")
        meta_str = f" ({', '.join(meta)})" if meta else ""
        return f"{self.name}{meta_str}"


class ImportBatch(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        SUCCESS = 'SUCCESS', 'Completed Successfully'
        FAILED = 'FAILED', 'Failed'
        PARTIAL = 'PARTIAL', 'Completed with Warnings'

    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='batches')
    filename = models.CharField(max_length=255)
    file_checksum = models.CharField(max_length=64, blank=True)
    total_rows = models.IntegerField(default=0)
    rows_accepted = models.IntegerField(default=0)
    rows_rejected = models.IntegerField(default=0)
    rows_skipped = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    summary_notes = models.TextField(blank=True)
    error_log = models.TextField(blank=True)

    def __str__(self):
        return f"Batch #{self.id} - {self.filename} ({self.get_status_display()})"


class StagingSASProduction(models.Model):
    """
    Tier 1 Raw Staging Table for SAS Production Records.
    Maintains exact source codes and raw values.
    """
    batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name='raw_sas_records')
    source_row_index = models.IntegerField()
    
    # Official NISR raw variables
    segment_id = models.CharField(max_length=60, db_index=True)
    s1q1 = models.IntegerField(null=True, blank=True, help_text="Province code")
    s1q2 = models.IntegerField(null=True, blank=True, help_text="District code")
    s1q3 = models.CharField(max_length=100, blank=True, help_text="Stratum")
    s1q6 = models.CharField(max_length=60, blank=True, help_text="Farmer ID")
    s1q7 = models.CharField(max_length=100, blank=True, help_text="Farmer Type")
    
    # Plot & Crop
    s2q1 = models.IntegerField(null=True, blank=True, help_text="Plot number")
    s2q2 = models.FloatField(null=True, blank=True, help_text="Plot area sqm")
    s2q2_ha = models.FloatField(null=True, blank=True, help_text="Plot area ha")
    s2q4 = models.CharField(max_length=150, blank=True, help_text="Crop name / code")
    crop_category = models.CharField(max_length=100, blank=True)
    
    # Inputs & Harvest
    s2q9 = models.CharField(max_length=20, blank=True, help_text="Used improved seed")
    s2q19_3 = models.FloatField(null=True, blank=True, help_text="Harvested kg to date")
    s2q20_2 = models.FloatField(null=True, blank=True, help_text="Remaining harvest kg")
    s2q21 = models.FloatField(null=True, blank=True, help_text="Total harvest kg")
    
    # Processing, Sales & Storage
    s2q25 = models.FloatField(null=True, blank=True, help_text="Transformed kg")
    s2q26 = models.FloatField(null=True, blank=True, help_text="Sold kg")
    s2q28 = models.FloatField(null=True, blank=True, help_text="Market price RWF/kg")
    s2q36 = models.FloatField(null=True, blank=True, help_text="Stored kg")
    s2q37 = models.CharField(max_length=150, blank=True, help_text="Storage facility type")
    
    # Post Harvest Losses (kg)
    loss_harvest_kg = models.FloatField(null=True, blank=True)
    loss_transport_kg = models.FloatField(null=True, blank=True)
    loss_storage_kg = models.FloatField(null=True, blank=True)
    loss_processing_kg = models.FloatField(null=True, blank=True)
    loss_sales_kg = models.FloatField(null=True, blank=True)
    
    # Fertilizers & Pesticides
    uses_organic_fert = models.CharField(max_length=20, blank=True)
    uses_inorganic_fert = models.CharField(max_length=20, blank=True)
    uses_pesticide = models.CharField(max_length=20, blank=True)
    
    plot_weight = models.FloatField(default=1.0)
    is_validated = models.BooleanField(default=False)
    validation_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['batch', 'segment_id']),
            models.Index(fields=['s1q2', 's2q4']),
        ]


class ValidatedObservation(models.Model):
    """
    Tier 2 Validated Domain Table.
    Normalised, foreign-key constrained observation record with explicit provenance.
    """
    batch = models.ForeignKey(ImportBatch, on_delete=models.PROTECT, related_name='observations')
    provenance = models.CharField(max_length=40, db_index=True) # e.g. NISR_SAS_2025
    season = models.ForeignKey('agriculture.AgriculturalSeason', on_delete=models.PROTECT, related_name='observations')
    district = models.ForeignKey('geography.District', on_delete=models.PROTECT, related_name='observations')
    sector = models.ForeignKey('geography.Sector', on_delete=models.SET_NULL, null=True, blank=True, related_name='observations')
    crop = models.ForeignKey('agriculture.Crop', on_delete=models.PROTECT, related_name='observations')
    
    # Linkage & identifiers
    source_record_id = models.CharField(max_length=100, db_index=True)
    segment_id = models.CharField(max_length=60, blank=True, db_index=True)
    plot_number = models.IntegerField(null=True, blank=True)
    farmer_type = models.CharField(max_length=60, blank=True)
    
    # Standardised Metrics
    plot_area_ha = models.DecimalField(max_digits=12, decimal_places=4)
    total_production_kg = models.DecimalField(max_digits=14, decimal_places=2)
    calculated_yield_kg_per_ha = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Agricultural Practices
    is_improved_seed = models.BooleanField(default=False)
    uses_organic_fertilizer = models.BooleanField(default=False)
    uses_inorganic_fertilizer = models.BooleanField(default=False)
    uses_pesticide = models.BooleanField(default=False)
    is_irrigated = models.BooleanField(default=False)
    has_anti_erosion = models.BooleanField(default=False)
    uses_mechanization = models.BooleanField(default=False)
    
    # Post-Harvest Loss & Commercialization
    quantity_sold_kg = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)
    market_price_rwf = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity_stored_kg = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)
    total_loss_kg = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)
    loss_rate_percentage = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Survey Expansion Weight
    sampling_weight = models.DecimalField(max_digits=14, decimal_places=4, default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['provenance', 'season', 'district']),
            models.Index(fields=['crop', 'season']),
            models.Index(fields=['district', 'crop']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['season', 'source_record_id'],
                name='unique_season_source_record'
            )
        ]

    def __str__(self):
        return f"{self.crop.name} in {self.district.name} ({self.season}) - {self.calculated_yield_kg_per_ha} kg/ha"


class ManualObservation(models.Model):
    """
    Authorized Manual Agricultural Data Entry.
    Includes strict audit trail and multi-step review/approval lifecycle.
    """
    class ReviewStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted for Review'
        APPROVED = 'APPROVED', 'Approved by Authority'
        REJECTED = 'REJECTED', 'Returned for Correction'

    review_status = models.CharField(
        max_length=20, 
        choices=ReviewStatus.choices, 
        default=ReviewStatus.DRAFT, 
        db_index=True
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='manual_entries')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_entries')
    review_comments = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Observation metadata
    reporting_organization = models.CharField(max_length=150, blank=True)
    observation_reference = models.CharField(max_length=100, blank=True)
    observation_date = models.DateField()

    # Dynamic Data Source & Classification
    data_source = models.ForeignKey(
        DataSource, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='manual_entries',
        help_text="Linked dynamic data source"
    )
    data_kind = models.CharField(
        max_length=40, 
        choices=DataSource.DataKind.choices, 
        default=DataSource.DataKind.EXTENSION_REPORT,
        db_index=True,
        help_text="Classification of submitted agricultural data"
    )
    
    # Domain fields
    season = models.ForeignKey('agriculture.AgriculturalSeason', on_delete=models.PROTECT, related_name='manual_entries')
    district = models.ForeignKey('geography.District', on_delete=models.PROTECT, related_name='manual_entries')
    sector = models.ForeignKey('geography.Sector', on_delete=models.PROTECT, related_name='manual_entries')
    crop = models.ForeignKey('agriculture.Crop', on_delete=models.PROTECT, related_name='manual_entries')
    
    # Area & Harvest
    plot_area_ha = models.DecimalField(max_digits=10, decimal_places=4)
    total_production_kg = models.DecimalField(max_digits=12, decimal_places=2)
    calculated_yield_kg_per_ha = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Practices
    is_irrigated = models.BooleanField(default=False)
    is_improved_seed = models.BooleanField(default=False)
    uses_inorganic_fertilizer = models.BooleanField(default=False)
    uses_organic_fertilizer = models.BooleanField(default=False)
    has_soil_conservation = models.BooleanField(default=False)
    uses_mechanization = models.BooleanField(default=False)
    
    # Post Harvest Loss & Sales
    loss_quantity_kg = models.DecimalField(max_digits=12, decimal_places=2, default=0.0, blank=True)
    quantity_sold_kg = models.DecimalField(max_digits=12, decimal_places=2, default=0.0, blank=True)
    farmgate_price_rwf = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Calculate yield automatically if positive area provided
        if self.plot_area_ha and self.plot_area_ha > 0 and self.total_production_kg is not None:
            self.calculated_yield_kg_per_ha = round(self.total_production_kg / self.plot_area_ha, 2)

        # Auto-link dynamic data source if none specified
        if not self.data_source and self.season:
            source_slug = f"MANUAL_{self.data_kind}_{self.season.year}_{self.season.season}"[:80]
            ds, _ = DataSource.objects.get_or_create(
                source_type=source_slug,
                defaults={
                    'name': f"{self.get_data_kind_display()} - {self.season.year} Season {self.season.season}",
                    'data_kind': self.data_kind,
                    'year': self.season.year,
                    'season': self.season.season,
                    'organization': self.reporting_organization or 'AgriLens Field Submissions',
                    'is_official_survey': False,
                    'description': f"Dynamic data source generated for manual {self.get_data_kind_display()} records."
                }
            )
            self.data_source = ds

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Manual Entry #{self.id} ({self.crop.name} - {self.district.name}) [{self.get_review_status_display()}]"


class DataQualityIssue(models.Model):
    class Severity(models.TextChoices):
        CRITICAL = 'CRITICAL', 'Critical (Blocks ingestion)'
        HIGH = 'HIGH', 'High (Distorts calculations)'
        MEDIUM = 'MEDIUM', 'Medium (Affects sub-analyses)'
        LOW = 'LOW', 'Low (Warning / Minor)'

    batch = models.ForeignKey(ImportBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name='qa_issues')
    dataset_name = models.CharField(max_length=150)
    variable_name = models.CharField(max_length=100)
    record_reference = models.CharField(max_length=120, blank=True)
    issue_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MEDIUM)
    description = models.TextField()
    recommended_action = models.TextField(blank=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.severity}] {self.dataset_name}:{self.variable_name} - {self.issue_type}"
