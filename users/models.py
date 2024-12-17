from django.contrib.auth.models import User
from django.db import models
from datetime import datetime
import uuid
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random
import string

User = get_user_model()

class EmailAllUsers(models.Model):
    subject = models.CharField(max_length=255)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    broadcast = models.BooleanField(default=False)  # New field to track if the email has been sent

    def __str__(self):
        return f"Email sent on {self.sent_at}" if self.broadcast else "Email not sent yet"


class EmailSettings(models.Model):
    email_host = models.CharField(max_length=255, default='smtp.gmail.com')
    email_port = models.IntegerField(default=587)
    email_use_tls = models.BooleanField(default=True)
    email_host_user = models.EmailField()
    email_host_password = models.CharField(max_length=255)
    default_from_email = models.EmailField()

    def __str__(self):
        return f"Email Settings - {self.email_host_user}"

class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()

    def __str__(self):
        return self.name

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

class ScheduledMessage(models.Model):
    subject = models.CharField(max_length=255)
    message = models.TextField()
    scheduled_time = models.DateTimeField()
    sent = models.BooleanField(default=False)

    def __str__(self):
        return self.subject


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="user_profile"
    )
    profile_image = models.ImageField(
        upload_to="profile_images/", blank=True, null=True
    )
    cover_image = models.ImageField(upload_to="cover_images/", blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    whatsapp_number = models.CharField(max_length=15, blank=True, null=True)
    subscribers = models.ManyToManyField(
        User, related_name="profile_subscriptions", blank=True
    )
    is_verified = models.BooleanField(default=False)
    referral_code = models.CharField(max_length=12, unique=True, blank=True, null=True)
    coins = models.IntegerField(default=0)
    fcm_token = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    def generate_referral_code(self):
        return uuid.uuid4().hex[:12]


class OTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return self.created_at >= timezone.now() - timedelta(
            minutes=10
        )  # OTP valid for 10 minutes


def generate_otp():
    return "".join(random.choices(string.digits, k=6))


