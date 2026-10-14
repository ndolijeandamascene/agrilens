# AgriLens Official Data Dictionary & Variable Mapping

> **NISR 2026 Big Data Hackathon – Track 1: Agricultural Productivity**
> Authoritative mapping of official NISR survey questionnaire codes to AgriLens domain models.

**Total Source Variables Formally Mapped:** 923

## 1. Domain Mapping Overview

| Target AgriLens Model / Area | Source Variables Mapped | Transformation Type | Description |
| :--- | :--- | :--- | :--- |
| **Geographic Boundary** | `s1q1` (Province), `s1q2` (District), `s1q3` (Stratum) | Lookup mapping | Official NISR 2-digit integer codes (11 to 57) |
| **Sampling & Farm Structure** | `Segment_ID`, `s1q4`, `s1q6`, `s1q7`, `s2q1` | Direct relational key | Plot reference within segment and farmer type |
| **Crop Production & Harvest** | `s2q2`, `s2q4`, `s2q19_3`, `s2q20_2`, `s2q21` | Unit conversion & aggregation | Yield denominator (ha) and numerator (kg) |
| **Agricultural Inputs** | `s2q9`, `s2q17`, `s3q3`, `s3q9`, `s3q18` | Boolean & quantity parsing | Certified seed, inorganic & organic fertilizer, pesticides |
| **Practices & Climate** | `s4q1` (Erosion), `s4q3` (Anti-erosion), `s4q9` (Mechanization), `s4q14` (Irrigation) | Categorical & Boolean | Terracing, tractors, surface/drip irrigation |
| **Post-Harvest Losses** | `s2q41` to `s2q50` | Stage breakdown (kg) | Harvest, transport, storage, processing, and sales losses |
| **Markets & Commercialization** | `s2q26` (Sold kg), `s2q28` (Price RWF), `s2q36` (Stored kg) | Value & quantity metrics | Market sales share and observed farmgate price |

---

## 2. Core Variable Mapping Matrix

| Survey | Module | Source Code | Official Question Label | AgriLens Target Field | Status | Categories / Mappings |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| SAS 2025 | Production | `Segment_ID` | SEGMENT ID/LSF ID | `Segment_ID` | `verified` |  |
| SAS 2025 | Production | `s1q1` | 1.1 Province | `province_code` | `verified` | 1.0:Kigali; 2.0:South; 3.0:West; 4.0:North; 5.0:Ea |
| SAS 2025 | Production | `s1q2` | 1.2 District | `district_code` | `verified` | 11.0:Nyarugenege; 12.0:Gasabo; 13.0:Kicukiro; 21.0 |
| SAS 2025 | Production | `s1q3` | 1.3 Stratum | `stratum` | `verified` | 10.0:10 Intensive cropland on hillsides; 20.0:20 I |
| SAS 2025 | Production | `s1q6` | 1.6 Farmer ID/LSF ID | `farmer_identifier` | `verified` |  |
| SAS 2025 | Production | `s1q7` | 1.7 Farmer/LSF type | `farmer_type` | `verified` | 1.0:Small scale farmer as individual; 2.0:Small Sc |
| SAS 2025 | Production | `s1q8` | 1.8 Gender | `farmer_gender` | `verified` | 1.0:Male; 2.0:Female |
| SAS 2025 | Production | `s1q9` | 1.9 Age | `farmer_age` | `verified` |  |
| SAS 2025 | Production | `s2q1` | Q2.1. Plot number | `plot_number` | `verified` |  |
| SAS 2025 | Production | `s2q2` | 2.2 Plot area(sqm) | `plot_area_sqm` | `verified` |  |
| SAS 2025 | Production | `s2q4` | 2.4 Crop name | `crop_code / crop_name` | `verified` | 101.0:Maize; 102.0:Paddy rice; 103.0:Sorghum; 104. |
| SAS 2025 | Production | `CropCategory` | 2.4 Crop name | `crop_category` | `verified` | 1.0:Maize; 2.0:Sorghum; 3.0:Paddy rice; 4.0:Wheat; |
| SAS 2025 | Production | `s2q9` | 2.9 Did you use improved seed for this crop in any of your p... | `is_improved_seed` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Production | `s2q19_3` | 2.19 Quantity already harvested (in Kg) | `harvested_quantity_kg` | `verified` |  |
| SAS 2025 | Production | `s2q20_2` | 2.20 Remaining quantity to be harvested(in Kg) | `remaining_harvest_kg` | `verified` |  |
| SAS 2025 | Production | `s2q21` | 2.21 Total quantity of harvest for this season (in Kg) | `total_production_kg` | `verified` |  |
| SAS 2025 | Production | `s2q25` | 2.24 On the total production of this crop what was the quant... | `transformed_quantity_kg` | `verified` |  |
| SAS 2025 | Production | `s2q26` | 2.25 On the total production of this crop what is the quanti... | `sold_quantity_kg` | `verified` |  |
| SAS 2025 | Production | `s2q28` | 2.28. Market price | `market_unit_price_rwf` | `verified` |  |
| SAS 2025 | Production | `s2q29` | 2.29. Qty of production used as hh consumption | `hh_consumption_kg` | `verified` |  |
| SAS 2025 | Production | `s2q36` | 2.36. Qty of production to be stored for future uses | `stored_quantity_kg` | `verified` |  |
| SAS 2025 | Production | `s2q37` | 2.37. What is the type of storage used | `storage_facility_type` | `verified` | 1.0:Own storage; 2.0:Public storage; 3.0:Storage o |
| SAS 2025 | Production | `s2q41` | 2.40 What was the total quantity stolen ?(kg) | `loss_s2q41_kg` | `verified` |  |
| SAS 2025 | Production | `s2q42` | 2.41 What was the total quantity damaged by insects or pests... | `loss_s2q42_kg` | `verified` |  |
| SAS 2025 | Production | `s2q43` | 2.42 What was the total quantity lost due to birds or other ... | `loss_s2q43_kg` | `verified` |  |
| SAS 2025 | Production | `s2q44` | 2.43 What was the total quantity of Stalks fallen to the gro... | `loss_s2q44_kg` | `verified` |  |
| SAS 2025 | Production | `s2q45` | 2.44 What was the total quantity lost during harvesting?(kg) | `loss_s2q45_kg` | `verified` |  |
| SAS 2025 | Production | `s2q46` | 2.45 What was the total quantity lost in transport of produc... | `loss_s2q46_kg` | `verified` |  |
| SAS 2025 | Production | `s2q47` | 2.46 What was the total quantity lost at storage?(kg) | `loss_s2q47_kg` | `verified` |  |
| SAS 2025 | Production | `s2q48` | 2.47 What was the total quantity lost during processing ?(kg... | `loss_s2q48_kg` | `verified` |  |
| SAS 2025 | Production | `s2q49` | 2.48 What was the total quantity lost during packaging ?(kg) | `loss_s2q49_kg` | `verified` |  |
| SAS 2025 | Production | `s2q50` | 2.49 What was the total quantity lost at sales?(kg) | `loss_s2q50_kg` | `verified` |  |
| SAS 2025 | Production | `s3q1` | 3.1 Did you use organic fertilizer in any of your plots duri... | `uses_organic_fertilizer` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Production | `s3q3` | 3.3 Have you used organic fertilizer in this plot during thi... | `uses_organic_fertilizer` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Production | `s3q7` | 3.7 Did you use inorganic fertilizer in any of your plots du... | `uses_inorganic_fertilizer` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Production | `s3q9` | 3.9 Have you used inorganic fertilizer in this plot during t... | `uses_inorganic_fertilizer` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Production | `s3q18` | 3.18 Did you use pesticide/Fungicide in any of your plots du... | `uses_pesticide` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Production | `s4q1` | 4.1 What is the degree of erosion on this plot? | `erosion_degree` | `verified` | 1.0:Severe (Rill erosion, Gully erosion, Mass move |
| SAS 2025 | Production | `s4q3` | 4.3 Is there any anti-erosion activity on this plot? | `has_anti_erosion_activity` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Production | `s4q8` | 4.8 Did you use any mechanical equipment for agriculture act... | `uses_mechanization` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Production | `s4q9` | 4.9 Did you use any mechanical equipment for agriculture act... | `uses_mechanization` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Production | `s4q13` | 4.13 Practiced irrigation in any of your plots during this a... | `is_irrigated` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Production | `s4q14` | 4.14 Has this plot been irrigated during this agricultural s... | `is_irrigated` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Production | `plot_weight` | plot_weight | `sampling_weight` | `verified` |  |
| SAS 2025 | Agricultural Practice | `Segment_ID` | SEGMENT ID/LSF ID | `Segment_ID` | `verified` |  |
| SAS 2025 | Agricultural Practice | `s2q1` | Q2.1. Plot number | `plot_number` | `verified` |  |
| SAS 2025 | Agricultural Practice | `s1q1` | 1.1 Province | `province_code` | `verified` | 1.0:Kigali; 2.0:South; 3.0:West; 4.0:North; 5.0:Ea |
| SAS 2025 | Agricultural Practice | `s1q2` | 1.2 District | `district_code` | `verified` | 11.0:Nyarugenege; 12.0:Gasabo; 13.0:Kicukiro; 21.0 |
| SAS 2025 | Agricultural Practice | `s1q3` | 1.3 Stratum | `stratum` | `verified` | 10.0:10 Intensive cropland on hillsides; 20.0:20 I |
| SAS 2025 | Agricultural Practice | `s1q6` | 1.6 Farmer ID/LSF ID | `farmer_identifier` | `verified` |  |
| SAS 2025 | Agricultural Practice | `s1q7` | 1.7 Farmer/LSF type | `farmer_type` | `verified` | 1.0:Small scale farmer as individual; 2.0:Small Sc |
| SAS 2025 | Agricultural Practice | `s2q2_ha` | plot area(ha) | `plot_area_ha` | `verified` |  |
| SAS 2025 | Agricultural Practice | `s4q1` | 4.1 What is the degree of erosion on this plot? | `erosion_degree` | `verified` | 1.0:Severe (Rill erosion, Gully erosion, Mass move |
| SAS 2025 | Agricultural Practice | `s4q3` | 4.3 Is there any anti-erosion activity on this plot? | `has_anti_erosion_activity` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Agricultural Practice | `plot_weight` | plot_weight | `sampling_weight` | `verified` |  |
| SAS 2025 | Agricultural Practice | `s4q8` | 4.8 Did you use any mechanical equipment for agriculture act... | `uses_mechanization` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Agricultural Practice | `s4q9` | 4.9 Did you use any mechanical equipment for agriculture act... | `uses_mechanization` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Agricultural Practice | `s4q13` | 4.13 Did you practice irrigation in any of your plots during... | `is_irrigated` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Agricultural Practice | `s4q14` | 4.14 Has this plot been irrigated during this agricultural s... | `is_irrigated` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Agricultural Practice | `s4q15` | 4.15 What is irrigation technique used on this plot? | `irrigation_technique` | `verified` | 1.0:Surface irrigation; 2.0:Flood irrigation (espe |
| SAS 2025 | Agricultural Practice | `s4q16` | 4.16 What is the source of water for irrigation? | `irrigation_water_source` | `verified` |  |
| SAS 2025 | Fertilizer & Pesticide | `Segment_ID` | SEGMENT ID/LSF ID | `Segment_ID` | `verified` |  |
| SAS 2025 | Fertilizer & Pesticide | `s2q1` | Q2.1. Plot number | `plot_number` | `verified` |  |
| SAS 2025 | Fertilizer & Pesticide | `s1q1` | 1.1 Province | `province_code` | `verified` | 1.0:Kigali; 2.0:South; 3.0:West; 4.0:North; 5.0:Ea |
| SAS 2025 | Fertilizer & Pesticide | `s1q2` | 1.2 District | `district_code` | `verified` | 11.0:Nyarugenege; 12.0:Gasabo; 13.0:Kicukiro; 21.0 |
| SAS 2025 | Fertilizer & Pesticide | `s1q3` | 1.3 Stratum | `stratum` | `verified` | 10.0:10 Intensive cropland on hillsides; 20.0:20 I |
| SAS 2025 | Fertilizer & Pesticide | `s1q6` | 1.6 Farmer ID/LSF ID | `farmer_identifier` | `verified` |  |
| SAS 2025 | Fertilizer & Pesticide | `s1q7` | 1.7 Farmer/LSF type | `farmer_type` | `verified` | 1.0:Small scale farmer as individual; 2.0:Small Sc |
| SAS 2025 | Fertilizer & Pesticide | `s2q2` | 2.2 Plot area(sqm) | `plot_area_sqm` | `verified` |  |
| SAS 2025 | Fertilizer & Pesticide | `s3q1` | 3.1 Did you use organic fertilizer in any of your plots duri... | `uses_organic_fertilizer` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Fertilizer & Pesticide | `s3q3` | 3.3 Have you used organic fertilizer in this plot during thi... | `uses_organic_fertilizer` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Fertilizer & Pesticide | `s3q7` | 3.7 Did you use inorganic fertilizer in any of your plots du... | `uses_inorganic_fertilizer` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Fertilizer & Pesticide | `s3q9` | 3.9 Have you used inorganic fertilizer in this plot during t... | `uses_inorganic_fertilizer` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Fertilizer & Pesticide | `s3q18` | 3.18 Did you use pesticide/Fungicide in any of your plots du... | `uses_pesticide` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Fertilizer & Pesticide | `plot_weight` | plot_weight | `sampling_weight` | `verified` |  |
| SAS 2025 | Screening | `Segment_ID` | 1.0.SEGMENT ID/LSF ID | `Segment_ID` | `verified` |  |
| SAS 2025 | Screening | `s1q1` | Q1.1.Names and codes of the province the segment/LSF is loca... | `province_code` | `verified` | 1.0:Kigali; 2.0:South; 3.0:West; 4.0:North; 5.0:Ea |
| SAS 2025 | Screening | `s1q2` | Q1.2.Names and codes of the district the segment/LSF is loca... | `district_code` | `verified` | 11.0:Nyarugenge; 12.0:Gasabo; 13.0:Kicukiro; 21.0: |
| SAS 2025 | Screening | `s1q3` | Q1.3.Names and codes of the stratum | `stratum` | `verified` | 10.0:Agricultural land on hillside; 20.0:Agricultu |
| SAS 2025 | Screening | `s1q8` | Q1.8. Number of grids sampled in the segment | `farmer_gender` | `verified` | 99.0:NA |
| SAS 2025 | Screening | `s2q1` | Q2.1. Plot number | `plot_number` | `verified` |  |
| SAS 2025 | Screening | `s2q2` | Q2.2. Bloc number in case of LSF | `plot_area_sqm` | `verified` |  |
| SAS 2025 | Screening | `s2q4` | Q2.4.Which grids fall in this plot? | `crop_code / crop_name` | `verified` |  |
| SAS 2025 | Screening | `s2q9` | Q2.9.Is there any anti-erosion activity on this plot? | `is_improved_seed` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2025 | Screening | `s3q1` | Q3.1.Crop name | `uses_organic_fertilizer` | `verified` | 101.0:Maize; 102.0:Paddy rice; 103.0:Sorghum; 104. |
| SAS 2025 | Screening | `CropCategory` | Q3.1.Crop name | `crop_category` | `verified` | 1.0:Maize; 2.0:Sorghum; 3.0:Paddy rice; 4.0:Wheat; |
| SAS 2025 | Screening | `s3q7` | Q3.7 What is the expected period for harvesting this crop? | `uses_inorganic_fertilizer` | `verified` | 1.0:Before 01/12; 2.0:Between 01-15/12; 3.0:Betwee |
| SAS 2025 | Screening | `plot_weight` | plot_weight | `sampling_weight` | `verified` |  |
| SAS 2024 | Production | `Segment_ID` | IDQUEST | `Segment_ID` | `verified` |  |
| SAS 2024 | Production | `s1q1` | 1.1 Province | `province_code` | `verified` | 1.0:Kigali; 2.0:South; 3.0:West; 4.0:North; 5.0:Ea |
| SAS 2024 | Production | `s1q2` | 1.2 District name & code | `district_code` | `verified` | 11.0:Nyarugenge; 12.0:Gasabo; 13.0:Kicukiro; 21.0: |
| SAS 2024 | Production | `s1q3` | 1.3 Stratum | `stratum` | `verified` | 0.0:LSF; 10.0:Agricultural land on hillside; 20.0: |
| SAS 2024 | Production | `s1q6` | 1.6 Farmer ID/LSF ID | `farmer_identifier` | `verified` |  |
| SAS 2024 | Production | `s1q7` | 1.7 Farmer/LSF type | `farmer_type` | `verified` | 1.0:Small scale farmer as individual; 2.0:Small Sc |
| SAS 2024 | Production | `s1q8` | 1.8 Gender | `farmer_gender` | `verified` | 1.0:Male; 2.0:Female |
| SAS 2024 | Production | `s1q9` | 1.9 Age | `farmer_age` | `verified` |  |
| SAS 2024 | Production | `s2q1` | 2.1 Plot No | `plot_number` | `verified` |  |
| SAS 2024 | Production | `s2q2` | 2.2 Plot area(sqm) | `plot_area_sqm` | `verified` |  |
| SAS 2024 | Production | `s2q4` | Q.2.4 Crop name | `crop_code / crop_name` | `verified` | 101.0:Maize; 102.0:Paddy rice; 103.0:Sorghum; 104. |
| SAS 2024 | Production | `CropCategory` | Q.2.4 Crop name | `crop_category` | `verified` | 1.0:Maize; 2.0:Sorghum; 3.0:Paddy rice; 4.0:Wheat; |
| SAS 2024 | Production | `s2q9` | Q.2.9 Did you use improved seed for this crop in any of your... | `is_improved_seed` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Production | `s2q19_3` | Q.2.19 Quantity already harvested (in Kg) | `harvested_quantity_kg` | `verified` |  |
| SAS 2024 | Production | `s2q20_2` | Q.2.20 Remaining quantity to be harvested(in Kg) | `remaining_harvest_kg` | `verified` |  |
| SAS 2024 | Production | `s2q21` | Q.2.21 Total quantity of harvest for this season (in Kg) | `total_production_kg` | `verified` |  |
| SAS 2024 | Production | `s2q25` | Q.2.25 Qty of production transformed/to be transformed (Kg) | `transformed_quantity_kg` | `verified` |  |
| SAS 2024 | Production | `s2q26` | Q.2.26.Qty of production that has been sold/to be sold?(Kg) | `sold_quantity_kg` | `verified` |  |
| SAS 2024 | Production | `s2q28` | Q.2.28 What was the selling price per kilogram? (Rwf/Kg) | `market_unit_price_rwf` | `verified` |  |
| SAS 2024 | Production | `s2q29` | Q.2.29 Qty that has been used/to be used by the household (a... | `hh_consumption_kg` | `verified` |  |
| SAS 2024 | Production | `s2q36` | Q.2.36 Qty of production stored/to be stored(Kg) | `stored_quantity_kg` | `verified` |  |
| SAS 2024 | Production | `s2q37` | Q.2.37 What is the storage facility used during this agricul... | `storage_facility_type` | `verified` | 1.0:Own storage; 2.0:Public storage; 3.0:Storage o |
| SAS 2024 | Production | `s2q41` | Q.2.41 Qty of crop stollen at farm level? (kg) | `loss_s2q41_kg` | `verified` |  |
| SAS 2024 | Production | `s2q42` | Q.2.42 Qty of crop damaged by insects or pests at farm level... | `loss_s2q42_kg` | `verified` |  |
| SAS 2024 | Production | `s2q43` | Q.2.43 Qty of crop lost due to birds or other animals? (kg) | `loss_s2q43_kg` | `verified` |  |
| SAS 2024 | Production | `s2q44` | Q.2.44 Qty of crop’s stalks fallen to the ground? (kg) | `loss_s2q44_kg` | `verified` |  |
| SAS 2024 | Production | `s2q45` | Q.2.45 Qty of crop lost during harvesting procedures? (kg) | `loss_s2q45_kg` | `verified` |  |
| SAS 2024 | Production | `s2q46` | Q.2.46 Qty of crop production lost in the transport of produ... | `loss_s2q46_kg` | `verified` |  |
| SAS 2024 | Production | `s2q47` | Q.2.47 Qty of crop production lost during storage procedures... | `loss_s2q47_kg` | `verified` |  |
| SAS 2024 | Production | `s2q48` | Q.2.48 Qty lost during harvest processing? (kg) | `loss_s2q48_kg` | `verified` |  |
| SAS 2024 | Production | `s2q49` | Q.2.49 Qty of harvest lost during packaging? (kg) | `loss_s2q49_kg` | `verified` |  |
| SAS 2024 | Production | `s2q50` | Q.2.50 Qty of harvest lost at sales? (kg) | `loss_s2q50_kg` | `verified` |  |
| SAS 2024 | Production | `s3q1` | 3.1 Did you use organic fertilizer in any of your plots duri... | `uses_organic_fertilizer` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Production | `s3q3` | 3.3 Have you used organic fertilizer in this plot during thi... | `uses_organic_fertilizer` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Production | `s3q7` | 3.7 Did you use inorganic fertilizer in any of your plots du... | `uses_inorganic_fertilizer` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Production | `s3q9` | 3.9 Have you used inorganic fertilizer in this plot during t... | `uses_inorganic_fertilizer` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Production | `s3q18` | 3.18 Did you use pesticide/Fungicide in any of your plots du... | `uses_pesticide` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Production | `s4q1` | 4.1 What is the degree of erosion on this plot? | `erosion_degree` | `verified` | 1.0:Severe (Rill erosion, Gully erosion, Mass move |
| SAS 2024 | Production | `s4q3` | 4.3 Is there any anti-erosion activity on this plot? | `has_anti_erosion_activity` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Production | `s4q8` | 4.8 Did you use any mechanical equipment for agriculture act... | `uses_mechanization` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Production | `s4q9` | 4.9 Did you use any mechanical equipment for agriculture act... | `uses_mechanization` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Production | `s4q14` | 4.14 Did you practice irrigation in any of your plots during... | `is_irrigated` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Production | `s4q15` | 4.15 Has this plot been irrigated during this agricultural s... | `irrigation_technique` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Production | `plot_weight` | plot_weight | `sampling_weight` | `verified` |  |
| SAS 2024 | Agricultural Practice | `Segment_ID` | IDQUEST | `Segment_ID` | `verified` |  |
| SAS 2024 | Agricultural Practice | `s1q1` | 1.1 Province | `province_code` | `verified` | 1.0:Kigali; 2.0:South; 3.0:West; 4.0:North; 5.0:Ea |
| SAS 2024 | Agricultural Practice | `s1q2` | 1.2 District name & code | `district_code` | `verified` | 11.0:Nyarugenge; 12.0:Gasabo; 13.0:Kicukiro; 21.0: |
| SAS 2024 | Agricultural Practice | `s1q3` | 1.3 Stratum | `stratum` | `verified` | 0.0:LSF; 10.0:Agricultural land on hillside; 20.0: |
| SAS 2024 | Agricultural Practice | `s1q6` | 1.6 Farmer ID/LSF ID | `farmer_identifier` | `verified` |  |
| SAS 2024 | Agricultural Practice | `s1q7` | 1.7 Farmer/LSF type | `farmer_type` | `verified` | 1.0:Small scale farmer as individual; 2.0:Small Sc |
| SAS 2024 | Agricultural Practice | `s1q8` | 1.8 Gender | `farmer_gender` | `verified` | 1.0:Male; 2.0:Female |
| SAS 2024 | Agricultural Practice | `s1q9` | 1.9 Age | `farmer_age` | `verified` |  |
| SAS 2024 | Agricultural Practice | `s2q1` | 2.1 Plot No | `plot_number` | `verified` |  |
| SAS 2024 | Agricultural Practice | `s2q2` | 2.2 Plot area(sqm) | `plot_area_sqm` | `verified` |  |
| SAS 2024 | Agricultural Practice | `s2q2_ha` | Unlabeled | `plot_area_ha` | `verified` |  |
| SAS 2024 | Agricultural Practice | `s4q1` | 4.1 What is the degree of erosion on this plot? | `erosion_degree` | `verified` | 1.0:Severe (Rill erosion, Gully erosion, Mass move |
| SAS 2024 | Agricultural Practice | `s4q3` | 4.3 Is there any anti-erosion activity on this plot? | `has_anti_erosion_activity` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Agricultural Practice | `s4q8` | 4.8 Did you use any mechanical equipment for agriculture act... | `uses_mechanization` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Agricultural Practice | `s4q9` | 4.9 Did you use any mechanical equipment for agriculture act... | `uses_mechanization` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Agricultural Practice | `s4q13` | 4.13 Amount spent on hired labor used to prepare land, sowin... | `is_irrigated` | `verified` |  |
| SAS 2024 | Agricultural Practice | `s4q14` | 4.14 Did you practice irrigation in any of your plots during... | `is_irrigated` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Agricultural Practice | `s4q15` | 4.15 Has this plot been irrigated during this agricultural s... | `irrigation_technique` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Agricultural Practice | `s4q16` | 4.16 What is irrigation technique used on this plot? | `irrigation_water_source` | `verified` | 1.0:Surface irrigation; 2.0:Flood irrigation (espe |
| SAS 2024 | Agricultural Practice | `plot_weight` | plot_weight | `sampling_weight` | `verified` |  |
| SAS 2024 | Fertilizer & Pesticide | `Segment_ID` | 1.0 Segment identification | `Segment_ID` | `verified` |  |
| SAS 2024 | Fertilizer & Pesticide | `s1q1` | 1.1 Province | `province_code` | `verified` | 1.0:Kigali; 2.0:South; 3.0:West; 4.0:North; 5.0:Ea |
| SAS 2024 | Fertilizer & Pesticide | `s1q2` | 1.2 District name & code | `district_code` | `verified` | 11.0:Nyarugenge; 12.0:Gasabo; 13.0:Kicukiro; 21.0: |
| SAS 2024 | Fertilizer & Pesticide | `s1q3` | 1.3 Stratum | `stratum` | `verified` | 0.0:LSF; 10.0:Agricultural land on hillside; 20.0: |
| SAS 2024 | Fertilizer & Pesticide | `s1q6` | 1.6 Farmer ID/LSF ID | `farmer_identifier` | `verified` |  |
| SAS 2024 | Fertilizer & Pesticide | `s1q7` | 1.7 Farmer/LSF type | `farmer_type` | `verified` | 1.0:Small scale farmer as individual; 2.0:Small Sc |
| SAS 2024 | Fertilizer & Pesticide | `s1q8` | 1.8 Gender | `farmer_gender` | `verified` | 1.0:Male; 2.0:Female |
| SAS 2024 | Fertilizer & Pesticide | `s1q9` | 1.9 Age | `farmer_age` | `verified` |  |
| SAS 2024 | Fertilizer & Pesticide | `s2q1` | 2.1 Plot No | `plot_number` | `verified` |  |
| SAS 2024 | Fertilizer & Pesticide | `s2q2` | 2.2 Plot area(sqm) | `plot_area_sqm` | `verified` |  |
| SAS 2024 | Fertilizer & Pesticide | `s2q2_ha` | plot area(ha) | `plot_area_ha` | `verified` |  |
| SAS 2024 | Fertilizer & Pesticide | `plot_weight` | plot_weight | `sampling_weight` | `verified` |  |
| SAS 2024 | Fertilizer & Pesticide | `s3q1` | 3.1 Did you use organic fertilizer in any of your plots duri... | `uses_organic_fertilizer` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Fertilizer & Pesticide | `s3q3` | 3.3 Have you used organic fertilizer in this plot during thi... | `uses_organic_fertilizer` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Fertilizer & Pesticide | `s3q7` | 3.7 Did you use inorganic fertilizer in any of your plots du... | `uses_inorganic_fertilizer` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Fertilizer & Pesticide | `s3q9` | 3.9 Have you used inorganic fertilizer in this plot during t... | `uses_inorganic_fertilizer` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Fertilizer & Pesticide | `s3q18` | 3.18 Did you use pesticide/Fungicide in any of your plots du... | `uses_pesticide` | `verified` | 1.0:Yes; 2.0:No |
| SAS 2024 | Screening | `Segment_ID` | 1.0.SEGMENT ID/LSF ID | `Segment_ID` | `verified` |  |
| SAS 2024 | Screening | `s1q1` | Q1.1.Names and codes of the province the segment/LSF is loca... | `province_code` | `verified` | 1.0:Kigali; 2.0:South; 3.0:West; 4.0:North; 5.0:Ea |
| SAS 2024 | Screening | `s1q2` | Q1.2.Names and codes of the district the segment/LSF is loca... | `district_code` | `verified` | 11.0:Nyarugenge; 12.0:Gasabo; 13.0:Kicukiro; 21.0: |
| SAS 2024 | Screening | `s1q3` | Q1.3.Names and codes of the stratum | `stratum` | `verified` | 10.0:Agricultural land on hillside; 20.0:Agricultu |
| SAS 2024 | Screening | `s2q1` | Q2.1. Plot number | `plot_number` | `verified` |  |
| SAS 2024 | Screening | `s2q2` | Q2.2. Bloc number in case of LSF | `plot_area_sqm` | `verified` |  |
| SAS 2024 | Screening | `s2q4` | Q2.4.Which grids fall in this plot? | `crop_code / crop_name` | `verified` |  |
| SAS 2024 | Screening | `s3q1` | Q3.1.Crop name | `uses_organic_fertilizer` | `verified` | 101.0:Maize; 102.0:Paddy rice; 103.0:Sorghum; 104. |
| SAS 2024 | Screening | `s3q7` | Q3.7 What is the expected period for harvesting this crop? | `uses_inorganic_fertilizer` | `verified` | 1.0:Before 01/12; 2.0:Between 01-15/12; 3.0:Betwee |
| SAS 2024 | Screening | `CropCategory` | Q3.1.Crop name | `crop_category` | `verified` | 1.0:Maize; 2.0:Sorghum; 3.0:Paddy rice; 4.0:Wheat; |
| SAS 2024 | Screening | `plot_weight` | plot_weight | `sampling_weight` | `verified` |  |
| AHS 2024 | Demographics & Identification | `hhid` | Household Identification | `household_id` | `verified` |  |
| AHS 2024 | Demographics & Identification | `province` | Province | `province_code` | `verified` | 1:Kigali; 2:South; 3:West; 4:North; 5:East |
| AHS 2024 | Demographics & Identification | `district` | District | `district_code` | `verified` | 11:Nyarugenge; 12:Gasabo; 13:Kicukiro; 21:Nyanza;  |
| AHS 2024 | Demographics & Identification | `weight` | Final Season A weight | `sampling_weight` | `verified` |  |
| AHS 2024 | Land Tenure | `hhid` | Household Identification | `household_id` | `verified` |  |
| AHS 2024 | Land Tenure | `district` | District | `district_code` | `verified` | 11:Nyarugenge; 12:Gasabo; 13:Kicukiro; 21:Nyanza;  |
| AHS 2024 | Land Tenure | `province` | Province | `province_code` | `verified` | 1:Kigali; 2:South; 3:West; 4:North; 5:East |
| AHS 2024 | Land Tenure | `s2q1` | 2.1 Plot No. | `plot_number` | `verified` |  |
| AHS 2024 | Land Tenure | `s2q2` | Area in sqm | `plot_area_sqm` | `verified` |  |
| AHS 2024 | Land Tenure | `s2q4` | 2.4 How did the owners/users get access to this plot? | `crop_code / crop_name` | `verified` | 1:Inherited; 2:Purchase; 3:Gift; 4:Rented in (fixe |
| AHS 2024 | Land Tenure | `s2q9` | 2.9 Household members with the right to bequeath the land. | `is_improved_seed` | `verified` |  |
| AHS 2024 | Land Tenure | `weight` | Final Season A weight | `sampling_weight` | `verified` |  |
| AHS 2024 | Crop Production & Practices | `hhid` | Household Identification | `household_id` | `verified` |  |
| AHS 2024 | Crop Production & Practices | `province` | Province | `province_code` | `verified` | 1:Kigali; 2:South; 3:West; 4:North; 5:East |
| AHS 2024 | Crop Production & Practices | `district` | District | `district_code` | `verified` | 11:Nyarugenge; 12:Gasabo; 13:Kicukiro; 21:Nyanza;  |
| AHS 2024 | Crop Production & Practices | `s2q1` | 2.1 Plot No. | `plot_number` | `verified` |  |
| AHS 2024 | Crop Production & Practices | `s2q2` | area_sqm | `plot_area_sqm` | `verified` |  |
| AHS 2024 | Crop Production & Practices | `weight` | Final Season A weight | `sampling_weight` | `verified` |  |
| AHS 2024 | Sustainable Agriculture | `hhid` | Household Identification | `household_id` | `verified` |  |
| AHS 2024 | Sustainable Agriculture | `province` | Province | `province_code` | `verified` | 1:Kigali; 2:South; 3:West; 4:North; 5:East |
| AHS 2024 | Sustainable Agriculture | `district` | District | `district_code` | `verified` | 11:Nyarugenge; 12:Gasabo; 13:Kicukiro; 21:Nyanza;  |
| AHS 2024 | Sustainable Agriculture | `weight` | Final Season A weight | `sampling_weight` | `verified` |  |
