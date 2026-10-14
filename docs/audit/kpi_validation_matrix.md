# KPI Validation Matrix & Statistical Evaluation

**Platform:** AgriLens — Agricultural Intelligence & Decision-Support Platform for Rwanda  
**Audit Milestone:** Milestone 2  
**Purpose:** Formal statistical audit of analytical indicators against NISR survey design  

---

## 1. Indicator Validation Matrix

| Indicator | Formal Formula | Source Fields (SAS 2024 / 2025) | Units | Weighting Method | Validation Result | Limitations & Methodological Caveats |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Weighted Average Yield** | $\hat{Y} = \frac{\sum (W_i \times \text{Prod}_i)}{\sum (W_i \times \text{Area}_i)}$ | `total_production_kg` (`s2q21`), `plot_area_ha` (`s2q2_ha` / `s2q2`), `sampling_weight` (`plot_weight`) | Kilograms per Hectare ($\text{kg/ha}$) | Survey Expansion Weight (`plot_weight`) | **Validated** (Correctly avoids unweighted arithmetic mean; handles zero area safely) | Plot area measured by GPS/tape; excludes unharvested failed plots where area $>0$ and prod $=0$ if filtered out. |
| **2. Total Production Volume** | $\hat{P} = \sum (W_i \times \text{Prod}_i) / 1000$ | `total_production_kg` (`s2q21`), `sampling_weight` (`plot_weight`) | Metric Tons ($\text{MT}$) | Expansion factor ($W_i$) applied | **Validated** | Based on sample extrapolation; does not account for non-agricultural households or urban micro-gardens. |
| **3. Total Cultivated Area** | $\hat{A} = \sum (W_i \times \text{Area}_i)$ | `plot_area_ha` (`s2q2_ha` / `s2q2`), `sampling_weight` (`plot_weight`) | Hectares ($\text{ha}$) | Expansion factor ($W_i$) applied | **Validated** | Plot area reflects parcel crop-share; intercropped plots partition physical area. |
| **4. Improved Seed Adoption Rate** | $\text{Rate} = \frac{\sum \mathbb{I}(\text{Seed}=\text{True})}{N_{\text{plots}}} \times 100$ | `is_improved_seed` (`s2q9`) | Percentage ($\%$) | Unweighted Plot-Incidence (Current) | **Validated with caveat** (Needs area-weighting: $\frac{\sum W \times A \times \mathbb{I}}{\sum W \times A}$) | Currently reports percentage of sampled plot observations, not weighted land area under certified seed. |
| **5. Mineral Fertilizer Adoption Rate** | $\text{Rate} = \frac{\sum \mathbb{I}(\text{Fert}=\text{True})}{N_{\text{plots}}} \times 100$ | `uses_inorganic_fertilizer` (`s3q9`) | Percentage ($\%$) | Unweighted Plot-Incidence (Current) | **Validated with caveat** (Needs area-weighting) | DAP, Urea, NPK usage; does not reflect application dosage ($\text{kg/ha}$). |
| **6. Organic Fertilizer Adoption Rate** | $\text{Rate} = \frac{\sum \mathbb{I}(\text{Org}=\text{True})}{N_{\text{plots}}} \times 100$ | `uses_organic_fertilizer` (`s3q3`) | Percentage ($\%$) | Unweighted Plot-Incidence (Current) | **Validated** | Covers farmyard manure, compost, green manure. |
| **7. Irrigation Adoption Rate** | $\text{Rate} = \frac{\sum \mathbb{I}(\text{Irrig}=\text{True})}{N_{\text{plots}}} \times 100$ | `is_irrigated` (`s4q14` in 2025; `s4q15` in 2024) | Percentage ($\%$) | Plot-level binary indicator | **Identified Defect:** Mapped as False in initial pilot; requires re-mapping from Section 4. | Season A rainfed crops have low irrigation; Season C marshland has high irrigation. Must not conflate seasons. |
| **8. Post-Harvest Loss Rate** | $\text{Rate} = \frac{\sum (W_i \times \text{Loss}_i)}{\sum (W_i \times (\text{Prod}_i + \text{Loss}_i))} \times 100$ | `total_loss_kg` ($\sum \text{s2q45–s2q50}$), `total_production_kg` (`s2q21`) | Percentage ($\%$) | Survey Expansion Weight ($W_i$) | **Validated** | Farmer self-reported loss estimates across harvesting, transport, storage, processing, and sales. |
| **9. Productivity Gap** | $\text{Gap} = \frac{Y_{\text{lagging}} - Y_{\text{benchmark}}}{Y_{\text{benchmark}}} \times 100$ | Benchmark vs. Lagging district weighted yields for selected crop | Percentage ($\%$) | Survey weighted at district level | **Identified Defect:** District ranking was unweighted and lacked minimum sample threshold ($N \ge 5$). | Descriptive comparison between top district and bottom district; does not imply causal agronomic factors. |
| **10. Year-over-Year (YoY) Growth** | $\text{Growth} = \frac{\hat{Y}_{2025} - \hat{Y}_{2024}}{\hat{Y}_{2024}} \times 100$ | Harmonized crop yield across SAS 2024A and SAS 2025A | Percentage ($\%$) | Weighted population yields | **Identified Defect:** Did not filter by `crop_name`; compared aggregate national basket instead of target crop. | Valid only when comparing the same season (Season A vs Season A) with consistent crop classifications. |

---

## 2. Independent Fixture Verification Tests

To verify formula accuracy independently from production database queries, we ran tests using verified manual calculations:

### Test Case 1: Survey Weighting vs. Unweighted Fallacy
- **Plot 1:** Area = $1.0\text{ ha}$, Production = $3,000\text{ kg}$, Weight = $2.0$  
  $\implies \text{Weighted Area} = 2.0$, $\text{Weighted Prod} = 6,000\text{ kg}$
- **Plot 2:** Area = $2.0\text{ ha}$, Production = $4,000\text{ kg}$, Weight = $1.0$  
  $\implies \text{Weighted Area} = 2.0$, $\text{Weighted Prod} = 4,000\text{ kg}$
- **Unweighted Mean of Plot Yields:** $\frac{3,000 + 2,000}{2} = 2,500\text{ kg/ha}$.
- **Unweighted Aggregate Yield:** $\frac{3,000 + 4,000}{1.0 + 2.0} = \frac{7,000}{3.0} = 2,333.33\text{ kg/ha}$.
- **Authoritative Weighted Yield:** $\frac{6,000 + 4,000}{2.0 + 2.0} = \frac{10,000}{4.0} = \mathbf{2,500.00\text{ kg/ha}}$.
- **Service Output:** `2500.00 kg/ha` (**Matches independent calculation exactly**).

### Test Case 2: Zero Area & Zero Denominator Protection
- **Fixture:** Query executed against an empty season filter with zero plots.
- **Expected:** Safe return with zeroes across all fields, no `ZeroDivisionError` or unhandled exceptions.
- **Service Output:** `'total_plots': 0, 'weighted_yield_kg_per_ha': 0.0, 'total_production_mt': 0.0` (**Verified**).

### Test Case 3: Post-Harvest Loss Rate Formula
- **Fixture:** Production = $10,000\text{ kg}$, Harvest loss = $500\text{ kg}$, Storage loss = $500\text{ kg}$ ($\text{Total loss} = 1,000\text{ kg}$).
- **Formula:** $\frac{1,000}{10,000 + 1,000} \times 100\% = \frac{1,000}{11,000} \times 100\% = \mathbf{9.09\%}$.
- **Service Output:** `9.09%` (**Verified**).
