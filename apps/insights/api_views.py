"""
AgriLens Agricultural Insights REST API Views.
Enforces institutional RBAC, public vs. internal segregation,
pagination, and query optimization.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from django.core.exceptions import PermissionDenied, ValidationError

from apps.agriculture.models import AgriculturalSeason
from apps.insights.models import AgriculturalInsight
from apps.insights.serializers import (
    AgriculturalInsightListSerializer,
    AgriculturalInsightDetailSerializer,
    InsightActionSerializer,
    InsightGenerateSerializer,
    InsightStatisticsSerializer,
)
from apps.insights.services.engine import AgriculturalInsightEngine
from apps.insights.services.rules import resolve_comparison_period
from apps.insights.services.workflow import InsightWorkflowService


class AgriculturalInsightViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Agricultural Insights API:
    - Public visitors receive exclusively approved & published insights.
    - Institutional users (Analysts, NISR Managers, Admins) access full lifecycle & actions.
    """
    lookup_field = 'pk'

    def get_queryset(self):
        user = self.request.user
        qs = AgriculturalInsight.objects.select_related(
            'crop', 'district', 'province', 'current_season', 'comparison_season', 'created_by', 'reviewed_by'
        )

        # Public anonymous access is restricted to PUBLISHED insights
        if not user.is_authenticated or not InsightWorkflowService.can_review(user):
            qs = qs.filter(status=AgriculturalInsight.Status.PUBLISHED)
        else:
            # Internal user can filter by status
            status_param = self.request.query_params.get('status')
            if status_param:
                qs = qs.filter(status=status_param)

        # Common filters
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)

        crop_id = self.request.query_params.get('crop')
        if crop_id:
            qs = qs.filter(crop_id=crop_id)

        district_id = self.request.query_params.get('district')
        if district_id:
            qs = qs.filter(district_id=district_id)

        province_id = self.request.query_params.get('province')
        if province_id:
            qs = qs.filter(province_id=province_id)

        year = self.request.query_params.get('year')
        if year:
            qs = qs.filter(current_season__year=year)

        season_code = self.request.query_params.get('season')
        if season_code:
            qs = qs.filter(current_season__season=season_code.upper())

        quality = self.request.query_params.get('data_quality')
        if quality:
            qs = qs.filter(data_quality_status=quality)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(summary__icontains=search) |
                Q(headline__icontains=search) |
                Q(crop__name__icontains=search) |
                Q(district__name__icontains=search)
            )

        return qs

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AgriculturalInsightDetailSerializer
        return AgriculturalInsightListSerializer

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Returns aggregate distribution of insights for dashboard KPI cards."""
        user = request.user
        base_qs = AgriculturalInsight.objects.all()
        if not user.is_authenticated or not InsightWorkflowService.can_review(user):
            base_qs = base_qs.filter(status=AgriculturalInsight.Status.PUBLISHED)

        total = base_qs.count()
        published = base_qs.filter(status=AgriculturalInsight.Status.PUBLISHED).count()
        under_review = base_qs.filter(status=AgriculturalInsight.Status.UNDER_REVIEW).count()
        generated = base_qs.filter(status=AgriculturalInsight.Status.GENERATED).count()
        approved = base_qs.filter(status=AgriculturalInsight.Status.APPROVED).count()
        rejected = base_qs.filter(status=AgriculturalInsight.Status.REJECTED).count()

        # Category counts
        cat_counts = {}
        for row in base_qs.values('category').annotate(cnt=Count('id')):
            cat_counts[row['category']] = row['cnt']

        # Province counts
        prov_counts = {}
        for row in base_qs.values('province__name').annotate(cnt=Count('id')):
            p_name = row['province__name'] or 'National'
            prov_counts[p_name] = row['cnt']

        # Quality status counts
        quality_counts = {}
        for row in base_qs.values('data_quality_status').annotate(cnt=Count('id')):
            quality_counts[row['data_quality_status']] = row['cnt']

        return Response({
            'total_insights': total,
            'published_count': published,
            'under_review_count': under_review,
            'generated_count': generated,
            'approved_count': approved,
            'rejected_count': rejected,
            'by_category': cat_counts,
            'by_province': prov_counts,
            'by_data_quality': quality_counts,
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def approve(self, request, pk=None):
        """Approves a generated or under-review insight."""
        insight = self.get_object()
        serializer = InsightActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comments = serializer.validated_data.get('comments', '')

        try:
            InsightWorkflowService.approve(insight, request.user, comments=comments, request=request)
            return Response({'status': 'approved', 'insight_id': insight.id, 'message': 'Insight successfully approved.'})
        except (PermissionDenied, ValidationError) as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        """Rejects an insight with mandatory justification comment."""
        insight = self.get_object()
        serializer = InsightActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comments = serializer.validated_data.get('comments', '')

        try:
            InsightWorkflowService.reject(insight, request.user, comments=comments, request=request)
            return Response({'status': 'rejected', 'insight_id': insight.id, 'message': 'Insight rejected.'})
        except (PermissionDenied, ValidationError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def publish(self, request, pk=None):
        """Publishes an insight to make it publicly visible."""
        insight = self.get_object()
        try:
            InsightWorkflowService.publish(insight, request.user, request=request)
            return Response({'status': 'published', 'insight_id': insight.id, 'message': 'Insight successfully published to public portal.'})
        except (PermissionDenied, ValidationError) as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def unpublish(self, request, pk=None):
        """Unpublishes an insight."""
        insight = self.get_object()
        serializer = InsightActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comments = serializer.validated_data.get('comments', '')

        try:
            InsightWorkflowService.unpublish(insight, request.user, comments=comments, request=request)
            return Response({'status': 'under_review', 'insight_id': insight.id, 'message': 'Insight unpublished and returned to review queue.'})
        except (PermissionDenied, ValidationError) as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def generate(self, request):
        """Triggers the Insight Engine to discover patterns for a designated season."""
        if not InsightWorkflowService.can_review(request.user):
            return Response({'error': 'Unauthorized to trigger insight generation.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = InsightGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        year = serializer.validated_data['year']
        season_code = serializer.validated_data['season'].upper()
        auto_publish = serializer.validated_data['auto_publish']
        min_pct = serializer.validated_data['min_pct']

        season = AgriculturalSeason.objects.filter(year=year, season=season_code).first()
        if not season:
            return Response({'error': f"Season {year}{season_code} not found."}, status=status.HTTP_404_NOT_FOUND)

        comp_season = resolve_comparison_period(season)
        engine = AgriculturalInsightEngine(current_season=season, comparison_season=comp_season, user=request.user)
        generated = engine.generate_all(auto_publish=auto_publish, min_pct_change=min_pct)

        return Response({
            'status': 'success',
            'count': len(generated),
            'season': str(season),
            'comparison_season': str(comp_season) if comp_season else None,
            'auto_published': auto_publish,
            'message': f"Discovered and processed {len(generated)} agricultural insights."
        })
