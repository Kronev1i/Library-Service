import pytest
from django.urls import reverse
from rest_framework import status

from books.models import Book


@pytest.mark.django_db
class TestBookList:
    def test_anonymous_can_list_books(self, api_client, book):
        url = reverse("books:book-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_anonymous_can_retrieve_book(self, api_client, book):
        url = reverse("books:book-detail", args=[book.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Test Book"


@pytest.mark.django_db
class TestBookCreate:
    def test_admin_can_create_book(self, admin_client):
        url = reverse("books:book-list")
        payload = {
            "title": "New Book",
            "author": "New Author",
            "cover": "SOFT",
            "inventory": 3,
            "daily_fee": "2.00",
        }
        response = admin_client.post(url, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert Book.objects.count() == 1

    def test_regular_user_cannot_create_book(self, auth_client):
        url = reverse("books:book-list")
        payload = {
            "title": "New Book",
            "author": "New Author",
            "cover": "SOFT",
            "inventory": 3,
            "daily_fee": "2.00",
        }
        response = auth_client.post(url, payload)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_anonymous_cannot_create_book(self, api_client):
        url = reverse("books:book-list")
        payload = {
            "title": "New Book",
            "author": "New Author",
            "cover": "SOFT",
            "inventory": 3,
            "daily_fee": "2.00",
        }
        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestBookUpdateDelete:
    def test_admin_can_update_book(self, admin_client, book):
        url = reverse("books:book-detail", args=[book.id])
        response = admin_client.patch(url, {"inventory": 10})

        assert response.status_code == status.HTTP_200_OK
        book.refresh_from_db()
        assert book.inventory == 10

    def test_admin_can_delete_book(self, admin_client, book):
        url = reverse("books:book-detail", args=[book.id])
        response = admin_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Book.objects.count() == 0

    def test_regular_user_cannot_delete_book(self, auth_client, book):
        url = reverse("books:book-detail", args=[book.id])
        response = auth_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Book.objects.count() == 1
