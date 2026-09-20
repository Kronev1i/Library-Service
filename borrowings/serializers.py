from rest_framework import serializers
from notifications.telegram import send_telegram_message
from books.serializers import BookSerializer
from borrowings.models import Borrowing


class BorrowingListSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source="book.title", read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book_title",
        )


class BorrowingDetailSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )


class BorrowingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "expected_return_date", "book")

    def validate_book(self, value):
        if value.inventory == 0:
            raise serializers.ValidationError(
                f"Book '{value.title}' is out of stock."
            )
        return value

    def create(self, validated_data):
        book = validated_data["book"]
        book.inventory -= 1
        book.save()

        user = self.context["request"].user
        borrowing = Borrowing.objects.create(user=user, **validated_data)

        send_telegram_message(
            f"📚 New borrowing created!\n"
            f"Book: {book.title}\n"
            f"User: {user.email}\n"
            f"Expected return: {borrowing.expected_return_date}"
        )

        return borrowing
