"""
AgriLens Intelligent Crop Suitability & Recommendation Service.
Ranks and recommends crops for any of Rwanda's 30 districts based on:
1. Agro-ecological cluster typology (K-Means 4-cluster classification).
2. Empirical microdata productivity (NISR ValidatedObservations).
3. Prevailing commodity market price returns (CommodityPrice).
4. Post-harvest loss risk profiles.
"""
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from django.db.models import Avg, Count, Max, Min, Q

from apps.geography.models import District
from apps.agriculture.models import Crop
from apps.data_management.models import ValidatedObservation
from apps.markets.models import CommodityPrice
from .spatial import DistrictTypologyService

logger = logging.getLogger(__name__)


class CropRecommendationService:
    """Evaluates agro-ecological suitability and commercial potential across crops for a district."""

    # Priority crops monitored in SAS microdata
    EVALUATED_CROPS = [
        'Irish Potato',
        'Maize',
        'Climbing Beans',
        'Bush Beans',
        'Sweet Potato',
        'Cassava',
        'Rice',
        'Soybeans',
        'Wheat',
        'Sorghum',
        'Banana',
    ]

    # Cluster agronomic affinities (boost scores for aligned cluster typologies)
    CLUSTER_AFFINITIES = {
        0: ['Maize', 'Soybeans', 'Rice', 'Bush Beans'],                     # Commercial Cereal Hub (Eastern Plains)
        1: ['Cassava', 'Sorghum', 'Sweet Potato', 'Bush Beans'],            # Fertility-Constrained Rainfed
        2: ['Banana', 'Cassava', 'Irish Potato', 'Sweet Potato'],           # Post-Harvest Loss Hotspot (Western High-Rainfall)
        3: ['Irish Potato', 'Climbing Beans', 'Wheat', 'Maize'],            # Diversified Transition Zone (Northern Highlands)
    }

    @classmethod
    def recommend_for_district(cls, district_name: str, top_n: int = 5) -> Dict[str, Any]:
        """
        Computes multi-criteria suitability scorecard and returns ranked recommendations.
        """
        district_clean = district_name.strip()
        district_obj = District.objects.filter(name__iexact=district_clean).first()
        if not district_obj:
            return {
                'success': False,
                'error': f"District '{district_clean}' not recognized.",
                'district': district_clean,
                'recommendations': []
            }

        # Retrieve cluster typology
        typology = DistrictTypologyService.get_typology_by_district(district_obj.name)
        cluster_id = typology.get('cluster_id', 0) if typology else 0
        cluster_name = typology.get('cluster_name', 'Commercial Cereal Hub') if typology else 'General Agricultural Zone'
        preferred_crops = cls.CLUSTER_AFFINITIES.get(cluster_id, [])

        # Fetch empirical district observations across evaluated crops
        scored_crops: List[Dict[str, Any]] = []

        for crop_name in cls.EVALUATED_CROPS:
            # Microdata filter for this crop in this district
            obs_qs = ValidatedObservation.objects.filter(
                district=district_obj,
                crop__name__icontains=crop_name,
                provenance__startswith='NISR_'
            )
            plot_count = obs_qs.count()

            # Baseline metrics
            if plot_count >= 3:
                agg = obs_qs.aggregate(
                    avg_yield=Avg('calculated_yield_kg_per_ha'),
                    avg_loss=Avg('loss_rate_percentage')
                )
                mean_yield_kg = float(agg['avg_yield'] or 0.0)
                mean_loss_pct = float(agg['avg_loss'] or 0.0)
                data_confidence = 'HIGH' if plot_count >= 15 else 'MODERATE'
            else:
                # National benchmark fallback for this crop
                nat_qs = ValidatedObservation.objects.filter(
                    crop__name__icontains=crop_name,
                    provenance__startswith='NISR_'
                )
                nat_count = nat_qs.count()
                if nat_count == 0:
                    continue
                agg = nat_qs.aggregate(
                    avg_yield=Avg('calculated_yield_kg_per_ha'),
                    avg_loss=Avg('loss_rate_percentage')
                )
                mean_yield_kg = float(agg['avg_yield'] or 0.0) * 0.90  # Uncalibrated district penalty
                mean_loss_pct = float(agg['avg_loss'] or 0.0)
                data_confidence = 'LOW (National Proxy)'

            if mean_yield_kg <= 0:
                continue

            # Prevailing market price lookup
            price_record = CommodityPrice.objects.filter(
                crop__name__icontains=crop_name,
                status=CommodityPrice.Status.PUBLISHED
            ).order_by('-date_recorded').first()
            unit_price_rwf = float(price_record.price_per_kg_rwf) if price_record else 350.0

            # Economic gross potential per hectare (RWF/ha)
            gross_revenue_rwf_ha = round(mean_yield_kg * unit_price_rwf, 0)

            # Suitability Scoring Algorithm (0 - 100)
            # 1. Cluster affinity bonus: up to 25 pts
            affinity_pts = 25.0 if crop_name in preferred_crops else 10.0

            # 2. Yield performance relative to standard benchmark: up to 35 pts
            yield_tha = mean_yield_kg / 1000.0
            if crop_name in ('Irish Potato', 'Sweet Potato', 'Cassava', 'Banana'):
                yield_pts = min(35.0, (yield_tha / 12.0) * 35.0)
            else:
                yield_pts = min(35.0, (yield_tha / 2.5) * 35.0)

            # 3. Post-harvest resilience (lower loss is better): up to 20 pts
            loss_penalty = min(20.0, (mean_loss_pct / 25.0) * 20.0)
            resilience_pts = max(0.0, 20.0 - loss_penalty)

            # 4. Economic return density: up to 20 pts
            econ_pts = min(20.0, (gross_revenue_rwf_ha / 2_500_000.0) * 20.0)

            composite_score = round(affinity_pts + yield_pts + resilience_pts + econ_pts, 1)

            # Risk classification
            if mean_loss_pct > 18.0:
                loss_risk = 'HIGH_LOSS_RISK'
            elif mean_loss_pct > 10.0:
                loss_risk = 'MODERATE_LOSS_RISK'
            else:
                loss_risk = 'LOW_LOSS_RISK'

            scored_crops.append({
                'crop_name': crop_name,
                'composite_score': composite_score,
                'yield_kg_per_ha': round(mean_yield_kg, 1),
                'yield_tha': round(yield_tha, 2),
                'loss_rate_pct': round(mean_loss_pct, 1),
                'loss_risk': loss_risk,
                'market_price_rwf_kg': round(unit_price_rwf, 1),
                'indicative_gross_revenue_rwf_ha': gross_revenue_rwf_ha,
                'cluster_aligned': crop_name in preferred_crops,
                'data_confidence': data_confidence,
                'plot_sample_size': plot_count,
            })

        # Sort descending by composite score
        scored_crops.sort(key=lambda x: x['composite_score'], reverse=True)
        top_recommendations = scored_crops[:top_n]

        # Assign rank
        for idx, rec in enumerate(top_recommendations, start=1):
            rec['rank'] = idx

        return {
            'success': True,
            'district': district_obj.name,
            'province': district_obj.province.name,
            'cluster_typology': {
                'cluster_id': cluster_id,
                'cluster_name': cluster_name,
                'preferred_specializations': preferred_crops,
                'summary': typology.get('profile_summary', '') if typology else '',
            },
            'total_crops_evaluated': len(scored_crops),
            'recommendations': top_recommendations,
            'disclaimer': (
                "Recommendations combine empirical SAS survey yields, agro-ecological clustering, "
                "and wholesale market prices. Farm-specific soil testing and topography should guide final planting."
            )
        }
