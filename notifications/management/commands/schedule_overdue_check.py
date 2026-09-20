from django.core.management.base import BaseCommand
from django_q.models import Schedule
from django_q.tasks import schedule


class Command(BaseCommand):
    def handle(self, *args, **options):
        if not Schedule.objects.filter(
            func="notifications.tasks.check_overdue_borrowings"
        ).exists():
            schedule(
                "notifications.tasks.check_overdue_borrowings",
                schedule_type=Schedule.DAILY,
                name="Check overdue borrowings",
            )
            self.stdout.write(self.style.SUCCESS("Schedule created"))
        else:
            self.stdout.write("Schedule already exists")
