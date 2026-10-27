"""
AgriLens Grounded AI Agricultural Assistant Views and APIs.
"""
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes

from .services.parser import GroundedAgriculturalAssistant
from .models import AssistantQueryLog

logger = logging.getLogger(__name__)


def assistant_view(request):
    """
    Interactive web interface for the Grounded Agricultural Data Assistant.
    Provides natural language query input, quick suggestion pills,
    syntax-highlighted ORM query cards, and audit log history.
    """
    recent_queries = []
    if request.user.is_authenticated:
        recent_queries = AssistantQueryLog.objects.filter(
            user=request.user
        ).order_by('-created_at')[:8]

    context = {
        'page_title': 'Grounded AI Agricultural Data Assistant',
        'recent_queries': recent_queries,
        'suggested_queries': [
            "What is the average Irish Potato yield in Musanze?",
            "Which district produces the most beans?",
            "What percentage of farmers in Nyagatare use mineral fertilizer?",
            "What is the vulnerability index for Karongi?",
            "What is the retail price of beans in monitored markets?",
            "What is the average maize yield in Nyagatare?",
        ],
    }
    return render(request, 'assistant/index.html', context)


class AssistantQueryAPIView(APIView):
    """
    POST /api/v1/assistant/query/
    Accepts natural language agricultural questions and executes
    deterministic, read-only aggregations over validated survey microdata.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        query_text = request.data.get('query', '').strip()
        if not query_text:
            return Response(
                {'error': 'A non-empty query string is required in the request body.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user if getattr(request.user, 'is_authenticated', False) else None
        result = GroundedAgriculturalAssistant.answer_query(query_text, user=user)

        return Response(result, status=status.HTTP_200_OK)


class AssistantStatusAPIView(APIView):
    """
    GET /api/v1/assistant/status/ or /assistant/api/status/
    Provides live telemetry on AgriLens AI model file existence, loading state,
    RAM memory mapping, and active background download progress.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from .services.runtime import QwenModelRuntime
        return Response(QwenModelRuntime.get_status(), status=status.HTTP_200_OK)


class AssistantDownloadAPIView(APIView):
    """
    POST /api/v1/assistant/download/ or /assistant/api/download/
    Manually initiates or verifies the background download of the 2.1 GB neural weights.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from .services.runtime import trigger_model_download_if_needed, QwenModelRuntime
        triggered = trigger_model_download_if_needed()
        info = QwenModelRuntime.get_status()
        info['download_triggered'] = triggered
        return Response(info, status=status.HTTP_200_OK)
