"""
AgriLens Machine Learning & Decision Intelligence Views and APIs.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes

from .models import MLModel, DistrictTypology
from .serializers import (
    YieldPredictionInputSerializer,
    ScenarioComparisonInputSerializer,
    MLModelSerializer,
    DistrictTypologySerializer,
)
from .permissions import CanTrainMLModel, CanViewML
from .services.inference import YieldInferenceService
from .services.productivity import MLProductivityService
from .services.spatial import DistrictTypologyService
from .services.forecasting import (
    ProductionForecastingService,
    MarketPriceForecastingService,
)
from .services.explainability import ModelExplainabilityService
from .services.training import YieldPredictionTrainer, DistrictClusteringTrainer
from .services.recommendation import CropRecommendationService

logger = logging.getLogger(__name__)


class PredictYieldAPIView(APIView):
    """
    POST /api/v1/ml/predict-yield/
    Accepts farm management conditions and returns predicted yield and baseline benchmarks.
    """
    permission_classes = [CanViewML]

    def post(self, request):
        serializer = YieldPredictionInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid farm input parameters', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = YieldInferenceService.predict(serializer.validated_data)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error("PredictYieldAPIView error: %s", exc)
            return Response(
                {'error': 'Yield inference failed', 'message': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SimulateScenarioAPIView(APIView):
    """
    POST /api/v1/ml/simulate-scenario/
    Compares current farming practices against recommended management practices.
    """
    permission_classes = [CanViewML]

    def post(self, request):
        serializer = ScenarioComparisonInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid scenario parameters', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        try:
            result = MLProductivityService.compare_scenarios(
                district=data['district'],
                crop=data['crop'],
                plot_area_ha=data['plot_area_ha'],
                current_practices=data.get('current_practices', {}),
                recommended_practices=data.get('recommended_practices', {})
            )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error("SimulateScenarioAPIView error: %s", exc)
            return Response(
                {'error': 'Scenario simulation failed', 'message': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DistrictClustersAPIView(APIView):
    """
    GET /api/v1/ml/district-clusters/
    Returns agro-ecological cluster typologies and constraints for all 30 districts.
    """
    permission_classes = [CanViewML]

    def get(self, request):
        district_id = request.GET.get('district_id')
        district_name = request.GET.get('district')

        if district_id or district_name:
            target = district_id or district_name
            record = DistrictTypologyService.get_typology_by_district(target)
            if not record:
                return Response(
                    {'error': f"Typology not found for district '{target}'"},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(record, status=status.HTTP_200_OK)

        clusters = DistrictTypologyService.get_all_district_typologies()
        return Response({
            'total_districts': len(clusters),
            'palette': DistrictTypologyService.CLUSTER_PALETTE,
            'clusters': clusters,
        }, status=status.HTTP_200_OK)


class ProductionForecastAPIView(APIView):
    """
    GET /api/v1/ml/forecast/
    Returns seasonal production forecast, multi-year trends, and early-warning deficit flags.
    """
    permission_classes = [CanViewML]

    def get(self, request):
        crop = request.GET.get('crop', 'Maize')
        season = request.GET.get('season', '2026A')
        province = request.GET.get('province')
        district = request.GET.get('district')

        forecast = ProductionForecastingService.get_forecast(
            crop_name=crop,
            forecast_season=season,
            province_name=province,
            district_name=district
        )
        return Response(forecast, status=status.HTTP_200_OK)


class MarketPriceForecastAPIView(APIView):
    """
    GET /api/v1/ml/price-forecast/
    Returns market price surveillance analysis and time-series forecast eligibility status.
    """
    permission_classes = [CanViewML]

    def get(self, request):
        crop = request.GET.get('crop', 'Maize')
        analysis = MarketPriceForecastingService.get_market_analysis(crop_name=crop)
        return Response(analysis, status=status.HTTP_200_OK)


class ModelListAPIView(APIView):
    """
    GET /api/v1/ml/models/
    Returns registry list of all ML models, active statuses, and validation metrics.
    """
    permission_classes = [CanViewML]

    def get(self, request):
        models = MLModel.objects.all().order_by('-created_at')
        serializer = MLModelSerializer(models, many=True)
        return Response({
            'count': models.count(),
            'models': serializer.data,
        }, status=status.HTTP_200_OK)


class ModelExplainabilityAPIView(APIView):
    """
    GET /api/v1/ml/explainability/
    Returns feature importance rankings, validation methodology, and non-causal limitations.
    """
    permission_classes = [CanViewML]

    def get(self, request):
        report = ModelExplainabilityService.get_report()
        return Response(report, status=status.HTTP_200_OK)


class TrainModelsAPIView(APIView):
    """
    POST /api/v1/ml/train/
    Triggers model training from PostgreSQL microdata.
    Restricted to Administrators, NISR Managers, and Analysts.
    """
    permission_classes = [CanTrainMLModel]

    def post(self, request):
        model_type = request.data.get('model_type', 'all')
        version = request.data.get('version', 'v1.0')
        results = {}

        try:
            if model_type in ('all', 'yield'):
                y_model, y_metrics = YieldPredictionTrainer.train_and_register(
                    user=request.user, version=version
                )
                results['yield_model'] = {
                    'version': y_model.version,
                    'status': y_model.status,
                    'metrics': y_metrics,
                }

            if model_type in ('all', 'clustering'):
                c_model, dist_count = DistrictClusteringTrainer.train_and_register(
                    user=request.user, version=version
                )
                results['district_clustering'] = {
                    'version': c_model.version,
                    'districts_updated': dist_count,
                    'status': c_model.status,
                }

            try:
                from apps.notifications.services import NotificationService
                from apps.notifications.models import Notification
                NotificationService.send(
                    recipient=request.user,
                    notification_type=Notification.Type.ML_TRAINING_COMPLETED,
                    title=f"ML Model Training Completed: {model_type}",
                    message=f"Model training and registry update for '{model_type}' ({version}) completed successfully.",
                    action_url="/indicators/models/",
                    priority=Notification.Priority.LOW,
                )
            except Exception:
                pass

            return Response({
                'status': 'SUCCESS',
                'message': 'Model training and registry update completed successfully.',
                'results': results,
            }, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.error("TrainModelsAPIView failed: %s", exc)

            try:
                from apps.notifications.services import NotificationService
                from apps.notifications.models import Notification
                NotificationService.send(
                    recipient=request.user,
                    notification_type=Notification.Type.ML_TRAINING_FAILED,
                    title=f"ML Model Training Failed: {model_type}",
                    message=f"Model training for '{model_type}' ({version}) failed: {str(exc)}",
                    action_url="/indicators/models/",
                    priority=Notification.Priority.HIGH,
                )
            except Exception:
                pass

            return Response(
                {'status': 'FAILED', 'error': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DistrictVulnerabilityAPIView(APIView):
    """
    GET /api/v1/ml/vulnerability/
    Returns multi-criteria District Agricultural Vulnerability Index (AVI) scores,
    component breakdowns (yield gap, post-harvest loss, input deficit, price volatility),
    and operational intervention tiers for all 30 districts in Rwanda.
    """
    permission_classes = [CanViewML]

    def get(self, request):
        try:
            year = int(request.GET.get('year', 2025))
        except (ValueError, TypeError):
            year = 2025
        season = request.GET.get('season', 'A').strip().upper()
        refresh = request.GET.get('refresh', 'false').lower() == 'true'

        from apps.decision_support.services.vulnerability import AgriculturalVulnerabilityService
        data = AgriculturalVulnerabilityService.compute_all_districts(
            year=year,
            season=season,
            use_cache=not refresh
        )
        return Response(data, status=status.HTTP_200_OK)


class CropRecommendationAPIView(APIView):
    """
    GET /api/v1/ml/recommend-crop/?district=Musanze
    Returns ranked crop suitability scorecard based on empirical microdata,
    agro-ecological cluster typology, post-harvest resilience, and wholesale revenue potential.
    """
    permission_classes = [CanViewML]

    def get(self, request):
        district = request.GET.get('district', 'Musanze').strip()
        try:
            top_n = int(request.GET.get('top_n', 5))
        except (ValueError, TypeError):
            top_n = 5
        result = CropRecommendationService.recommend_for_district(district, top_n=top_n)
        return Response(
            result,
            status=status.HTTP_200_OK if result.get('success') else status.HTTP_400_BAD_REQUEST
        )

