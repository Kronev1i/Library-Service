import datetime

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from borrowings.models import Borrowing


@pytest.fixture
def borrowing(book, user):
    return Borrowing.objects.create(
        expected_return_date=timezone.now().date() + datetime.timedelta(days=7),
        book=book,
        user=user,
    )


@pytest.mark.django_db
class TestBorrowingList:
    def test_user_sees_only_own_borrowings(
        self, auth_client, borrowing, book, admin_user
    ):
        other_borrowing = Borrowing.objects.create(
            expected_return_date=timezone.now().date() + datetime.timedelta(days=7),
            book=book,
            user=admin_user,
        )
        url = reverse("borrowings:borrowing-list")
        response = auth_client.get(url)

        ids = [item["id"] for item in response.data]
        assert borrowing.id in ids
        assert other_borrowing.id not in ids

    def test_admin_sees_all_borrowings(self, admin_client, borrowing, book, admin_user):
        Borrowing.objects.create(
            expected_return_date=timezone.now().date() + datetime.timedelta(days=7),
            book=book,
            user=admin_user,
        )
        url = reverse("borrowings:borrowing-list")
        response = admin_client.get(url)

        assert len(response.data) == 2

    def test_anonymous_cannot_list_borrowings(self, api_client):
        url = reverse("borrowings:borrowing-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_is_active_filter(self, auth_client, borrowing):
        borrowing.actual_return_date = timezone.now().date()
        borrowing.save()

        url = reverse("borrowings:borrowing-list")
        response = auth_client.get(url, {"is_active": "true"})

        assert len(response.data) == 0

        response = auth_client.get(url, {"is_active": "false"})
        assert len(response.data) == 1


@pytest.mark.django_db
class TestBorrowingDetail:
    def test_detail_includes_nested_book(self, auth_client, borrowing, book):
        url = reverse("borrowings:borrowing-detail", args=[borrowing.id])
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["book"]["title"] == book.title


@pytest.mark.django_db
class TestBorrowingCreate:
    def test_create_decreases_inventory(self, auth_client, book):
        url = reverse("borrowings:borrowing-list")
        payload = {
            "expected_return_date": str(
                timezone.now().date() + datetime.timedelta(days=5)
            ),
            "book": book.id,
        }
        response = auth_client.post(url, payload)

        assert response.status_code == status.HTTP_201_CREATED
        book.refresh_from_db()
        assert book.inventory == 4

    def test_cannot_create_when_out_of_stock(self, auth_client, book):
        book.inventory = 0
        book.save()

        url = reverse("borrowings:borrowing-list")
        payload = {
            "expected_return_date": str(
                timezone.now().date() + datetime.timedelta(days=5)
            ),
            "book": book.id,
        }
        response = auth_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_borrowing_attached_to_current_user(self, auth_client, book, user):
        url = reverse("borrowings:borrowing-list")
        payload = {
            "expected_return_date": str(
                timezone.now().date() + datetime.timedelta(days=5)
            ),
            "book": book.id,
        }
        auth_client.post(url, payload)

        assert Borrowing.objects.filter(user=user).exists()


@pytest.mark.django_db
class TestBorrowingReturn:
    def test_successful_return_increases_inventory(
        self, auth_client, borrowing, book
    ):
        original_inventory = book.inventory
        url = reverse("borrowings:borrowing-return-borrowing", args=[borrowing.id])
        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        book.refresh_from_db()
        assert book.inventory == original_inventory + 1

    def test_cannot_return_twice(self, auth_client, borrowing):
        url = reverse("borrowings:borrowing-return-borrowing", args=[borrowing.id])
        auth_client.post(url)
        response = auth_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_can_return_other_users_borrowing(self, admin_client, borrowing):
        url = reverse("borrowings:borrowing-return-borrowing", args=[borrowing.id])
        response = admin_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        borrowing.refresh_from_db()
        assert borrowing.actual_return_date is not None

    def test_regular_user_cannot_return_other_users_borrowing(
        self, api_client, book, user, admin_user
    ):
        others_borrowing = Borrowing.objects.create(
            expected_return_date=timezone.now().date() + datetime.timedelta(days=7),
            book=book,
            user=admin_user,
        )
        api_client.force_authenticate(user=user)
        url = reverse(
            "borrowings:borrowing-return-borrowing", args=[others_borrowing.id]
        )
        response = api_client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
