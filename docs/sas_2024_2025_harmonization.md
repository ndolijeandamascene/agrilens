# Harmonization Specification: NISR Seasonal Agricultural Survey (SAS) 2024 & 2025

**Platform:** AgriLens — Agricultural Intelligence & Decision-Support Platform for Rwanda  
**Author:** Senior Data Engineering & Agricultural Analytics Team  
**Status:** Approved & Implemented  
**Date:** October 2026  

---

## 1. Executive Summary & Harmonization Objective

The National Institute of Statistics of Rwanda (NISR) conducts the Seasonal Agricultural Survey (SAS) across three distinct agricultural seasons annually:
- **Season A:** September to February (Major season for cereals, legumes, roots)
- **Season B:** March to June/July (Major season for beans, maize, sorghum, vegetables)
- **Season C:** July to September (Marshland/swamp & irrigated farming, vegetables, sweet potatoes)

To enable robust, statistically valid multi-year trend analysis (2024 vs. 2025) and cross-season productivity comparisons, AgriLens establishes a **formal harmonization layer**. This specification documents exact variable mappings, unit conversions, categorical reconciliations, weighting schemes, and analytical caveats to ensure that no misleading growth rates or invalid cross-survey joins occur.

---

## 2. Structural & Observational Unit Comparison

| Dimension | SAS 2024 | SAS 2025 | Harmonized AgriLens Representation |
| :--- | :--- | :--- | :--- |
| **Primary Sampling Unit (PSU)** | Segment (`Segment_ID`) | Segment (`Segment_ID`) | Anonymized spatial PSU code (`segment_id`) |
| **Observation Unit** | Crop Plot within Segment/Holding | Crop Plot within Segment/Holding | `ValidatedObservation` (Plot × Crop × Season) |
| **Geographic Keys** | Province, District (`s1q1`, `s1q2`) | Province, District (`s1q1`, `s1q2`) | Official NISR District Code (`11` to `57`) |
| **Sector Level Data** | Available in cluster metadata | Available via segment geo-hierarchy | Authoritative NISR 416-sector link |
| **Survey Weight** | Expansion factor (`plot_weight`) | Expansion factor (`plot_weight`) | Standardized `sampling_weight` (Decimal 14,4) |
| **Primary File Format** | SPSS (`.sav`) / CSV | SPSS (`.sav`) with embedded value labels | Validated PostgreSQL Relational Model |

> [!IMPORTANT]  
> **Key Rule on Granularity:**  
> SAS 2024 and SAS 2025 observe agricultural activities at the **crop-plot level**, whereas the Agricultural Household Survey (AHS 2024) observes agricultural activities at the **household and parcel level**. They must **never** be merged row-by-row into a single undifferentiated table. Harmonization between SAS and AHS occurs strictly at aggregate district/sector and thematic indicator levels.

---

## 3. Core Variable Harmonization Matrix

### 3.1. Production & Productivity (Yield)

| Indicator / Concept | SAS 2024 Source Variable | SAS 2025 Source Variable | Transformation / Harmonization Rule | AgriLens Field | Comparability Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Crop Identification** | `s2q4` (Numeric + Label) | `s2q4` (Numeric + Label) | Direct match via official NISR 97-crop classification table. | `crop_id` (FK: `Crop`) | **Verified Comparable** |
| **Plot Area (Hectares)** | `s2q2` (sqm) / 10,000 | `s2q2` (sqm) / 10,000 | Convert $m^2$ to hectares ($\frac{s2q2}{10000}$). Ensure $Area_{ha} > 0$. | `plot_area_ha` | **Verified Comparable** |
| **Total Production (Kg)** | `s2q21` (Total harvest kg) | `s2q21` (Total harvest kg) | Retain raw reported kg; fallback `s2q19_3` (harvested to date). | `total_production_kg` | **Verified Comparable** |
| **Yield (Kg / Ha)** | Calculated: $\frac{s2q21}{Area_{ha}}$ | Calculated: $\frac{s2q21}{Area_{ha}}$ | Recalculated systematically as $\frac{Total\_Production\_Kg}{Plot\_Area\_Ha}$ to prevent pre-rounded discrepancies. | `calculated_yield_kg_per_ha` | **Verified Comparable** |

### 3.2. Agricultural Practices & Input Adoption (Verified Section 4 & 3 Variables)

| Practice | SAS 2024 Source Code | SAS 2025 Source Code | Binary Harmonization Rule | AgriLens Field | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Plot Irrigation** | `s4q15` (1=Yes, 2=No) | `s4q14` (1=Yes, 2=No) | Year-aware: 2024 uses `s4q15`; 2025 uses `s4q14` | `is_irrigated` | Note: 2024 `s4q14` was operator-level practice |
| **Improved Seeds** | `s2q9` (1=Yes, 2=No) | `s2q9` (1=Yes, 2=No) | If $x == 1.0 \to \text{True}$; Else $\text{False}$ | `is_improved_seed` | Asked per crop across operator plots |
| **Organic Fertilizer** | `s3q3` (1=Yes, 2=No) | `s3q3` (1=Yes, 2=No) | If $x == 1.0 \to \text{True}$; Else $\text{False}$ | `uses_organic_fertilizer` | Farmyard manure, compost (Section 3) |
| **Inorganic Fertilizer** | `s3q9` (1=Yes, 2=No) | `s3q9` (1=Yes, 2=No) | If $x == 1.0 \to \text{True}$; Else $\text{False}$ | `uses_inorganic_fertilizer` | DAP, UREA, NPK (Section 3) |
| **Anti-Erosion Activities**| `s4q3` (1=Yes, 2=No) | `s4q3` (1=Yes, 2=No) | If $x == 1.0 \to \text{True}$; Else $\text{False}$ | `has_anti_erosion` | Ditches, progressive/radical terraces (Section 4) |
| **Mechanization Equipment**| `s4q9` (1=Yes, 2=No) | `s4q9` (1=Yes, 2=No) | If $x == 1.0 \to \text{True}$; Else $\text{False}$ | `uses_mechanization` | Tractor, power-tiller, thresher (Section 4) |

### 3.3. Post-Harvest Losses, Sales & Storage

| Concept | SAS 2024 Variable | SAS 2025 Variable | Harmonization Formula | AgriLens Field | Comparability Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Quantity Sold (Kg)** | `s2q26` | `s2q26` | If empty $\to 0.0$. | `quantity_sold_kg` | **Verified Comparable** |
| **Farmgate Price (RWF/Kg)**| `s2q28` | `s2q28` | Unit: Rwandan Francs per kilogram. | `market_price_rwf` | **Verified Comparable** |
| **Quantity Stored (Kg)** | `s2q36` | `s2q36` | If empty $\to 0.0$. Storage facility in `s2q37`. | `quantity_stored_kg` | **Verified Comparable** |
| **Total Post-Harvest Loss**| Sum of `s2q45`–`s2q50` | Sum of `s2q45`–`s2q50` | $\sum (\text{Harvest } s2q45 + \text{Transport } s2q46 + \text{Storage } s2q47 + \text{Process } s2q48 + \text{Sales } s2q50)$ | `total_loss_kg` | **Verified Comparable** |
| **Loss Rate (%)** | Derived: $\frac{Loss}{Prod + Loss} \times 100$ | Derived: $\frac{Loss}{Prod + Loss} \times 100$ | Calculated on gross harvest volume ($\text{Harvested} + \text{Loss}$). | `loss_rate_percentage` | **Verified Comparable** |

---

## 4. Statistically Valid Weighting & Aggregation Protocol

### 4.1. The Fallacy of Unweighted Arithmetic Means
In agricultural survey sampling, smallholder plots in high-density rural areas and large commercial marshlands do not have equal selection probabilities. Therefore:
$$\bar{Y}_{\text{unweighted}} = \frac{1}{n} \sum_{i=1}^n \frac{P_i}{A_i} \quad \text{IS NOT POPULATION YIELD.}$$

### 4.2. Authoritative NISR Weighted Formulae
AgriLens implements the following weighted estimators:

1. **Total Estimated National/District Production:**
   $$\hat{P}_{\text{total}} = \sum_{i=1}^n \left( W_i \times P_i \right)$$
   Where $W_i$ is `sampling_weight` and $P_i$ is `total_production_kg`.

2. **Total Estimated National/District Cultivated Area:**
   $$\hat{A}_{\text{total}} = \sum_{i=1}^n \left( W_i \times A_i \right)$$
   Where $A_i$ is `plot_area_ha`.

3. **Weighted Average Crop Yield (Kg/Ha):**
   $$\hat{Y}_{\text{weighted}} = \frac{\sum_{i=1}^n \left( W_i \times P_i \right)}{\sum_{i=1}^n \left( W_i \times A_i \right)} = \frac{\hat{P}_{\text{total}}}{\hat{A}_{\text{total}}}$$

4. **Input Adoption Rate (% of Cultivated Area):**
   $$\text{Adoption Rate} = \frac{\sum_{i=1}^n \left( W_i \times A_i \times \mathbb{I}(\text{Practice}_i = \text{True}) \right)}{\sum_{i=1}^n \left( W_i \times A_i \right)} \times 100\%$$

---

## 5. Temporal Harmonization & Season Comparability

| Comparison Scenario | Validity | Scientific Rationale |
| :--- | :--- | :--- |
| **SAS 2024 Season A vs. SAS 2025 Season A** | **VALID** | Same agricultural cycle, identical seasonal precipitation patterns, identical crop types (cereals/tubers). |
| **SAS 2024 Season B vs. SAS 2025 Season B** | **VALID** | Same agricultural cycle, comparable harvesting windows (legumes/grains). |
| **SAS Season A vs. SAS Season B (Within Year)** | **CONDITIONAL** | Valid for season-over-season output shifts, but crop-specific yields differ naturally due to rainfall variations. |
| **SAS Season A vs. SAS Season C** | **INVALID for Direct Yield Comparison** | Season C is restricted to marshlands/swamps; yields are disproportionately higher due to full irrigation. Must be analyzed as a distinct agro-ecological sub-sector. |

---

## 6. Audit Trail & Provenance Segregation

1. Every row in `ValidatedObservation` maintains its source tag:
   - `NISR_SAS_2024`
   - `NISR_SAS_2025`
   - `NISR_AHS_2024`
   - `MANUAL_ENTRY`
2. Analytical views, dashboard charts, and API endpoints filter strictly by `provenance.startswith('NISR_')` by default.
3. Manual observations (`MANUAL_ENTRY`) are accessible under dedicated Data Governance reviews and can only be included in analytics if explicitly toggled by an authorized analyst via `source_filter=all`.

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

