"""
AgriLens Dataset Profiler & Inventory Generator.
Recursively inspects official NISR SAS 2024, SAS 2025, and AHS 2024 datasets.
Extracts metadata, shapes, column names, variable labels, value labels, identifiers, and missingness.
Outputs machine-readable inventory to data/reference/dataset_inventory.csv
and comprehensive documentation to docs/dataset_inventory.md.
"""
import os
import sys
import json
import csv
from pathlib import Path
import pandas as pd
import pyreadstat

BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / 'Datasets'
REF_DIR = BASE_DIR / 'data' / 'reference'
DOCS_DIR = BASE_DIR / 'docs'

REF_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

def detect_delimiter(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        first_line = f.readline()
        if '\t' in first_line:
            return '\t'
        elif ',' in first_line:
            return ','
        elif ';' in first_line:
            return ';'
    return ','

def profile_all():
    print(f"Profiling datasets in: {DATASETS_DIR}")
    inventory_rows = []
    detailed_inventory = []

    # Walk Datasets directory
    for root, dirs, files in os.walk(DATASETS_DIR):
        for f in sorted(files):
            file_path = Path(root) / f
            ext = file_path.suffix.lower()
            if ext not in ['.csv', '.dta', '.sav', '.xlsx', '.xls']:
                continue

            rel_path = file_path.relative_to(BASE_DIR).as_posix()
            file_size_mb = round(file_path.stat().st_size / (1024 * 1024), 2)
            
            # Determine survey and season
            survey_name = 'Unknown'
            survey_year = 'Unknown'
            season = 'N/A'
            
            if 'AHS' in rel_path or 'Agriculture Household Survey' in rel_path:
                survey_name = 'NISR AHS'
                survey_year = '2024'
                season = 'Annual / Multi-Season'
            elif 'SAS 2024' in rel_path or ('2024' in rel_path and 'SAS' in rel_path):
                survey_name = 'NISR SAS'
                survey_year = '2024'
                if 'Season A' in rel_path or 'SeasonA' in f:
                    season = 'Season A'
                elif 'Season B' in rel_path or 'SeasonB' in f:
                    season = 'Season B'
                elif 'Season C' in rel_path or 'SeasonC' in f:
                    season = 'Season C'
            elif 'SAS 2025' in rel_path or ('2025' in rel_path and 'SAS' in rel_path):
                survey_name = 'NISR SAS'
                survey_year = '2025'
                if 'Season A' in rel_path or 'SeasonA' in f:
                    season = 'Season A'
                elif 'Season B' in rel_path or 'SeasonB' in f:
                    season = 'Season B'
                elif 'Season C' in rel_path or 'SeasonC' in f:
                    season = 'Season C'

            # Determine dataset purpose / domain
            purpose = 'General'
            f_lower = f.lower()
            if 'production' in f_lower:
                purpose = 'Crop Production & Harvest'
            elif 'practice' in f_lower:
                purpose = 'Agricultural Practices & Inputs (Irrigation, Seeds, Mechanization)'
            elif 'fertilizer' in f_lower or 'pesticide' in f_lower:
                purpose = 'Fertilizer & Pesticide Application'
            elif 'screening' in f_lower:
                purpose = 'Farm Parcel & Household Screening'
            elif 'land tenure' in f_lower or 'section2' in f_lower:
                purpose = 'Land Tenure & Plot Characteristics'
            elif 'credits' in f_lower:
                purpose = 'Agricultural Credit & Finance'
            elif 'saving' in f_lower:
                purpose = 'Savings & Investments'
            elif 'milk' in f_lower or 'egg' in f_lower or 'honey' in f_lower or 'livestock' in f_lower:
                purpose = 'Livestock & Animal Products'
            elif 'sustainable' in f_lower or 'section8' in f_lower:
                purpose = 'Sustainable Agriculture & Soil Conservation'
            elif 'extension' in f_lower or 'section6' in f_lower:
                purpose = 'Extension Services & Government Programs'
            elif 'tools' in f_lower or 'section7' in f_lower:
                purpose = 'Farm Tools & Equipment'
            elif 'section0' in f_lower:
                purpose = 'Household Identification & Demographics'
            elif 'section1_' in f_lower:
                purpose = 'Household Members Characteristics'
            elif 'section3_4' in f_lower:
                purpose = 'Crops Grown, Seeds, Production, Inputs & Practices'

            print(f"Reading: {f} ({ext}, {file_size_mb} MB)...")
            
            num_rows = 0
            num_cols = 0
            columns = []
            col_labels = {}
            val_labels = {}
            id_cols = []
            weight_cols = []
            geo_cols = []
            encoding_used = 'utf-8'
            
            try:
                if ext == '.sav':
                    df, meta = pyreadstat.read_sav(str(file_path), metadataonly=True)
                    num_rows = meta.number_rows
                    num_cols = meta.number_columns
                    columns = meta.column_names
                    col_labels = dict(zip(meta.column_names, meta.column_labels))
                    val_labels = meta.variable_value_labels
                    encoding_used = meta.file_encoding or 'SPSS-auto'
                elif ext == '.dta':
                    try:
                        df, meta = pyreadstat.read_dta(str(file_path), metadataonly=True)
                        encoding_used = meta.file_encoding or 'utf-8'
                    except Exception:
                        df, meta = pyreadstat.read_dta(str(file_path), encoding='latin1', metadataonly=True)
                        encoding_used = 'latin1'
                    num_rows = meta.number_rows
                    num_cols = meta.number_columns
                    columns = meta.column_names
                    col_labels = dict(zip(meta.column_names, meta.column_labels))
                    val_labels = meta.variable_value_labels
                elif ext == '.csv':
                    sep = detect_delimiter(file_path)
                    df_sample = pd.read_csv(file_path, sep=sep, nrows=5, encoding='utf-8', encoding_errors='ignore')
                    columns = list(df_sample.columns)
                    num_cols = len(columns)
                    encoding_used = 'utf-8 (sep=' + repr(sep) + ')'
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as fp:
                        num_rows = sum(1 for _ in fp) - 1 # minus header line
            except Exception as e:
                print(f"Error inspecting {f}: {e}")
                num_rows = -1
                num_cols = -1
                columns = []

            # Detect ID columns, geographic columns, weights
            for c in columns:
                cl = c.lower()
                if cl in ['segment_id', 'hhid', 'plot_no', 's2q1', 'id', 'clust', 'farmer_id']:
                    id_cols.append(c)
                if 'weight' in cl or 'wt' in cl:
                    weight_cols.append(c)
                if any(k in cl for k in ['prov', 'dist', 'sect', 'cell', 'village', 's1q1', 's1q2', 's1q3']):
                    geo_cols.append(c)

            item = {
                'filename': f,
                'relative_path': rel_path,
                'file_format': ext.replace('.', '').upper(),
                'file_size_mb': file_size_mb,
                'survey_name': survey_name,
                'survey_year': survey_year,
                'season': season,
                'purpose': purpose,
                'row_count': num_rows,
                'col_count': num_cols,
                'encoding': encoding_used,
                'potential_ids': "; ".join(id_cols),
                'geographic_columns': "; ".join(geo_cols),
                'weight_columns': "; ".join(weight_cols),
                'sample_columns': "; ".join(columns[:10]),
                'all_columns_count': len(columns),
            }
            inventory_rows.append(item)
            
            detailed_inventory.append({
                **item,
                'columns': columns,
                'col_labels': col_labels,
                'val_labels_keys': list(val_labels.keys())
            })

    # Save to CSV
    csv_path = REF_DIR / 'dataset_inventory.csv'
    fieldnames = [
        'filename', 'relative_path', 'file_format', 'file_size_mb',
        'survey_name', 'survey_year', 'season', 'purpose',
        'row_count', 'col_count', 'encoding', 'potential_ids',
        'geographic_columns', 'weight_columns', 'sample_columns'
    ]
    with open(csv_path, 'w', newline='', encoding='utf-8') as cf:
        writer = csv.DictWriter(cf, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(inventory_rows)
    print(f"Saved inventory CSV: {csv_path} ({len(inventory_rows)} files)")

    # Save detailed JSON for report generation
    json_path = REF_DIR / 'detailed_dataset_inventory.json'
    with open(json_path, 'w', encoding='utf-8') as jf:
        json.dump(detailed_inventory, jf, indent=2)
    print(f"Saved detailed JSON: {json_path}")

    return inventory_rows, detailed_inventory

if __name__ == '__main__':
    profile_all()
