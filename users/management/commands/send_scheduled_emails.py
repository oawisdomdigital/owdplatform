print("Loading send_scheduled_emails command")

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from users.models import ScheduledMessage, Subscriber

class Command(BaseCommand):
    help = 'Send scheduled emails'

    def handle(self, *args, **kwargs):
        print("Executing send_scheduled_emails command")
        now = timezone.now()
        messages = ScheduledMessage.objects.filter(sent=False, scheduled_time__lte=now)
        subscribers = Subscriber.objects.all()

        for message in messages:
            for subscriber in subscribers:
                send_mail(
                    subject=message.subject,
                    message=message.message,
                    from_email='oawisdomdigitalfirm@gmail.com',
                    recipient_list=[subscriber.email],
                )
            message.sent = True
            message.save()

        self.stdout.write(self.style.SUCCESS('Successfully sent scheduled emails'))
