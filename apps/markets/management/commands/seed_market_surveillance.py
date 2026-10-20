from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.geography.models import District, Province
from apps.agriculture.models import Crop
from apps.markets.models import (
    MarketLocation,
    MarketCommodity,
    CommodityPrice,
    PriceCollectionAssignment,
    PricePublicNotice,
    PriceAuditLog,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds realistic Rwandan agricultural market hubs, commodity definitions, and surveillance prices."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding market surveillance data...")
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.first()

        # 1. Market Locations across Rwanda
        markets_data = [
            ("Nyabugogo Central Market", "Nyarugenge", "wholesale", True, -1.9366, 30.0444),
            ("Kimironko Modern Market", "Gasabo", "retail", True, -1.9388, 30.1264),
            ("Kicukiro Centre Market", "Kicukiro", "retail", False, -1.9792, 30.1033),
            ("Musanze Modern Market", "Musanze", "wholesale", True, -1.4989, 29.6343),
            ("Mahoko Market", "Rubavu", "assembly", True, -1.6883, 29.3562),
            ("Gisenyi Cross-Border Hub", "Rubavu", "border", True, -1.7011, 29.2561),
            ("Huye Central Market", "Huye", "wholesale", True, -2.5967, 29.7394),
            ("Muhanga Commercial Market", "Muhanga", "retail", True, -2.0833, 29.7500),
            ("Rwamagana Central Market", "Rwamagana", "wholesale", True, -1.9487, 30.4347),
            ("Nyagatare Grain Market", "Nyagatare", "assembly", True, -1.2972, 30.3253),
            ("Kabarondo Trade Post", "Kayonza", "retail", False, -1.9833, 30.5500),
            ("Gicumbi High-Altitude Market", "Gicumbi", "retail", False, -1.6039, 30.1172),
            ("Rusizi Kamembe Market", "Rusizi", "border", True, -2.4839, 28.9078),
            ("Karongi Lakefront Market", "Karongi", "retail", False, -2.0667, 29.3500),
            ("Nyanza Royal Market", "Nyanza", "retail", False, -2.3500, 29.7500),
        ]

        created_markets = {}
        for name, district_name, m_type, is_hub, lat, lng in markets_data:
            district = District.objects.filter(name__iexact=district_name).first()
            if not district:
                continue
            market, _ = MarketLocation.objects.update_or_create(
                name=name,
                defaults={
                    "district": district,
                    "province": district.province,
                    "market_type": m_type,
                    "is_major_hub": is_hub,
                    "latitude": Decimal(str(lat)),
                    "longitude": Decimal(str(lng)),
                    "is_active": True,
                }
            )
            created_markets[name] = market
        self.stdout.write(f"Created/updated {len(created_markets)} market locations.")

        # 2. Market Commodities Catalog
        commodities_data = [
            ("Maize Grain", "Maize", "Cereals", "RWF/kg", 200, 800),
            ("Climbing Beans", "Climbing Beans", "Legumes", "RWF/kg", 280, 950),
            ("Bush Beans", "Bush Beans", "Legumes", "RWF/kg", 250, 900),
            ("Irish Potatoes", "Irish Potato", "Roots & Tubers", "RWF/kg", 180, 700),
            ("Cassava Flour", "Cassava", "Roots & Tubers", "RWF/kg", 200, 750),
            ("Local Milled Rice", "Marshland Rice", "Cereals", "RWF/kg", 650, 1600),
            ("Soybeans", "Soyabean", "Legumes", "RWF/kg", 380, 1100),
            ("Sweet Potatoes", "Sweet Potato", "Roots & Tubers", "RWF/kg", 150, 550),
            ("Wheat Grain", "Wheat", "Cereals", "RWF/kg", 350, 900),
            ("Sorghum Flour", "Sorghum", "Cereals", "RWF/kg", 300, 850),
        ]

        created_commodities = {}
        for comm_name, crop_name, category, unit, min_p, max_p in commodities_data:
            crop = Crop.objects.filter(name__iexact=crop_name).first()
            comm, _ = MarketCommodity.objects.update_or_create(
                name=comm_name,
                defaults={
                    "crop": crop,
                    "category": category,
                    "standard_unit": unit,
                    "min_expected_price": Decimal(str(min_p)),
                    "max_expected_price": Decimal(str(max_p)),
                    "is_active": True,
                }
            )
            created_commodities[comm_name] = comm
        self.stdout.write(f"Created/updated {len(created_commodities)} commodities.")

        # 3. Commodity Prices & Surveillance Lineage
        today = timezone.now().date()
        nyabugogo = created_markets.get("Nyabugogo Central Market")
        kimironko = created_markets.get("Kimironko Modern Market")
        musanze = created_markets.get("Musanze Modern Market")
        mahoko = created_markets.get("Mahoko Market")
        huye = created_markets.get("Huye Central Market")
        rwamagana = created_markets.get("Rwamagana Central Market")
        muhanga = created_markets.get("Muhanga Commercial Market")
        nyagatare = created_markets.get("Nyagatare Grain Market")

        # Key crops
        crop_maize = Crop.objects.filter(name__iexact="Maize").first()
        crop_climbing_beans = Crop.objects.filter(name__iexact="Climbing Beans").first()
        crop_bush_beans = Crop.objects.filter(name__iexact="Bush Beans").first()
        crop_potato = Crop.objects.filter(name__iexact="Irish Potato").first()
        crop_rice = Crop.objects.filter(name__iexact="Marshland Rice").first()
        crop_cassava = Crop.objects.filter(name__iexact="Cassava").first()

        price_specs = [
            # Published prices (Public View)
            (nyabugogo, crop_maize, 440, 410, 370, today, CommodityPrice.Status.PUBLISHED),
            (kimironko, crop_maize, 430, 400, 370, today, CommodityPrice.Status.PUBLISHED),
            (musanze, crop_maize, 400, 370, 340, today, CommodityPrice.Status.PUBLISHED),
            (rwamagana, crop_maize, 390, 360, 330, today, CommodityPrice.Status.PUBLISHED),
            (nyagatare, crop_maize, 380, 350, 320, today, CommodityPrice.Status.PUBLISHED),
            (huye, crop_maize, 420, 390, 360, today, CommodityPrice.Status.PUBLISHED),
            (muhanga, crop_maize, 420, 390, 360, today, CommodityPrice.Status.PUBLISHED),
            
            (nyabugogo, crop_climbing_beans, 440, 400, 360, today, CommodityPrice.Status.PUBLISHED),
            (kimironko, crop_climbing_beans, 460, 420, 380, today, CommodityPrice.Status.PUBLISHED),
            (musanze, crop_climbing_beans, 410, 370, 340, today, CommodityPrice.Status.PUBLISHED),
            (huye, crop_climbing_beans, 430, 390, 350, today, CommodityPrice.Status.PUBLISHED),

            (nyabugogo, crop_bush_beans, 420, 380, 340, today, CommodityPrice.Status.PUBLISHED),
            (rwamagana, crop_bush_beans, 390, 350, 310, today, CommodityPrice.Status.PUBLISHED),

            (musanze, crop_potato, 300, 260, 220, today, CommodityPrice.Status.PUBLISHED),
            (mahoko, crop_potato, 290, 250, 210, today, CommodityPrice.Status.PUBLISHED),
            (nyabugogo, crop_potato, 340, 300, 260, today, CommodityPrice.Status.PUBLISHED),
            (kimironko, crop_potato, 350, 310, 270, today, CommodityPrice.Status.PUBLISHED),

            (nyabugogo, crop_rice, 1150, 1050, 950, today, CommodityPrice.Status.PUBLISHED),
            (rwamagana, crop_rice, 1050, 980, 900, today, CommodityPrice.Status.PUBLISHED),
            (huye, crop_cassava, 380, 330, 290, today, CommodityPrice.Status.PUBLISHED),
            (nyabugogo, crop_cassava, 410, 360, 310, today, CommodityPrice.Status.PUBLISHED),
        ]

        # Add 7-day historical trail for Maize at Nyabugogo to power 7-day trend chart
        historical_maize = [
            (today - timedelta(days=6), 405),
            (today - timedelta(days=5), 410),
            (today - timedelta(days=4), 415),
            (today - timedelta(days=3), 425),
            (today - timedelta(days=2), 430),
            (today - timedelta(days=1), 435),
        ]
        for past_date, p_val in historical_maize:
            if nyabugogo and crop_maize:
                price_specs.append((nyabugogo, crop_maize, p_val, p_val - 30, p_val - 60, past_date, CommodityPrice.Status.PUBLISHED))

        # Workflow demonstration records (Submitted, Under Review, Needs Correction, Draft)
        workflow_specs = [
            (kimironko, crop_bush_beans, 470, 420, 380, today, CommodityPrice.Status.SUBMITTED, [], ""),
            (mahoko, crop_maize, 395, 360, 320, today, CommodityPrice.Status.UNDER_REVIEW, ["price_above_benchmark"], ""),
            (huye, crop_potato, 680, 600, 520, today, CommodityPrice.Status.NEEDS_CORRECTION, ["out_of_expected_bounds"], "Price seems quoted per 2kg sack instead of standard kg. Please verify with market collector."),
            (nyagatare, crop_bush_beans, 400, 360, 320, today, CommodityPrice.Status.DRAFT, [], ""),
        ]

        count = 0
        for item in price_specs:
            mkt, crp, retail, wholesale, farmgate, p_date, stat = item
            if not mkt or not crp:
                continue
            price, created = CommodityPrice.objects.update_or_create(
                market=mkt,
                crop=crp,
                date_recorded=p_date,
                price_type="retail",
                defaults={
                    "price_per_kg_rwf": Decimal(str(retail)),
                    "wholesale_price_rwf": Decimal(str(wholesale)),
                    "farmgate_price_rwf": Decimal(str(farmgate)),
                    "status": stat,
                    "unit": "RWF/kg",
                    "collected_by": admin_user,
                    "approved_by": admin_user if stat == CommodityPrice.Status.PUBLISHED else None,
                    "published_at": timezone.now() if stat == CommodityPrice.Status.PUBLISHED else None,
                }
            )
            count += 1

        for mkt, crp, retail, wholesale, farmgate, p_date, stat, flags, comment in workflow_specs:
            if not mkt or not crp:
                continue
            price, _ = CommodityPrice.objects.get_or_create(
                market=mkt,
                crop=crp,
                date_recorded=p_date,
                status=stat,
                defaults={
                    "price_per_kg_rwf": Decimal(str(retail)),
                    "wholesale_price_rwf": Decimal(str(wholesale)),
                    "farmgate_price_rwf": Decimal(str(farmgate)),
                    "validation_flags": flags,
                    "review_comments": comment,
                    "correction_reason": comment,
                    "collected_by": admin_user,
                    "unit": "RWF/kg",
                }
            )
            count += 1
            # Add audit log
            PriceAuditLog.objects.create(
                price_record=price,
                actor=admin_user,
                action=stat,
                reason=comment or f"Surveillance record {stat}",
                details={"price": float(retail), "market": mkt.name, "crop": crp.name}
            )

        # 4. Public Notice
        PricePublicNotice.objects.get_or_create(
            title="Season A Market Stability Bulletin",
            defaults={
                "message": "Maize and bean prices across Eastern and Northern Province assembly markets show positive supply stabilization following post-harvest consolidation.",
                "severity": "info",
                "effective_date": today,
                "is_active": True,
                "created_by": admin_user,
            }
        )

        self.stdout.write(self.style.SUCCESS(f"Successfully populated {count} price records, market hubs, commodities, and workflow queue!"))
