# AgriLens PostgreSQL Database Architecture & Provenance Specification

**Project:** AgriLens • National Agricultural Productivity Intelligence Platform  
**Hackathon:** NISR 2026 Big Data Hackathon – Track 1: Agricultural Productivity  
**Date:** October 2026  
**Status:** Approved Architectural Design (Stage 3 Deliverable)  

---

## 1. Design Principles

1. **Strict Provenance Isolation:**  
   Every record stores its exact origin (`provenance`), import batch (`import_batch_id`), and source record identifier. Official NISR statistics never mix with manual entries unless explicitly requested by authorized administrative filters.
2. **Three-Tier Storage Model:**  
   - **Tier 1: Staging Tables (`staging_*`):** High-throughput ingestion retaining immutable source variables and strings.
   - **Tier 2: Validated Domain Tables:** Strongly typed, foreign-key constrained tables for crops, plots, districts, practices, and inputs.
   - **Tier 3: Analytical & Indicator Views (`analytics_*`):** Harmonized aggregates, weighted yield calculations, and productivity gap metrics.
3. **Audit Trail & Role-Based Workflows:**  
   Manual data entry flows through a verifiable lifecycle: `Draft ➔ Submitted ➔ Reviewed ➔ Approved`. All edits are tracked with timestamps, user foreign keys, and change justifications.

---

## 2. Logical Data Architecture Diagram

```text
               RAW SURVEY INGESTION
          (SAS 2024, SAS 2025, AHS 2024)
                        │
                        ▼
       ┌─────────────────────────────────┐
       │   Tier 1: Staging Tables        │
       │   • StagingSASProduction        │
       │   • StagingSASPractices         │
       │   • StagingAHSProduction        │
       └────────────────┬────────────────┘
                        │ Validation, Range Checks, QA Rules
                        ▼
       ┌─────────────────────────────────┐
       │   Tier 2: Validated Domain      │
       │   • Province / District / Sector│
       │   • Crop / Season               │
       │   • ValidatedObservation        │
       │     (provenance flag)           │
       │   • ManualObservation           │
       │     (approval workflow)         │
       └────────────────┬────────────────┘
                        │ Weighted Aggregation
                        ▼
       ┌─────────────────────────────────┐
       │   Tier 3: Analytical Core       │
       │   • ProductivityMetric          │
       │   • YieldGapAnalysis            │
       │   • PracticeAdoptionKPI         │
       └─────────────────────────────────┘
```

---

## 3. Provenance & Data Source Registry

### Model: `DataSource` & `ImportBatch`
```python
class DataSource(models.Model):
    class SourceType(models.TextChoices):
        NISR_SAS_2024 = 'NISR_SAS_2024', 'NISR Seasonal Agricultural Survey 2024'
        NISR_SAS_2025 = 'NISR_SAS_2025', 'NISR Seasonal Agricultural Survey 2025'
        NISR_AHS_2024 = 'NISR_AHS_2024', 'NISR Agriculture Household Survey 2024'
        MANUAL_ENTRY = 'MANUAL_ENTRY', 'Authorized Manual Entry'
        OTHER = 'OTHER', 'Other Authorized Dataset'

    name = models.CharField(max_length=100)
    source_type = models.CharField(max_length=40, choices=SourceType.choices, unique=True)
    description = models.TextField(blank=True)
    citation = models.CharField(max_length=255, blank=True)
    is_official_survey = models.BooleanField(default=True)

class ImportBatch(models.Model):
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='batches')
    filename = models.CharField(max_length=255)
    file_checksum = models.CharField(max_length=64)
    total_rows = models.IntegerField(default=0)
    rows_accepted = models.IntegerField(default=0)
    rows_rejected = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='PENDING') # PENDING, SUCCESS, FAILED
    error_log = models.TextField(blank=True)
```

---

## 4. Tier 1: Staging Tables (Immutable Raw Capture)

### Model: `StagingSASProduction`
Preserves authentic NISR column identifiers directly from `Rwa_raw_Season*202*_Production`:
* `batch` $\rightarrow$ FK to `ImportBatch`
* `Segment_ID` (BigInt)
* `s1q1` (Province numeric code)
* `s1q2` (District numeric code)
* `s1q3` (Stratum)
* `s1q6` (Farmer ID)
* `s1q7` (Farmer / LSF type)
* `s2q1` (Plot number)
* `s2q2` (Plot area sqm)
* `s2q2_ha` (Plot area ha)
* `s2q4` (Crop name string / code)
* `CropCategory` (Category string)
* `s2q9` (Improved seed flag)
* `s2q19_3` (Harvested kg)
* `s2q20_2` (Remaining harvest kg)
* `s2q21` (Total production kg)
* `s2q25` (Transformed / processed kg)
* `s2q26` (Quantity sold kg)
* `s2q28` (Market unit price)
* `s2q36` (Stored quantity kg)
* `s2q37` (Storage facility)
* Post-harvest loss fields (`s2q41` to `s2q50`)
* `s3q3`, `s3q9`, `s3q18` (Fertilizer & Pesticide flags)
* `plot_weight` (Sampling weight)

---

## 5. Tier 2: Validated Domain & Observation Tables

### Model: `ValidatedObservation`
Represents cleaned, verified, and mapped agricultural plot-level records:
```python
class ValidatedObservation(models.Model):
    batch = models.ForeignKey(ImportBatch, on_delete=models.PROTECT, related_name='observations')
    provenance = models.CharField(max_length=40, db_index=True) # e.g. NISR_SAS_2025
    season = models.ForeignKey('agriculture.AgriculturalSeason', on_delete=models.PROTECT)
    district = models.ForeignKey('geography.District', on_delete=models.PROTECT)
    sector = models.ForeignKey('geography.Sector', on_delete=models.SET_NULL, null=True, blank=True)
    crop = models.ForeignKey('agriculture.Crop', on_delete=models.PROTECT)
    
    # Identifiers
    segment_id = models.CharField(max_length=50, blank=True, db_index=True)
    plot_number = models.IntegerField(null=True, blank=True)
    farmer_type = models.CharField(max_length=50, blank=True)
    
    # Area & Production
    plot_area_ha = models.DecimalField(max_digits=10, decimal_places=4)
    total_production_kg = models.DecimalField(max_digits=12, decimal_places=2)
    calculated_yield_kg_per_ha = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Practices
    is_improved_seed = models.BooleanField(default=False)
    uses_organic_fertilizer = models.BooleanField(default=False)
    uses_inorganic_fertilizer = models.BooleanField(default=False)
    uses_pesticide = models.BooleanField(default=False)
    is_irrigated = models.BooleanField(default=False)
    has_anti_erosion = models.BooleanField(default=False)
    uses_mechanization = models.BooleanField(default=False)
    
    # Post-Harvest Losses (kg)
    total_loss_kg = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    loss_rate_percentage = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Sampling Weight
    sampling_weight = models.DecimalField(max_digits=12, decimal_places=4, default=1.0)
    
    class Meta:
        indexes = [
            models.Index(fields=['provenance', 'season', 'district']),
            models.Index(fields=['crop', 'season']),
        ]
```

### Model: `ManualObservation` (Audited Manual Submissions)
```python
class ManualObservation(models.Model):
    class ReviewStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted for Review'
        APPROVED = 'APPROVED', 'Approved by Authority'
        REJECTED = 'REJECTED', 'Returned for Correction'

    review_status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.DRAFT, db_index=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='manual_entries')
    reviewed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_entries')
    review_comments = models.TextField(blank=True)
    
    # Domain fields
    season = models.ForeignKey('agriculture.AgriculturalSeason', on_delete=models.PROTECT)
    district = models.ForeignKey('geography.District', on_delete=models.PROTECT)
    sector = models.ForeignKey('geography.Sector', on_delete=models.PROTECT)
    crop = models.ForeignKey('agriculture.Crop', on_delete=models.PROTECT)
    
    plot_area_ha = models.DecimalField(max_digits=10, decimal_places=4)
    total_production_kg = models.DecimalField(max_digits=12, decimal_places=2)
    calculated_yield_kg_per_ha = models.DecimalField(max_digits=12, decimal_places=2)
    
    is_irrigated = models.BooleanField(default=False)
    is_improved_seed = models.BooleanField(default=False)
    uses_inorganic_fertilizer = models.BooleanField(default=False)
    loss_quantity_kg = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

---

## 6. Tier 3: Statistical Indicators & Aggregates

Aggregates `avg_yield_kg_per_ha` and productivity gaps using verified survey expansion weights:

$$\text{Weighted Yield} = \frac{\sum (\text{production\_kg}_i \times \text{weight}_i)}{\sum (\text{plot\_area\_ha}_i \times \text{weight}_i)}$$

$$\text{Productivity Gap \%} = \frac{\text{Yield}_{\text{Ref}} - \text{Yield}_{\text{Dist}}}{\text{Yield}_{\text{Ref}}} \times 100$$

By default, Tier 3 calculations execute exclusively where `provenance IN ('NISR_SAS_2024', 'NISR_SAS_2025')`. Manual entries are only evaluated under dedicated user-selected filter scenarios.
