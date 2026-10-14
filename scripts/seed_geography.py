"""
Authoritative Seeder for AgriLens:
- 5 Provinces (with official NISR numeric codes: 1=Kigali, 2=South, 3=West, 4=North, 5=East)
- 30 Districts (with official NISR 2-digit codes: 11-57)
- 416 Sectors (from authoritative rwanda_hierarchy.json)
- Agricultural Seasons (2024 A/B/C, 2025 A/B/C, 2026 A)
- Crop Categories & Priority Crops
- Data Sources for strict provenance tracking
"""
import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.geography.models import Province, District, Sector
from apps.agriculture.models import AgriculturalSeason, CropCategory, Crop
from apps.data_management.models import DataSource

BASE_DIR = Path(__file__).resolve().parent.parent

# Official NISR geographic codes
PROVINCE_MAPPING = {
    "1": ("City of Kigali", [
        ("11", "Nyarugenge"),
        ("12", "Gasabo"),
        ("13", "Kicukiro"),
    ]),
    "2": ("Southern Province", [
        ("21", "Nyanza"),
        ("22", "Gisagara"),
        ("23", "Nyaruguru"),
        ("24", "Huye"),
        ("25", "Nyamagabe"),
        ("26", "Ruhango"),
        ("27", "Muhanga"),
        ("28", "Kamonyi"),
    ]),
    "3": ("Western Province", [
        ("31", "Karongi"),
        ("32", "Rutsiro"),
        ("33", "Rubavu"),
        ("34", "Nyabihu"),
        ("35", "Ngororero"),
        ("36", "Rusizi"),
        ("37", "Nyamasheke"),
    ]),
    "4": ("Northern Province", [
        ("41", "Rulindo"),
        ("42", "Gakenke"),
        ("43", "Musanze"),
        ("44", "Burera"),
        ("45", "Gicumbi"),
    ]),
    "5": ("Eastern Province", [
        ("51", "Rwamagana"),
        ("52", "Nyagatare"),
        ("53", "Gatsibo"),
        ("54", "Kayonza"),
        ("55", "Kirehe"),
        ("56", "Ngoma"),
        ("57", "Bugesera"),
    ]),
}

def seed_geography():
    print("Seeding official Rwanda administrative hierarchy...")
    district_obj_map = {}
    
    for prov_code, (prov_name, districts) in PROVINCE_MAPPING.items():
        prov, _ = Province.objects.update_or_create(
            name=prov_name,
            defaults={'code': prov_code}
        )
        for dist_code, dist_name in districts:
            dist, _ = District.objects.update_or_create(
                province=prov,
                name=dist_name,
                defaults={'code': dist_code}
            )
            district_obj_map[dist_name.lower()] = dist
            district_obj_map[dist_code] = dist

    # Load 416 Sectors from hierarchy JSON (Province -> District -> Sector)
    hierarchy_file = BASE_DIR / 'static' / 'data' / 'rwanda_hierarchy.json'
    sector_objs = []
    if hierarchy_file.exists():
        with open(hierarchy_file, 'r', encoding='utf-8') as f:
            hierarchy = json.load(f)
            
        for prov_key, dists_dict in hierarchy.items():
            for dist_name, sectors_dict in dists_dict.items():
                dist = district_obj_map.get(dist_name.lower())
                if not dist:
                    continue
                for s_idx, sector_name in enumerate(sectors_dict.keys(), start=1):
                    sec_code = f"{dist.code}{s_idx:02d}"
                    sector_objs.append(Sector(
                        district=dist,
                        name=sector_name,
                        code=sec_code
                    ))
        
        Sector.objects.bulk_create(sector_objs, ignore_conflicts=True)
                
    print(f"Geography seeded: 5 Provinces, 30 Districts, {Sector.objects.count()} Sectors.")

def seed_agriculture():
    print("Seeding seasons, categories, and priority crops...")
    # Seasons
    seasons = [
        (2024, 'A', '2023-09-01', '2024-02-28'),
        (2024, 'B', '2024-03-01', '2024-06-30'),
        (2024, 'C', '2024-07-01', '2024-09-30'),
        (2025, 'A', '2024-09-01', '2025-02-28'),
        (2025, 'B', '2025-03-01', '2025-06-30'),
        (2025, 'C', '2025-07-01', '2025-09-30'),
        (2026, 'A', '2025-09-01', '2026-02-28'),
    ]
    for year, code, s_date, e_date in seasons:
        AgriculturalSeason.objects.get_or_create(
            year=year,
            season=code,
            defaults={'start_date': s_date, 'end_date': e_date}
        )

    # Categories
    categories = {
        'Cereals': 'Grain crops including Maize, Rice, Wheat, Sorghum',
        'Legumes': 'Protein rich crops including Beans, Soya, Peas',
        'Tubers': 'Root and tuber crops including Irish Potato, Sweet Potato, Cassava',
        'Cash Crops': 'Export and commercial crops including Coffee, Tea, Pyrethrum',
        'Horticulture': 'Fruits, Vegetables and Floriculture',
        'Bananas': 'Cooking, Beer, and Dessert Bananas',
    }
    cat_objs = {}
    for cat_name, desc in categories.items():
        obj, _ = CropCategory.objects.get_or_create(name=cat_name, defaults={'description': desc})
        cat_objs[cat_name] = obj

    # Priority Crops
    crops = [
        ('Maize', 'Cereals', 'Ikigori', 'Zea mays', True),
        ('Marshland Rice', 'Cereals', 'Umuceri', 'Oryza sativa', True),
        ('Wheat', 'Cereals', 'Ingano', 'Triticum', False),
        ('Sorghum', 'Cereals', 'Amasaka', 'Sorghum bicolor', False),
        ('Climbing Beans', 'Legumes', 'Ibishyimbo', 'Phaseolus vulgaris', True),
        ('Bush Beans', 'Legumes', 'Ibishyimbo bigufi', 'Phaseolus vulgaris', True),
        ('Soyabean', 'Legumes', 'Soya', 'Glycine max', True),
        ('Irish Potato', 'Tubers', 'Ibirayi', 'Solanum tuberosum', True),
        ('Cassava', 'Tubers', 'Imyumbati', 'Manihot esculenta', True),
        ('Sweet Potato', 'Tubers', 'Ibijumba', 'Ipomoea batatas', False),
        ('Cooking Banana', 'Bananas', 'Ibitoki byo guteka', 'Musa', True),
        ('Coffee', 'Cash Crops', 'Ikawa', 'Coffea arabica', True),
        ('Tea', 'Cash Crops', 'Icyayi', 'Camellia sinensis', True),
    ]
    for name, cat_name, kiny, sci, priority in crops:
        Crop.objects.get_or_create(
            name=name,
            defaults={
                'category': cat_objs[cat_name],
                'kinyarwanda_name': kiny,
                'scientific_name': sci,
                'is_priority_crop': priority,
            }
        )
    print("Agriculture domain seeded successfully.")

def seed_data_sources():
    print("Seeding official data sources...")
    sources = [
        (DataSource.SourceType.NISR_SAS_2024, 'NISR Seasonal Agricultural Survey 2024', 'Official survey covering Seasons 2024 A, B, C', True),
        (DataSource.SourceType.NISR_SAS_2025, 'NISR Seasonal Agricultural Survey 2025', 'Official survey covering Seasons 2025 A, B, C', True),
        (DataSource.SourceType.NISR_AHS_2024, 'NISR Agriculture Household Survey 2024', 'Official household-level agricultural microdata 2024', True),
        (DataSource.SourceType.MANUAL_ENTRY, 'Authorized Manual Agricultural Entries', 'Manual submissions vetted through review lifecycle', False),
    ]
    for st, name, desc, is_off in sources:
        DataSource.objects.get_or_create(
            source_type=st,
            defaults={'name': name, 'description': desc, 'is_official_survey': is_off}
        )
    print("Data sources seeded successfully.")

def run():
    seed_geography()
    seed_agriculture()
    seed_data_sources()

if __name__ == '__main__':
    run()
