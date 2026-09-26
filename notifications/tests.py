from unittest.mock import patch

from notifications.telegram import send_telegram_message
from notifications.tasks import check_overdue_borrowings


class TestSendTelegramMessage:
    @patch("notifications.telegram.requests.post")
    def test_sends_message_with_correct_params(self, mock_post, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")

        send_telegram_message("Hello")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "fake-token" in args[0]
        assert kwargs["data"]["chat_id"] == "12345"
        assert kwargs["data"]["text"] == "Hello"

    @patch("notifications.telegram.requests.post")
    def test_does_nothing_without_credentials(self, mock_post, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

        send_telegram_message("Hello")

        mock_post.assert_not_called()


import datetime

import pytest
from django.utils import timezone

from borrowings.models import Borrowing


@pytest.mark.django_db
class TestCheckOverdueBorrowings:
    @patch("notifications.tasks.send_telegram_message")
    def test_sends_no_overdue_message_when_none(self, mock_send, book, user):
        Borrowing.objects.create(
            expected_return_date=timezone.now().date() + datetime.timedelta(days=5),
            book=book,
            user=user,
        )

        check_overdue_borrowings()

        mock_send.assert_called_once_with("No borrowings overdue today!")

    @patch("notifications.tasks.send_telegram_message")
    def test_sends_message_for_overdue_borrowing(self, mock_send, book, user):
        borrowing = Borrowing.objects.create(
            expected_return_date=timezone.now().date() + datetime.timedelta(days=5),
            book=book,
            user=user,
        )
        Borrowing.objects.filter(pk=borrowing.pk).update(
            borrow_date=timezone.now().date() - datetime.timedelta(days=10),
            expected_return_date=timezone.now().date() - datetime.timedelta(days=1),
        )

        check_overdue_borrowings()

        mock_send.assert_called_once()
        assert "Overdue" in mock_send.call_args[0][0]

    @patch("notifications.tasks.send_telegram_message")
    def test_returned_borrowing_not_flagged_as_overdue(self, mock_send, book, user):
        borrowing = Borrowing.objects.create(
            expected_return_date=timezone.now().date() + datetime.timedelta(days=5),
            book=book,
            user=user,
        )
        Borrowing.objects.filter(pk=borrowing.pk).update(
            borrow_date=timezone.now().date() - datetime.timedelta(days=10),
            expected_return_date=timezone.now().date() - datetime.timedelta(days=1),
            actual_return_date=timezone.now().date(),
        )

        check_overdue_borrowings()

        mock_send.assert_called_once_with("No borrowings overdue today!")
