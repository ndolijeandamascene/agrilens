"""
Generate docs/dataset_inventory.md from data/reference/detailed_dataset_inventory.json
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
JSON_PATH = BASE_DIR / 'data' / 'reference' / 'detailed_dataset_inventory.json'
DOC_PATH = BASE_DIR / 'docs' / 'dataset_inventory.md'

with open(JSON_PATH, 'r', encoding='utf-8') as f:
    items = json.load(f)

# Group items by survey and season
ahs_items = [it for it in items if it['survey_name'] == 'NISR AHS']
sas24_items = [it for it in items if it['survey_name'] == 'NISR SAS' and it['survey_year'] == '2024']
sas25_items = [it for it in items if it['survey_name'] == 'NISR SAS' and it['survey_year'] == '2025']

lines = []
lines.append("# AgriLens Official Dataset Inventory")
lines.append("")
lines.append("> **NISR 2026 Big Data Hackathon – Track 1: Agricultural Productivity**")
lines.append("> Verified catalog and structural profile of official NISR microdata.")
lines.append("")
lines.append(f"**Total Data Files Profiled:** {len(items)} files across AHS 2024, SAS 2024, and SAS 2025.")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 1. Executive Summary of Discovered Datasets")
lines.append("")
lines.append("| Survey Name | Period / Seasons Covered | Formats Available | Primary File Count | Total Disk Footprint | Key Observational Unit |")
lines.append("| :--- | :--- | :--- | :---: | :---: | :--- |")
lines.append("| **NISR AHS 2024** | 2024 Agricultural Year (Multi-Season) | Stata (`.dta`) | 14 files | ~170 MB | Household (`hhid`), Member (`pid`), Plot (`s2q1`) |")
lines.append("| **NISR SAS 2024** | Season A, Season B, Season C | CSV (tab-sep), Stata, SPSS | 36 files (12 sets) | ~340 MB | Segment (`Segment_ID`), Plot (`s2q1`), Crop |")
lines.append("| **NISR SAS 2025** | Season A, Season B, Season C | CSV (tab-sep), Stata, SPSS | 36 files (12 sets) | ~1.15 GB | Segment (`Segment_ID`), Plot (`s2q1`), Crop |")
lines.append("")
lines.append("---")
lines.append("")

def render_section(title, file_list):
    res = []
    res.append(f"## {title}")
    res.append("")
    res.append("| Filename | Season | Module Purpose | Rows | Cols | Size (MB) | Formats | Key ID Columns | Geographic Keys | Weights |")
    res.append("| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- | :--- |")
    
    # deduplicate by base name (without extension) to make a readable matrix
    grouped = {}
    for it in file_list:
        base = Path(it['filename']).stem
        if base not in grouped:
            grouped[base] = []
        grouped[base].append(it)
        
    for base, group in grouped.items():
        first = group[0]
        fmts = "/".join(sorted(set(g['file_format'] for g in group)))
        total_size = round(sum(g['file_size_mb'] for g in group), 2)
        rows_str = f"{first['row_count']:,}" if first['row_count'] >= 0 else "N/A"
        cols_str = str(first['col_count'])
        ids = first['potential_ids'] or "None detected"
        geo = first['geographic_columns'] or "None"
        wt = first['weight_columns'] or "Unweighted"
        
        res.append(f"| `{first['filename']}` | {first['season']} | {first['purpose']} | {rows_str} | {cols_str} | {total_size} | {fmts} | `{ids}` | `{geo}` | `{wt}` |")
        
    res.append("")
    return res

lines.extend(render_section("2. Agriculture Household Survey (AHS) 2024 Datasets", ahs_items))
lines.extend(render_section("3. Seasonal Agricultural Survey (SAS) 2024 Datasets", sas24_items))
lines.extend(render_section("4. Seasonal Agricultural Survey (SAS) 2025 Datasets", sas25_items))

lines.append("---")
lines.append("")
lines.append("## 5. Critical Observations & Structural Peculiarities")
lines.append("")
lines.append("1. **Tri-Format Redundancy in SAS:**")
lines.append("   Every SAS module in 2024 and 2025 exists in three parallel formats: `.csv`, `.dta`, and `.sav`.")
lines.append("   - The `.csv` files are actually **Tab-Delimited (`\\t`)** rather than comma-delimited.")
lines.append("   - The `.sav` (SPSS) and `.dta` (Stata) files contain authoritative variable labels and value-label mappings (e.g. `s1q1`: 1=Kigali, 2=South; `s1q2`: 11=Nyarugenge, 12=Gasabo, etc.).")
lines.append("   - **Recommendation:** Use `.sav` / `.dta` for automated dictionary extraction, and `.csv` or `.dta` for high-throughput batch database ingestion.")
lines.append("")
lines.append("2. **SAS Season C 2024 Naming Anomaly:**")
lines.append("   In `Datasets/SAS 2024 catalog and data dictionary/Season C/`, the CSV file for fertilizer is named `Rwa_raw_fertilizer_pesticideB2024.csv`, whereas the companion Stata/SPSS files are named `Rwa_raw_fertilizer_pesticideC2024.dta` and `.sav`.")
lines.append("   This confirms that file naming alone cannot be relied upon without cross-referencing internal metadata.")
lines.append("")
lines.append("3. **Stata Character Encodings in AHS 2024:**")
lines.append("   `AHS2024_Section1_HOUSEHOLD MEMBERS CHARACTERISTICS.dta` and `AHS2024_Section6_EXTENSION SERVICES...dta` require `latin1` / `WINDOWS-1252` encoding rather than strict `utf-8` due to special accented French characters in interview text.")
lines.append("")
lines.append("4. **Observational Granularity Differences:**")
lines.append("   - **SAS:** Sample unit is a geographic segment (`Segment_ID`) containing sampled parcels/plots (`s2q1`), with crop-level production records within plots.")
lines.append("   - **AHS:** Sample unit is an agricultural household (`hhid`), with household members (`pid`), land parcels (`s2q1`), and crops grown across seasons.")
lines.append("   - **Crucial Rule:** Never join SAS and AHS records directly into a single flat observation. They represent different sampling frames and must remain partitioned with explicit provenance.")
lines.append("")

with open(DOC_PATH, 'w', encoding='utf-8') as f:
    f.write("\n".join(lines))

print(f"Generated inventory documentation: {DOC_PATH}")
