from django.contrib import admin
from .models import Profile, Contact, Subscriber, ScheduledMessage, EmailSettings
from django.contrib import admin
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.html import format_html
from django.contrib import messages
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
import threading
from django.conf import settings
from .models import EmailAllUsers, User
import logging

# Create a logger instance
logger = logging.getLogger(__name__)

@admin.register(EmailAllUsers)
class EmailAllUsersAdmin(admin.ModelAdmin):
    list_display = ['subject', 'sent_at', 'broadcast']
    actions = ['send_email_to_all_users']

    def send_email_to_all_users(self, request, queryset):
        # Ensure that only one email object is selected at a time
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one email to send.", level=messages.ERROR)
            return

        email = queryset.first()
        users = User.objects.all()
        recipient_list = [user.email for user in users if user.email]

        if not recipient_list:
            self.message_user(request, "No users with a valid email address found.", level=messages.WARNING)
            return

        # Render the email content using the base_email.html template
        email_body = render_to_string('base_email.html', {
            'email_subject': email.subject,
            'email_content': email.message,
            'current_year': timezone.now().year,
        })

        # Send emails one by one and track success/failure
        failed_recipients = []
        success_count = 0

        for recipient in recipient_list:
            try:
                send_mail(
                    email.subject,
                    "",  # Empty text message
                    settings.DEFAULT_FROM_EMAIL,  # Sender's email
                    [recipient],
                    html_message=email_body,  # HTML email content
                )
                success_count += 1
            except Exception as e:
                failed_recipients.append(recipient)
                logger.error(f"Failed to send email to {recipient}: {e}")

        # Update the email object to mark it as broadcasted
        if success_count > 0:
            email.broadcast = True
            email.save()

        # Inform the admin user about the result
        if failed_recipients:
            self.message_user(
                request,
                f"Emails sent to {success_count} users. Failed to send to {len(failed_recipients)} users.",
                level=messages.WARNING,
            )
        else:
            self.message_user(request, f"Emails sent successfully to all {success_count} users.")

    send_email_to_all_users.short_description = "Send selected email to all users"

@admin.register(EmailSettings)
class EmailSettingsAdmin(admin.ModelAdmin):
    list_display = ['email_host_user', 'email_host', 'email_port']

@admin.action(description='Send scheduled emails')
def send_scheduled_emails(modeladmin, request, queryset):
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

    modeladmin.message_user(request, "Scheduled emails have been sent successfully")

class ScheduledMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'scheduled_time', 'sent')
    actions = [send_scheduled_emails]

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_verified', 'referral_code')
    search_fields = ('user__username', 'bio', 'referral_code')

class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject')
    search_fields = ('name', 'email', 'subject')

class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')
    search_fields = ('email',)
    list_filter = ('subscribed_at',)

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False

class UserAdmin(admin.ModelAdmin):
    inlines = [ProfileInline]

class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_verified', 'referral_code']
    search_fields = ['user__username', 'referral_code']

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)

    def subscribed_to(self, obj):
        return ", ".join([user.username for user in obj.subscribed_to.all()])

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'subscribed_to')

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(Subscriber, SubscriberAdmin)
admin.site.register(ScheduledMessage, ScheduledMessageAdmin)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
