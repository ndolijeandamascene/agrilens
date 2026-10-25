"""
Spatial & GIS Analysis:
- District choropleth maps of crop intensity
- Agro-ecological typology mapping via unsupervised machine learning
"""
from typing import Dict, Any, List
from apps.ml.services.spatial import DistrictTypologyService


def get_district_typology_clusters() -> List[Dict[str, Any]]:
    """Returns ML-generated agro-ecological cluster typologies for all 30 districts."""
    return DistrictTypologyService.get_all_district_typologies()


def generate_district_choropleth(metric_df=None, geojson_path=None) -> Dict[str, Any]:
    """Create geographic distribution data for visualization."""
    clusters = DistrictTypologyService.get_all_district_typologies()
    return {
        'typology_clusters': clusters,
        'palette': DistrictTypologyService.CLUSTER_PALETTE,
    }
