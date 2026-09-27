import pytest
from django.urls import reverse
from rest_framework import status

from users.models import User


@pytest.mark.django_db
class TestUserRegistration:
    def test_can_register_new_user(self, api_client):
        url = reverse("users:create")
        payload = {
            "email": "new@test.com",
            "password": "strongpass123",
            "first_name": "Test",
            "last_name": "User",
        }
        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email="new@test.com").exists()

    def test_password_is_not_returned_in_response(self, api_client):
        url = reverse("users:create")
        payload = {"email": "new@test.com", "password": "strongpass123"}
        response = api_client.post(url, payload)

        assert "password" not in response.data

    def test_password_is_hashed(self, api_client):
        url = reverse("users:create")
        payload = {"email": "new@test.com", "password": "strongpass123"}
        api_client.post(url, payload)

        user = User.objects.get(email="new@test.com")
        assert user.password != "strongpass123"
        assert user.check_password("strongpass123")

    def test_cannot_register_duplicate_email(self, api_client, user):
        url = reverse("users:create")
        payload = {"email": user.email, "password": "anotherpass123"}
        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserToken:
    def test_can_obtain_token_with_valid_credentials(self, api_client, user):
        url = reverse("users:token_obtain_pair")
        payload = {"email": user.email, "password": "testpass123"}
        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_cannot_obtain_token_with_wrong_password(self, api_client, user):
        url = reverse("users:token_obtain_pair")
        payload = {"email": user.email, "password": "wrongpassword"}
        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserProfile:
    def test_authenticated_user_can_view_own_profile(self, auth_client, user):
        url = reverse("users:manage")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email

    def test_anonymous_cannot_view_profile(self, api_client):
        url = reverse("users:manage")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_can_update_own_profile(self, auth_client):
        url = reverse("users:manage")
        response = auth_client.patch(url, {"first_name": "Updated"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Updated"
