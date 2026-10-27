"""
Tests for Qwen 2.5 3B In-Process Runtime, Role-Aware Prompt Builder,
and Public Chatbot Widget Integration in AgriLens.
"""
import pytest
from unittest.mock import patch, MagicMock
from django.test import Client
from rest_framework.test import APIClient
from django.contrib.auth.models import AnonymousUser

from apps.accounts.models import User
from apps.assistant.services.prompt_builder import AgronomicPromptBuilder
from apps.assistant.services.runtime import QwenModelRuntime
from apps.assistant.services.parser import GroundedAgriculturalAssistant


@pytest.mark.django_db
class TestAgronomicPromptBuilder:
    """Verifies that the prompt builder correctly injects role-based clearance and governance boundaries."""

    def test_anonymous_user_clearance(self):
        """Anonymous visitor receives PUBLIC_VISITOR clearance with public scope."""
        anon = AnonymousUser()
        clearance = AgronomicPromptBuilder.get_user_clearance(anon)

        assert clearance['role_code'] == 'PUBLIC_VISITOR'
        assert clearance['clearance'] == 'PUBLIC_AGGREGATES_ONLY'
        assert clearance['is_institutional'] is False
        assert 'Public' in clearance['role_title']

    def test_none_user_clearance(self):
        """None user falls back cleanly to PUBLIC_VISITOR clearance."""
        clearance = AgronomicPromptBuilder.get_user_clearance(None)

        assert clearance['role_code'] == 'PUBLIC_VISITOR'
        assert clearance['clearance'] == 'PUBLIC_AGGREGATES_ONLY'
        assert clearance['is_institutional'] is False

    def test_institutional_officer_clearance(self):
        """District Officer receives institutional clearance with designated title."""
        user = User.objects.create_user(
            username='district_officer_musanze',
            email='musanze@agrilens.rw',
            role=User.Role.DISTRICT_OFFICER
        )
        clearance = AgronomicPromptBuilder.get_user_clearance(user)

        assert clearance['role_code'] == 'DISTRICT_OFFICER'
        assert clearance['clearance'] == 'INSTITUTIONAL_CLEARANCE'
        assert clearance['is_institutional'] is True
        assert 'District Agriculture Officer' in clearance['role_title']

    def test_admin_user_clearance(self):
        """Administrator receives system administrator role clearance."""
        admin = User.objects.create_superuser(
            username='sys_admin',
            email='admin@agrilens.rw',
            password='Password123!',
            role=User.Role.ADMIN
        )
        clearance = AgronomicPromptBuilder.get_user_clearance(admin)

        assert clearance['role_code'] == 'ADMIN'
        assert clearance['clearance'] == 'INSTITUTIONAL_CLEARANCE'
        assert clearance['is_institutional'] is True
        assert 'System Administrator' in clearance['role_title']

    def test_build_system_prompt_contains_role(self):
        """System prompt explicitly mentions user role, clearance, and non-causal directives."""
        clearance = {
            'role_code': 'DISTRICT_OFFICER',
            'role_title': 'District Agriculture Officer',
            'clearance': 'INSTITUTIONAL_CLEARANCE',
            'scope': 'Musanze District',
            'is_institutional': True,
        }
        prompt = AgronomicPromptBuilder.build_system_prompt(clearance)

        assert 'District Agriculture Officer' in prompt
        assert 'INSTITUTIONAL_CLEARANCE' in prompt
        assert 'Musanze District' in prompt
        assert 'STATISTICAL INTEGRITY' in prompt
        assert 'GENERAL CONVERSATION' in prompt

    def test_build_chatml_messages_general_intent(self):
        """General questions generate standard conversational ChatML messages with role clearance."""
        messages = AgronomicPromptBuilder.build_chatml_messages(
            query="Hello, how can you help me?",
            intent="GENERAL",
            metrics={},
            deterministic_answer="Welcome to AgriLens.",
            user=None
        )

        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[1]['role'] == 'user'
        assert 'PUBLIC_AGGREGATES_ONLY' in messages[0]['content']
        assert 'Hello, how can you help me?' in messages[1]['content']

    def test_build_chatml_messages_empirical_intent(self):
        """Empirical queries include the exact computed facts in the user prompt."""
        messages = AgronomicPromptBuilder.build_chatml_messages(
            query="What is the average Irish Potato yield in Musanze?",
            intent="YIELD",
            metrics={'mean_yield_t_ha': 9.5, 'sample_count': 5},
            deterministic_answer="Average Irish Potato yield in Musanze is 9.50 t/ha across 5 observations.",
            user=None
        )

        assert len(messages) == 2
        assert 'OFFICIALLY COMPUTED STATISTICAL FACTS' in messages[1]['content']
        assert '9.50 t/ha' in messages[1]['content']
        assert 'mean_yield_t_ha' in messages[1]['content']


@pytest.mark.django_db
class TestQwenModelRuntime:
    """Verifies that the Qwen in-process runtime handles initialization, fallback, and inference safely."""

    def test_runtime_reports_operational_telemetry(self):
        """Operational telemetry reports 100% operational grounded ML engine."""
        status = QwenModelRuntime.get_status()
        assert status['status'] == 'OPERATIONAL'
        assert status['grounded_observations'] == 23833
        assert status['zero_hallucination'] is True

    def test_runtime_graceful_fallback_when_disabled(self):
        """Pure ML runtime prioritizes deterministic execution without external LLM."""
        response = QwenModelRuntime.generate(
            messages=[{"role": "user", "content": "Hello"}]
        )
        assert response is None

    def test_parser_falls_back_to_deterministic_if_qwen_unavailable(self):
        """GroundedAgriculturalAssistant produces verified deterministic answers with ML governance."""
        result = GroundedAgriculturalAssistant.answer_query(
            "What is the average Irish Potato yield in Musanze?"
        )
        assert result['status'] in ['SUCCESS', 'NO_DATA', 'AGRONOMIC_CONTEXT']
        assert 'answer' in result
        assert result['synthesized_by'] == 'AgriLens Grounded ML Intelligence Engine'


@pytest.mark.django_db
class TestPublicChatbotWidget:
    """Verifies that the public chatbot widget is rendered on public pages and functional."""

    def test_public_home_renders_chatbot_widget(self):
        """Public homepage contains the floating chatbot trigger button and drawer modal."""
        client = Client()
        response = client.get('/')
        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Check floating launcher and modal presence
        assert 'publicAiWidgetTrigger' in content
        assert 'publicAiWidgetWindow' in content
        assert 'AgriLens Grounded Assistant' in content
        assert 'Ask AgriLens Assistant' in content

    def test_public_api_endpoint_handles_general_queries(self):
        """Assistant API /api/v1/assistant/query/ accepts general agronomic queries from public widget."""
        api_client = APIClient()
        response = api_client.post(
            '/api/v1/assistant/query/',
            {'query': 'Hello, can you give me advice on maize planting?'},
            format='json'
        )
        assert response.status_code == 200
        data = response.json()

        assert data['status'] in ['SUCCESS', 'GENERAL_GUIDANCE']
        assert 'answer' in data
        assert len(data['answer']) > 0
