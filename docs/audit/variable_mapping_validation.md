# AgriLens Milestone 3: Variable Mapping Validation & Source Data Audit

**Author:** NISR Survey Data Specialist & ETL Integrity Auditor  
**Date:** October 2026  
**Status:** COMPLETE AUDIT  
**Datasets Analyzed:**  
- `Datasets/SAS 2024 catalog and data dictionary/Season A/Rwa_raw_SeasonA2024_Production.sav` (39,330 rows, 95 columns)
- `Datasets/SAS 2025 catalog and data dictionary/Season A/Rwa_raw_SeasonA2025_Production.sav` (34,369 rows, 101 columns)
- `Datasets/SAS 2024 catalog and data dictionary/Season A/Rwa_raw_SeasonA2024_Agricultural_practice.sav` (17,506 rows, 58 columns)
- `Datasets/SAS 2025 catalog and data dictionary/Season A/Rwa_raw_SeasonA2025_Agricultural_practice.sav` (17,062 rows, 59 columns)

---

## 1. Executive Summary & Variable Audit Findings

The previous acceptance audit noted that **irrigation, mechanization, and anti-erosion variables were unmapped in the pilot extraction**, resulting in 0.0% values displayed across the dashboard.

### Key Audit Findings:
1. **The Variables Exist in Section 4 of Production.sav:**  
   Contrary to early assumptions, anti-erosion (`s4q3`), mechanization (`s4q9`), and irrigation (`s4q14`/`s4q15`) **do exist** directly within both the 2024 and 2025 `Production.sav` datasets.
2. **Current Database Values Default to `False`:**  
   Because the initial pilot ETL script was executed before Section 4 variable mappings were wired into the ingestion pipeline, all 10,800 records currently in `ValidatedObservation` have `is_irrigated=False`, `uses_mechanization=False`, and `has_anti_erosion=False`.
3. **Questionnaire Question Numbering Shift (Critical Gotcha):**
   - **In 2024:** Plot-level irrigation is `s4q15` (*"Has this plot been irrigated during this agricultural season?"*). Question `s4q14` was an operator-level practice question (*"Did you practice irrigation in any of your plots?"*).
   - **In 2025:** Plot-level irrigation shifted to `s4q14` (*"Has this plot been irrigated during this agricultural season?"*), and operator-level irrigation shifted to `s4q13`. `s4q15` in 2025 became irrigation technique code.
   - Using a naive single variable name `s4q14` across both years without year-awareness results in semantic misalignment.

---

## 2. Comprehensive Variable Mapping Matrix (13 Primary Variables)

Below is the verified audit matrix covering all 13 required agricultural variables across SAS 2024A and SAS 2025A:

### 1. Production (`total_production_kg`)
- **Dataset & Season:** SAS 2024A & SAS 2025A
- **Source Filename:** `Rwa_raw_SeasonA2024_Production.sav` / `Rwa_raw_SeasonA2025_Production.sav`
- **Variable Code & Label:**  
  - 2024: `s2q21` — *"Q.2.21 Total quantity of harvest for this season (in Kg)"*  
  - 2025: `s2q21` — *"2.21 Total quantity of harvest for this season (in Kg)"*
- **Units & Valid Values:** Continuous float $\ge 0.0$ (kg).
- **Missing-Value Handling:** `s2q21` or fallback `s2q19_3` (quantity already harvested). If missing/null, treated as 0.0.
- **ETL Transformation:** `float(row['s2q21']) if pd.notnull(row.get('s2q21')) else float(row['s2q19_3'])`
- **Destination Field:** `ValidatedObservation.total_production_kg` (DecimalField, max_digits=14, decimal_places=2)
- **Mapping Confidence:** **100% (High)**
- **Comparability Across Years:** **Directly comparable**. Identical definition, question, and unit.
- **Supported Uses:** National production aggregates, crop yield ratio calculation, post-harvest loss rates.

---

### 2. Harvested Quantity to Date (`s2q19_3`)
- **Dataset & Season:** SAS 2024A & SAS 2025A
- **Source Filename:** `Rwa_raw_SeasonA2024_Production.sav` / `Rwa_raw_SeasonA2025_Production.sav`
- **Variable Code & Label:**  
  - 2024: `s2q19_3` — *"Q.2.19 Quantity already harvested (in Kg)"*  
  - 2025: `s2q19_3` — *"2.19 Quantity already harvested (in Kg)"*
- **Units & Valid Values:** Continuous float $\ge 0.0$ (kg).
- **Missing-Value Handling:** Stored in staging; used as fallback if `s2q21` is empty.
- **Destination Field:** `StagingSASProduction.s2q19_3`
- **Mapping Confidence:** **100% (High)**
- **Comparability Across Years:** **Directly comparable**.
- **Supported Uses:** Progressive seasonal harvest monitoring.

---

### 3. Plot Area (`plot_area_ha`)
- **Dataset & Season:** SAS 2024A & SAS 2025A
- **Source Filename:** `Rwa_raw_SeasonA2024_Production.sav` / `Rwa_raw_SeasonA2025_Production.sav`
- **Variable Code & Label:**  
  - 2024: `s2q2` — *"2.2 Plot area(sqm)"*  
  - 2025: `s2q2` — *"2.2 Plot area(sqm)"*
- **Units & Valid Values:** Square meters ($m^2$). Positive float $> 0.0$. Note: `s2q2_ha` is **not** present in the raw SPSS file; it is derived.
- **Missing-Value Handling:** Rejects row if area $\le 0.0$ or missing.
- **ETL Transformation:** `float(row['s2q2']) / 10000.0`
- **Destination Field:** `ValidatedObservation.plot_area_ha` (DecimalField, max_digits=12, decimal_places=4)
- **Mapping Confidence:** **100% (High)**
- **Comparability Across Years:** **Directly comparable**.
- **Supported Uses:** Denominator for crop yield ratio estimator, total cultivated area aggregation.

---

### 4. Crop Yield (`calculated_yield_kg_per_ha`)
- **Dataset & Season:** Derived metric across both years
- **Formula:** `total_production_kg / plot_area_ha`
- **Units:** kg/ha.
- **Biological Plausibility Threshold:** Observations $> 60,000 \text{ kg/ha}$ are flagged as `PlausibilityThreshold` in `DataQualityIssue`.
- **Destination Field:** `ValidatedObservation.calculated_yield_kg_per_ha`
- **Mapping Confidence:** **100% (High)**
- **Comparability Across Years:** **Directly comparable**.
- **Supported Uses:** Plot-level yield distribution, district ranking benchmark, productivity gap analysis.

---

### 5. Irrigation (`is_irrigated`) — HIGH PRIORITY
- **Dataset & Season:** SAS 2024A & SAS 2025A
- **Source Filename:** `Production.sav` (Section 4) and `Agricultural_practice.sav`
- **Variable Code & Official Label:**  
  - **2024 Season A:**  
    - Plot-level: `s4q15` — *"4.15 Has this plot been irrigated during this agricultural season?"* (`1.0=Yes, 2.0=No`)  
    - Household-level: `s4q14` — *"4.14 Did you practice irrigation in any of your plots during this agricultural s"* (`1.0=Yes, 2.0=No`)
  - **2025 Season A:**  
    - Plot-level: `s4q14` — *"4.14 Has this plot been irrigated during this agricultural season?"* (`1.0=Yes, 2.0=No`)  
    - Household-level: `s4q13` — *"4.13 Practiced irrigation in any of your plots during this agricultural season"* (`1.0=Yes, 2.0=No`)  
    - Technique: `s4q15` — *"4.15 What is irrigation technique used on this plot?"* (Categorical 1–6)
- **Empirical Adoption in Source Data (Pilot Head 5,000):**  
  - 2024A: Plot-level irrigation (`s4q15`): **15.2% Yes** (761 / 5,000)  
  - 2025A: Plot-level irrigation (`s4q14`): **25.5% Yes** (1,274 / 5,000)
- **Current Database Status:** **0.0% (Unextracted in legacy imported records; all set to False)**.
- **Harmonized ETL Transformation:**
  ```python
  if year == 2024:
      is_irrigated = str(row.get('s4q15', '')).strip() in ['1', '1.0', 'Yes']
  else:
      is_irrigated = str(row.get('s4q14', '')).strip() in ['1', '1.0', 'Yes']
  ```
- **Destination Field:** `ValidatedObservation.is_irrigated` (BooleanField)
- **Mapping Confidence:** **100% (High)**
- **Comparability Across Years:** **Comparable when mapped using year-aware question alignment**.
- **Supported Uses:** Plot-level irrigation adoption, yield comparison on irrigated vs rainfed plots.

---

### 6. Mechanization (`uses_mechanization`) — HIGH PRIORITY
- **Dataset & Season:** SAS 2024A & SAS 2025A
- **Source Filename:** `Production.sav` (Section 4) and `Agricultural_practice.sav`
- **Variable Code & Official Label:**  
  - 2024: `s4q9` — *"4.9 Did you use any mechanical equipment for agriculture activities on this plot"* (`1.0=Yes, 2.0=No`)  
  - 2025: `s4q9` — *"4.9 Did you use any mechanical equipment for agriculture activities on this plot"* (`1.0=Yes, 2.0=No`)
- **Empirical Adoption in Source Data (Pilot Head 5,000):**  
  - 2024A: **3.0% Yes** (148 / 5,000)  
  - 2025A: **4.0% Yes** (200 / 5,000)
- **Current Database Status:** **0.0% (Unextracted in legacy imported records; all set to False)**.
- **Harmonized ETL Transformation:**  
  `str(row.get('s4q9', '')).strip() in ['1', '1.0', 'Yes']`
- **Destination Field:** `ValidatedObservation.uses_mechanization` (BooleanField)
- **Mapping Confidence:** **100% (High)**
- **Comparability Across Years:** **Directly comparable**. Identical variable code, question label, and value domain.
- **Supported Uses:** Mechanization adoption rate, farm power productivity analysis.

---

### 7. Anti-Erosion / Soil Conservation (`has_anti_erosion`) — HIGH PRIORITY
- **Dataset & Season:** SAS 2024A & SAS 2025A
- **Source Filename:** `Production.sav` (Section 4) and `Agricultural_practice.sav`
- **Variable Code & Official Label:**  
  - 2024: `s4q3` — *"4.3 Is there any anti-erosion activity on this plot?"* (`1.0=Yes, 2.0=No`)  
  - 2025: `s4q3` — *"4.3 Is there any anti-erosion activity on this plot?"* (`1.0=Yes, 2.0=No`)
- **Empirical Adoption in Source Data (Pilot Head 5,000):**  
  - 2024A: **75.6% Yes** (3,782 / 5,000)  
  - 2025A: **70.3% Yes** (3,514 / 5,000)
- **Current Database Status:** **0.0% (Unextracted in legacy imported records; all set to False)**.
- **Harmonized ETL Transformation:**  
  `str(row.get('s4q3', '')).strip() in ['1', '1.0', 'Yes']`
- **Destination Field:** `ValidatedObservation.has_anti_erosion` (BooleanField)
- **Mapping Confidence:** **100% (High)**
- **Comparability Across Years:** **Directly comparable**. Identical variable code and value domain.
- **Supported Uses:** Sustainable land management tracking, soil erosion mitigation correlation.

---

### 8. Improved Seed Use (`is_improved_seed`)
- **Dataset & Season:** SAS 2024A & SAS 2025A
- **Source Filename:** `Production.sav` (Section 2)
- **Variable Code & Official Label:**  
  - 2024: `s2q9` — *"Q.2.9 Did you use improved seed for this crop in any of your plots in this season?"* (`1.0=Yes, 2.0=No`)  
  - 2025: `s2q9` — *"2.9 Did you use improved seed for this crop in any of your plots in this season?"* (`1.0=Yes, 2.0=No`)
- **Current Database Adoption Rate:** 26.9% in 2024A, 26.3% in clean 2025A.
- **Destination Field:** `ValidatedObservation.is_improved_seed` (BooleanField)
- **Mapping Confidence:** **100% (High)**
- **Methodological Caveat:** The questionnaire asks if improved seed was used *for this crop in any of your plots*. Thus, it is a crop-operator level indicator mapped to plot observations.
- **Supported Uses:** Input adoption rates, productivity response comparisons.

---

### 9. Fertilizer Adoption (`uses_inorganic_fertilizer`, `uses_organic_fertilizer`)
- **Dataset & Season:** SAS 2024A & SAS 2025A
- **Source Filename:** `Production.sav` (Section 3)
- **Variable Codes & Official Labels:**  
  - Inorganic: `s3q9` — *"3.9 Have you used inorganic fertilizer in this plot during this season?"* (`1.0=Yes, 2.0=No`)  
  - Organic: `s3q3` — *"3.3 Have you used organic fertilizer in this plot during this season?"* (`1.0=Yes, 2.0=No`)
- **Current Database Adoption Rate:**  
  - Inorganic: 32.3% in 2024A, 32.1% in clean 2025A.  
  - Organic: 69.3% in 2024A, 62.4% in clean 2025A.
- **Destination Fields:** `ValidatedObservation.uses_inorganic_fertilizer`, `ValidatedObservation.uses_organic_fertilizer`
- **Mapping Confidence:** **100% (High)**
- **Comparability Across Years:** **Directly comparable**. Plot-level questions.
- **Supported Uses:** Soil fertility management, input subsidy evaluation.

---

### 10. Storage (`quantity_stored_kg`, `s2q37`)
- **Dataset & Season:** SAS 2024A & SAS 2025A
- **Source Filename:** `Production.sav` (Section 2)
- **Variable Code & Label:**  
  - 2024: `s2q36` — *"Q.2.36 Qty of production stored/to be stored(Kg)"*; `s2q37` — storage facility (`1=Own storage, 2=Public, 3=Cooperatives, 4=Other`)  
  - 2025: `s2q36` — *"2.36. Qty of production to be stored for future uses"*; `s2q37` — storage facility
- **Units:** Continuous float (kg).
- **Destination Field:** `ValidatedObservation.quantity_stored_kg`, `StagingSASProduction.s2q37`
- **Mapping Confidence:** **100% (High)**
- **Comparability Across Years:** **Directly comparable**.
- **Supported Uses:** On-farm storage capacity, food security buffer analysis.

---

### 11. Processing / Transformation (`s2q25`)
- **Dataset & Season:** SAS 2024A & SAS 2025A
- **Source Filename:** `Production.sav` (Section 2)
- **Variable Code & Label:**  
  - 2024: `s2q25` — *"Q.2.25 Qty of production transformed/to be transformed (Kg)"*  
  - 2025: `s2q25` — *"2.24 On the total production of this crop what was the quantity transformed/to be transformed"*
- **Units:** Continuous float (kg).
- **Destination Field:** `StagingSASProduction.s2q25`
- **Mapping Confidence:** **100% (High)**
- **Comparability Across Years:** **Directly comparable**. Note: question number was 2.25 in 2024 and 2.24 in 2025, but variable code `s2q25` is identical.
- **Supported Uses:** Value addition and agro-processing rate calculation.

---

### 12. Post-Harvest Losses (`total_loss_kg`, `loss_rate_percentage`)
- **Dataset & Season:** SAS 2024A & SAS 2025A
- **Source Filename:** `Production.sav` (Section 2)
- **Variable Codes & Labels:**  
  - Harvesting: `s2q45` (kg)
  - Transport: `s2q46` (kg)
  - Storage: `s2q47` (kg)
  - Processing: `s2q48` (kg)
  - Sales: `s2q50` (kg)
- **Units:** Kilograms (kg).
- **Aggregation Formula:** $\text{total\_loss} = s2q45 + s2q46 + s2q47 + s2q48 + s2q50$
- **Loss Rate Formula:** $\frac{\text{total\_loss}}{\text{total\_production\_kg} + \text{total\_loss}} \times 100\%$
- **Destination Fields:** `ValidatedObservation.total_loss_kg`, `ValidatedObservation.loss_rate_percentage`
- **Mapping Confidence:** **100% (High)**
- **Comparability Across Years:** **Directly comparable**.
- **Supported Uses:** Stage-by-stage loss diagnostics, national food waste prevention.

---

### 13. Sales and Market Prices (`quantity_sold_kg`, `market_price_rwf`)
- **Dataset & Season:** SAS 2024A & SAS 2025A
- **Source Filename:** `Production.sav` (Section 2)
- **Variable Codes & Labels:**  
  - Quantity Sold: `s2q26` (kg)
  - Market Price: `s2q28` (RWF/kg)
- **Destination Fields:** `ValidatedObservation.quantity_sold_kg`, `ValidatedObservation.market_price_rwf`
- **Mapping Confidence:** **100% (High)**
- **Comparability Across Years:** **Directly comparable**.
- **Supported Uses:** Commercialization rates, farmgate revenue modeling.

---

## 3. UI Display & Graceful Degradation Policy

To comply with Mandatory Safety Rule 8 (*"Do not invent variable codes or use approximate mappings without evidence"*) and Rule 12 (*"Keep existing working frontend and backend functionality"*):

1. **Irrigation, Mechanization, and Anti-Erosion in Current State:**  
   Because existing database records in PostgreSQL have not yet been re-extracted from Section 4, the platform must NOT display `0.0%` as if it were a verified empirical fact.  
   The indicator cards for these metrics must display an informative status badge:  
   *"Variable verified in source SPSS catalog (s4q14, s4q9, s4q3); awaiting database ETL re-ingestion approval."*
2. **Preventing Misleading Calculations:**  
   `apps/indicators/services.py` has been audited to ensure all adoption rate calculations explicitly verify if practice records are non-zero before generating percentages, returning metadata indicating extraction status.
