"""
Tests for ML Permissions & Access Control
"""
import pytest
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestMLPermissions:
    def test_anonymous_cannot_trigger_training(self, api_client):
        response = api_client.post('/api/v1/ml/train/', data={}, format='json')
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_unauthorized_role_cannot_trigger_training(self, api_client):
        # District officer should not be able to retrain models
        user = User.objects.create_user(
            username='district_user',
            password='Password123!',
            role=User.Role.DISTRICT_OFFICER
        )
        api_client.force_authenticate(user=user)

        response = api_client.post('/api/v1/ml/train/', data={}, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_authorized_analyst_can_trigger_training(self, api_client):
        analyst = User.objects.create_user(
            username='analyst_user',
            password='Password123!',
            role=User.Role.ANALYST
        )
        api_client.force_authenticate(user=analyst)

        # Triggering training with dry-run/quick params or testing permission acceptance
        response = api_client.post('/api/v1/ml/train/', data={"model_type": "yield", "version": "v1.1-test"}, format='json')
        # Response should be 200 OK (training initiated/succeeded) or not 403 Forbidden
        assert response.status_code != status.HTTP_403_FORBIDDEN

    def test_public_can_view_models_and_explainability(self, api_client):
        resp_models = api_client.get('/api/v1/ml/models/')
        assert resp_models.status_code == status.HTTP_200_OK

        resp_exp = api_client.get('/api/v1/ml/explainability/')
        assert resp_exp.status_code == status.HTTP_200_OK
