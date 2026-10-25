# AgriLens PostgreSQL Database Architecture & Provenance Specification

**Project:** AgriLens • National Agricultural Productivity Intelligence Platform  
**Hackathon:** NISR 2026 Big Data Hackathon – Track 1: Agricultural Productivity  
**Document Version:** 2.0 &bull; Comprehensive Specification (Data Provenance, Notifications, ML & RBAC)  

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
4. **Idempotent Asynchronous Communications:**  
   Notification models isolate transaction-safe email logs and preferences with automatic retry counters to prevent duplicate notifications during network retries.

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
       └────────────────┬────────────────┘
                        │
        ┌───────────────┴───────────────┐
        ▼                               ▼
┌──────────────────────────────┐ ┌──────────────────────────────┐
│  Tier 4: Notification Core   │ │ Tier 5: Machine Learning Core│
│  • Notification              │ │ • Model Registry             │
│  • NotificationPreference    │ │ • Feature Weights / Clusters │
│  • SystemAnnouncement        │ │ • Inference Logs             │
│  • EmailDeliveryLog          │ └──────────────────────────────┘
└──────────────────────────────┘
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
    status = models.CharField(max_length=20, default='PENDING')  # PENDING, SUCCESS, FAILED
    error_log = models.TextField(blank=True)
```

---

## 4. Tier 1: Staging Tables (Immutable Raw Capture)

### Model: `StagingSASProduction`
Preserves authentic NISR column identifiers directly from `Rwa_raw_Season*202*_Production`:
* `batch` $\rightarrow$ FK to `ImportBatch`
* `Segment_ID` (BigInt)
* `s1q1` (Province numeric code: 1–5)
* `s1q2` (District numeric code: 11–57)
* `s1q3` (Stratum)
* `s4q3` (Crop Name)
* `s4q4` (Crop Code)
* `s4q5` (Plot Area)
* `s4q9` (Harvested Quantity)
* `weight` (Household sampling expansion factor)

---

## 5. Tier 2: Validated Domain Models

### Model: `ManualObservation` (Maker-Checker Submissions)
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

---

## 7. Tier 4: Notifications & Multi-Channel Communications

```python
class Notification(models.Model):
    class NotificationType(models.TextChoices):
        DATA_SUBMITTED = 'DATA_SUBMITTED', 'Data Submission'
        DATA_APPROVED = 'DATA_APPROVED', 'Data Approved'
        DATA_REJECTED = 'DATA_REJECTED', 'Data Rejected'
        PRICE_ALERT = 'PRICE_ALERT', 'Commodity Price Alert'
        REPORT_READY = 'REPORT_READY', 'Report Generated'
        ANNOUNCEMENT = 'ANNOUNCEMENT', 'System Announcement'
        SECURITY_ALERT = 'SECURITY_ALERT', 'Security & Access Alert'

    recipient = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=40, choices=NotificationType.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    action_url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

class NotificationPreference(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='notification_preference')
    email_on_submission = models.BooleanField(default=True)
    email_on_approval = models.BooleanField(default=True)
    email_on_price_alert = models.BooleanField(default=False)
    email_on_announcement = models.BooleanField(default=True)

class EmailDeliveryLog(models.Model):
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    notification = models.ForeignKey(Notification, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, default='PENDING')  # PENDING, SENT, FAILED
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    sent_at = models.DateTimeField(null=True, blank=True)
```

---

## 8. Tier 5: Machine Learning Models & Metadata Schema

Stores serialized ML pipelines (Random Forest yield predictors, K-Means clusterers) alongside version metrics:
- **`model_name`**: e.g., `yield_predictor_randomforest_v1`
- **`algorithm`**: `RandomForestRegressor(n_estimators=100, max_depth=12)`
- **`target_crop`**: e.g., `Maize`
- **`r2_score`**, **`mae`**, **`rmse`**: Empirical model evaluation metrics.
- **`feature_importance`**: JSON payload storing normalized weights for rainfall, fertilizer, irrigation, seed type, and soil pH.

---

## ⚖️ Intellectual Property, License & Usage Policy

> ### ⚠️ STRICT RESTRICTED USE NOTICE
> **All Rights Reserved © 2026 AgriLens Development Team.**
>
> 1. **Non-Commercial & No Personal Profit:**  
>    No individual, entity, or third party is permitted to use, copy, reproduce, monetize, sub-license, or exploit any portion of this codebase, architecture, machine learning models, algorithms, or visual designs for commercial purposes, revenue generation, or personal financial profit under any circumstances.
>
> 2. **Public Hackathon Visibility Disclaimer:**  
>    Although this repository is publicly accessible solely for the purpose of evaluation, review, and judging during the **2026 NISR Big Data Hackathon (Track 1: Agricultural Productivity)**, public availability does **NOT** constitute an open-source license, public domain dedication, or waiver of intellectual property rights.
>
> 3. **Prohibition of Modifications & Derivative Works:**  
>    Any unauthorized modification, alteration, redistribution, fork, decompilation, reverse-engineering, or derivation of this codebase or its underlying assets is strictly prohibited.
>
> 4. **Exclusive Authorization for NISR:**  
>    Operational utilization, institutional adoption, data integration, and platform deployment are **exclusively and solely permitted for the National Institute of Statistics of Rwanda (NISR)** and its officially designated national agricultural partners.
