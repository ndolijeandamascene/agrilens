# AgriLens Official Dataset Inventory

> **NISR 2026 Big Data Hackathon – Track 1: Agricultural Productivity**
> Verified catalog and structural profile of official NISR microdata.

**Total Data Files Profiled:** 86 files across AHS 2024, SAS 2024, and SAS 2025.

---

## 1. Executive Summary of Discovered Datasets

| Survey Name | Period / Seasons Covered | Formats Available | Primary File Count | Total Disk Footprint | Key Observational Unit |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **NISR AHS 2024** | 2024 Agricultural Year (Multi-Season) | Stata (`.dta`) | 14 files | ~170 MB | Household (`hhid`), Member (`pid`), Plot (`s2q1`) |
| **NISR SAS 2024** | Season A, Season B, Season C | CSV (tab-sep), Stata, SPSS | 36 files (12 sets) | ~340 MB | Segment (`Segment_ID`), Plot (`s2q1`), Crop |
| **NISR SAS 2025** | Season A, Season B, Season C | CSV (tab-sep), Stata, SPSS | 36 files (12 sets) | ~1.15 GB | Segment (`Segment_ID`), Plot (`s2q1`), Crop |

---

## 2. Agriculture Household Survey (AHS) 2024 Datasets

| Filename | Season | Module Purpose | Rows | Cols | Size (MB) | Formats | Key ID Columns | Geographic Keys | Weights |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| `AHS2024_Credits.dta` | Annual / Multi-Season | Agricultural Credit & Finance | 5,224 | 12 | 1.53 | DTA | `hhid; clust` | `None` | `Unweighted` |
| `AHS2024_Saving.dta` | Annual / Multi-Season | Savings & Investments | 10,342 | 14 | 0.67 | DTA | `hhid; clust` | `district; province` | `Unweighted` |
| `AHS2024_Section0.dta` | Annual / Multi-Season | Household Identification & Demographics | 3,724 | 9 | 0.11 | DTA | `hhid; clust` | `province; district` | `weight` |
| `AHS2024_Section11_1_CATTLE MILK PRODUCTION AND USE.dta` | Annual / Multi-Season | Crop Production & Harvest | 12,209 | 40 | 2.35 | DTA | `hhid; clust` | `province; district` | `weight` |
| `AHS2024_Section11_2_EGG PRODUCTION.dta` | Annual / Multi-Season | Crop Production & Harvest | 19,077 | 17 | 1.5 | DTA | `hhid; clust` | `province; district` | `weight` |
| `AHS2024_Section11_3_HONEY PRODUCTION.dta` | Annual / Multi-Season | Crop Production & Harvest | 9,387 | 16 | 0.79 | DTA | `hhid; clust` | `province; district` | `weight` |
| `AHS2024_Section1_HOUSEHOLD MEMBERS CHARACTERISTICS.dta` | Annual / Multi-Season | Household Members Characteristics | 16,292 | 142 | 9.01 | DTA | `hhid; clust` | `province; district; s1q1; s1q2; s1q3y; s1q3m; s1q10; s1q11; s1q12; s1q13; s1q14` | `Unweighted` |
| `AHS2024_Section2_LAND TENURE.dta` | Annual / Multi-Season | Land Tenure & Plot Characteristics | 23,266 | 20 | 2.93 | DTA | `hhid; clust; s2q1` | `district; province` | `weight` |
| `AHS2024_Section3_4_CROP GROWN, SEEDS AND PRODUCTION & AGRICULTURAL INPUTS AND PRACTICES.dta` | Annual / Multi-Season | Crop Production & Harvest | 32,616 | 331 | 123.37 | DTA | `hhid; clust; s2q1` | `province; district` | `weight` |
| `AHS2024_Section5_FRUITS PRODUCTION.dta` | Annual / Multi-Season | Crop Production & Harvest | 9,193 | 16 | 0.73 | DTA | `hhid; clust` | `province; district` | `weight` |
| `AHS2024_Section6_EXTENSION SERVICES AND AGRICULTURAL PROGRAMMES.dta` | Annual / Multi-Season | Extension Services & Government Programs | 9,286 | 30 | 1.92 | DTA | `hhid; clust` | `province; district` | `weight` |
| `AHS2024_Section7_AGRICULTURAL TOOLS.dta` | Annual / Multi-Season | Farm Tools & Equipment | 9,981 | 20 | 1.93 | DTA | `hhid; clust` | `province; district` | `weight` |
| `AHS2024_Section8_SUSTAINABLE AGRICULTURE.dta` | Annual / Multi-Season | Sustainable Agriculture & Soil Conservation | 3,724 | 11 | 1.46 | DTA | `hhid; clust` | `province; district` | `weight` |
| `AHS2024_Section9_10_12_LIVESTOCK AND ANIMAL INPUTS EXPENDITURES,.dta` | Annual / Multi-Season | Livestock & Animal Products | 9,947 | 54 | 2.62 | DTA | `hhid; clust` | `province; district` | `weight` |

## 3. Seasonal Agricultural Survey (SAS) 2024 Datasets

| Filename | Season | Module Purpose | Rows | Cols | Size (MB) | Formats | Key ID Columns | Geographic Keys | Weights |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| `Rwa_raw_SeasonA2024_Agricultural_practice.csv` | Season A | Agricultural Practices & Inputs (Irrigation, Seeds, Mechanization) | 17,506 | 58 | 16.59 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3; s1q14; s1q17; s1q17_o` | `plot_weight` |
| `Rwa_raw_SeasonA2024_Production.csv` | Season A | Crop Production & Harvest | 39,330 | 95 | 71.93 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3; s1q14` | `plot_weight` |
| `Rwa_raw_SeasonA2024_Screening.csv` | Season A | Farm Parcel & Household Screening | 54,382 | 45 | 71.55 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3; s1q10; s1q13` | `plot_weight` |
| `Rwa_raw_fertilizer_pesticideA2024.csv` | Season A | Fertilizer & Pesticide Application | 22,105 | 63 | 35.41 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3; s1q14; s1q17; s1q17_o` | `plot_weight` |
| `Rwa_raw_SeasonB2024_Agricultural_practice.csv` | Season B | Agricultural Practices & Inputs (Irrigation, Seeds, Mechanization) | 17,261 | 52 | 15.46 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3; s1q14; s1q17; s1q17_o` | `plot_weight` |
| `Rwa_raw_SeasonB2024_Production.csv` | Season B | Crop Production & Harvest | 35,584 | 97 | 70.12 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3; s1q14; s1q17; s1q17_o` | `plot_weight` |
| `Rwa_raw_SeasonB2024_Screening.csv` | Season B | Farm Parcel & Household Screening | 28,562 | 45 | 37.2 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3; s1q10; s1q13` | `plot_weight` |
| `Rwa_raw_fertilizer_pesticideB2024.csv` | Season B | Fertilizer & Pesticide Application | 19,965 | 63 | 32.51 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3; s1q14; s1q17; s1q17_o` | `plot_weight` |
| `Rwa_raw_SeasonC2024_Agricultural_practice.csv` | Season C | Agricultural Practices & Inputs (Irrigation, Seeds, Mechanization) | 1,632 | 47 | 1.47 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3; s1q14; s1q17; s1q17_o` | `plot_weight` |
| `Rwa_raw_SeasonC2024_Production.csv` | Season C | Crop Production & Harvest | 1,949 | 96 | 3.91 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3; s1q14; s1q17; s1q17_o` | `plot_weight` |
| `Rwa_raw_SeasonC2024_Screening.csv` | Season C | Farm Parcel & Household Screening | 8,195 | 41 | 9.09 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3; s1q13` | `plot_weight` |
| `Rwa_raw_fertilizer_pesticideC2024.dta` | Season C | Fertilizer & Pesticide Application | 2,307 | 60 | 3.26 | DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3; s1q14` | `plot_weight` |

## 4. Seasonal Agricultural Survey (SAS) 2025 Datasets

| Filename | Season | Module Purpose | Rows | Cols | Size (MB) | Formats | Key ID Columns | Geographic Keys | Weights |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| `Rwa_raw_SeasonA2025_Agricultural_practice.csv` | Season A | Agricultural Practices & Inputs (Irrigation, Seeds, Mechanization) | 17,062 | 59 | 101.79 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3` | `plot_weight` |
| `Rwa_raw_SeasonA2025_Production.csv` | Season A | Crop Production & Harvest | 34,369 | 101 | 136.3 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3; s1q14; s1q16` | `plot_weight` |
| `Rwa_raw_SeasonA2025_Screening.csv` | Season A | Farm Parcel & Household Screening | 52,569 | 51 | 104.53 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3` | `plot_weight` |
| `Rwa_raw_fertilizer_pesticideA2025.csv` | Season A | Fertilizer & Pesticide Application | 17,062 | 80 | 47.71 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3; s1q14` | `plot_weight` |
| `Rwa_raw_SeasonB2025_Agricultural_practice.csv` | Season B | Agricultural Practices & Inputs (Irrigation, Seeds, Mechanization) | 17,100 | 55 | 58.25 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3` | `plot_weight` |
| `Rwa_raw_SeasonB2025_Production.csv` | Season B | Crop Production & Harvest | 32,920 | 101 | 142.31 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3; s1q14; s1q16` | `plot_weight` |
| `Rwa_raw_SeasonB2025_Screening.csv` | Season B | Farm Parcel & Household Screening | 50,537 | 54 | 309.1 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3` | `plot_weight` |
| `Rwa_raw_fertilizer_pesticideB2025.csv` | Season B | Fertilizer & Pesticide Application | 17,100 | 93 | 138.33 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3` | `plot_weight` |
| `Rwa_raw_SeasonC2025_Agricultural_practice.csv` | Season C | Agricultural Practices & Inputs (Irrigation, Seeds, Mechanization) | 1,667 | 47 | 2.67 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3` | `Plot_weight` |
| `Rwa_raw_SeasonC2025_Production.csv` | Season C | Crop Production & Harvest | 1,884 | 99 | 7.51 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3; s1q14; s1q16` | `Plot_weight` |
| `Rwa_raw_SeasonC2025_Screening.csv` | Season C | Farm Parcel & Household Screening | 8,412 | 42 | 22.39 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3` | `Plot_weight` |
| `Rwa_raw_fertilizer_pesticideC2025.csv` | Season C | Fertilizer & Pesticide Application | 1,667 | 85 | 10.52 | CSV/DTA/SAV | `Segment_ID; s2q1` | `s1q1; s1q2; s1q3` | `Plot_weight` |

---

## 5. Critical Observations & Structural Peculiarities

1. **Tri-Format Redundancy in SAS:**
   Every SAS module in 2024 and 2025 exists in three parallel formats: `.csv`, `.dta`, and `.sav`.
   - The `.csv` files are actually **Tab-Delimited (`\t`)** rather than comma-delimited.
   - The `.sav` (SPSS) and `.dta` (Stata) files contain authoritative variable labels and value-label mappings (e.g. `s1q1`: 1=Kigali, 2=South; `s1q2`: 11=Nyarugenge, 12=Gasabo, etc.).
   - **Recommendation:** Use `.sav` / `.dta` for automated dictionary extraction, and `.csv` or `.dta` for high-throughput batch database ingestion.

2. **SAS Season C 2024 Naming Anomaly:**
   In `Datasets/SAS 2024 catalog and data dictionary/Season C/`, the CSV file for fertilizer is named `Rwa_raw_fertilizer_pesticideB2024.csv`, whereas the companion Stata/SPSS files are named `Rwa_raw_fertilizer_pesticideC2024.dta` and `.sav`.
   This confirms that file naming alone cannot be relied upon without cross-referencing internal metadata.

3. **Stata Character Encodings in AHS 2024:**
   `AHS2024_Section1_HOUSEHOLD MEMBERS CHARACTERISTICS.dta` and `AHS2024_Section6_EXTENSION SERVICES...dta` require `latin1` / `WINDOWS-1252` encoding rather than strict `utf-8` due to special accented French characters in interview text.

4. **Observational Granularity Differences:**
   - **SAS:** Sample unit is a geographic segment (`Segment_ID`) containing sampled parcels/plots (`s2q1`), with crop-level production records within plots.
   - **AHS:** Sample unit is an agricultural household (`hhid`), with household members (`pid`), land parcels (`s2q1`), and crops grown across seasons.
   - **Crucial Rule:** Never join SAS and AHS records directly into a single flat observation. They represent different sampling frames and must remain partitioned with explicit provenance.

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
