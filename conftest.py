import pytest
from rest_framework.test import APIClient

from books.models import Book


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        email="user@test.com", password="testpass123"
    )


@pytest.fixture
def admin_user(django_user_model):
    return django_user_model.objects.create_user(
        email="admin@test.com", password="testpass123", is_staff=True
    )


@pytest.fixture
def book():
    return Book.objects.create(
        title="Test Book",
        author="Test Author",
        cover=Book.Cover.HARD,
        inventory=5,
        daily_fee="1.50",
    )


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client
