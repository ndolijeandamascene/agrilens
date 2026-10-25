"""
AgriLens Spatial & GIS Machine Learning Service.
Provides district cluster typologies, centroid descriptions, and GeoJSON properties
for interactive Leaflet choropleth mapping.
"""
from typing import Dict, Any, List
from apps.geography.models import District
from apps.ml.models import DistrictTypology, MLModel


class DistrictTypologyService:
    """Provides district cluster metadata and choropleth GeoJSON feature attributes."""

    # Curated, professional cartographic palette for Rwanda's 4 typologies
    CLUSTER_PALETTE = {
        0: {'fillColor': '#16A34A', 'borderColor': '#15803D', 'name': 'Commercial Cereal Hub'},
        1: {'fillColor': '#EAB308', 'borderColor': '#CA8A04', 'name': 'Fertility-Constrained Rainfed'},
        2: {'fillColor': '#EA580C', 'borderColor': '#C2410C', 'name': 'Post-Harvest Loss Hotspot'},
        3: {'fillColor': '#0284C7', 'borderColor': '#0369A1', 'name': 'Diversified Transition Zone'},
    }

    @classmethod
    def get_all_district_typologies(cls) -> List[Dict[str, Any]]:
        """Returns cluster typology and constraints for all 30 districts."""
        typologies = DistrictTypology.objects.select_related('district', 'district__province').all()
        
        # If not yet generated, attempt to trigger auto-clustering
        if not typologies.exists():
            from .training import DistrictClusteringTrainer
            try:
                DistrictClusteringTrainer.train_and_register()
                typologies = DistrictTypology.objects.select_related('district', 'district__province').all()
            except Exception:
                pass

        results = []
        for typ in typologies:
            cid = typ.cluster_id
            palette = cls.CLUSTER_PALETTE.get(cid, cls.CLUSTER_PALETTE[0])
            results.append({
                'district_id': typ.district.id,
                'district_name': typ.district.name,
                'district_code': typ.district.code,
                'province_name': typ.district.province.name,
                'cluster_id': cid,
                'cluster_name': typ.cluster_name,
                'profile_summary': typ.profile_summary,
                'main_constraints': typ.main_constraints,
                'recommended_interventions': typ.recommended_interventions,
                'avg_yield_kg_per_ha': float(typ.avg_yield_kg_per_ha),
                'seed_adoption_rate': float(typ.seed_adoption_rate),
                'fertilizer_adoption_rate': float(typ.fertilizer_adoption_rate),
                'loss_rate_percentage': float(typ.loss_rate_percentage),
                'style': palette,
            })
        return results

    @classmethod
    def get_typology_by_district(cls, district_id_or_name) -> Dict[str, Any]:
        """Looks up typology for a specific district."""
        q = DistrictTypology.objects.select_related('district', 'district__province')
        if isinstance(district_id_or_name, int):
            typ = q.filter(district_id=district_id_or_name).first()
        else:
            typ = q.filter(district__name__iexact=str(district_id_or_name).strip()).first()

        if not typ:
            return None

        cid = typ.cluster_id
        palette = cls.CLUSTER_PALETTE.get(cid, cls.CLUSTER_PALETTE[0])
        return {
            'district_id': typ.district.id,
            'district_name': typ.district.name,
            'district_code': typ.district.code,
            'province_name': typ.district.province.name,
            'cluster_id': cid,
            'cluster_name': typ.cluster_name,
            'profile_summary': typ.profile_summary,
            'main_constraints': typ.main_constraints,
            'recommended_interventions': typ.recommended_interventions,
            'avg_yield_kg_per_ha': float(typ.avg_yield_kg_per_ha),
            'seed_adoption_rate': float(typ.seed_adoption_rate),
            'fertilizer_adoption_rate': float(typ.fertilizer_adoption_rate),
            'loss_rate_percentage': float(typ.loss_rate_percentage),
            'style': palette,
        }
