from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile
from django.contrib.auth.signals import user_logged_in
from django.core.mail import send_mail
from django.conf import settings
import logging
logger = logging.getLogger(__name__)
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage
from .file_utils import delete_file_from_storage
import threading
from django.template.loader import render_to_string
from django.utils import timezone


logger = logging.getLogger(__name__)

@receiver(post_delete)
def delete_files(sender, instance, **kwargs):
    """Deletes files from storage when a model instance is deleted."""
    # Iterate through all fields in the model
    for field in instance._meta.fields:
        # Check if the field is a FileField or ImageField
        if hasattr(field, 'upload_to'):
            file_field = getattr(instance, field.name)
            if file_field and file_field.name:
                delete_file_from_storage(file_field.name)



@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.user_profile.save()


logger = logging.getLogger(__name__)

@receiver(user_logged_in)
def send_welcome_email(sender, user, request, **kwargs):
    # Prepare email subject and content
    email_subject = "Login Successful!"
    email_content = (
        "Welcome to OWD, your one-stop destination for all digital solutions. "
        "Dive in and explore our comprehensive range of services designed to meet your every need.  "
        "Our services includes: "
        "Copywriting, "
        "Books & Project Typing,  "
        "Web Development, "
        "Thousands Of Digital Materials For Sale, "
        "Sponsored Ads Campaign, "
        "Integrate AI Chat Support System In Your Website or App, "
        "Data Purchase, "
        "Register Your Company/Organization with CAC, "
        "Domain Name Registration & Hosting, "
        "Digital Resources, "
        "Apps & Games"
            )

    # Render the email template
    email_body = render_to_string('base_email.html', {
        'email_subject': email_subject,
        'email_content': email_content,
        'current_year': timezone.now().year,
    })

    # Define the asynchronous email sending function
    def send_email_async():
        try:
            send_mail(
                subject=email_subject,
                message="",  # Empty text message
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=email_body,  # HTML email content
            )
            logger.info(f"Welcome email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {e}")

    # Start the asynchronous email thread
    threading.Thread(target=send_email_async).start()