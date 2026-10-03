"""
Seed script for Rwanda Administrative Structure:
- 5 Provinces: City of Kigali, Northern, Southern, Eastern, Western.
- 30 Districts (e.g. Gasabo, Kicukiro, Nyarugenge, Musanze, Huye, Bugesera, Rubavu, etc.).
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.geography.models import Province, District

RWANDA_STRUCTURE = {
    "City of Kigali": ["Gasabo", "Kicukiro", "Nyarugenge"],
    "Northern Province": ["Burera", "Gakenke", "Gicumbi", "Musanze", "Rulindo"],
    "Southern Province": ["Gisagara", "Huye", "Kamonyi", "Muhanga", "Nyamagabe", "Nyanza", "Nyaruguru", "Ruhango"],
    "Eastern Province": ["Bugesera", "Gatsibo", "Kayonza", "Kirehe", "Ngoma", "Nyagatare", "Rwamagana"],
    "Western Province": ["Karongi", "Ngororero", "Nyabihu", "Nyamasheke", "Rubavu", "Rusizi", "Rutsiro"]
}

def seed():
    print("Seeding Rwanda provinces and districts...")
    for prov_name, districts in RWANDA_STRUCTURE.items():
        prov, _ = Province.objects.get_or_create(
            name=prov_name,
            defaults={'code': prov_name[:3].upper()}
        )
        for dist_name in districts:
            District.objects.get_or_create(
                province=prov,
                name=dist_name,
                defaults={'code': dist_name[:3].upper()}
            )
    print("Geography seeded successfully (5 Provinces, 30 Districts).")

if __name__ == '__main__':
    seed()
