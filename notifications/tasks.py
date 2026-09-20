from datetime import date

from borrowings.models import Borrowing
from notifications.telegram import send_telegram_message


def check_overdue_borrowings():
    overdue = Borrowing.objects.filter(
        expected_return_date__lte=date.today(),
        actual_return_date__isnull=True,
    ).select_related("book", "user")

    if not overdue.exists():
        send_telegram_message("No borrowings overdue today!")
        return

    for borrowing in overdue:
        send_telegram_message(
            f"⚠️ Overdue borrowing!\n"
            f"Book: {borrowing.book.title}\n"
            f"User: {borrowing.user.email}\n"
            f"Expected return: {borrowing.expected_return_date}"
        )
