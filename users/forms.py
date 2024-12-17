from django import forms
from django.contrib.auth.models import User
from .models import Profile, Contact, Subscriber, ScheduledMessage
from django.contrib.auth.forms import UserCreationForm


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ["user", "coins", "is_verified"]  # Exclude is_verified field


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']


class SubscriberForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ["email"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if Subscriber.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already subscribed.")
        return email


class ScheduledMessageForm(forms.ModelForm):
    class Meta:
        model = ScheduledMessage
        fields = ['subject', 'message', 'scheduled_time']


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()
    whatsapp_number = forms.CharField(
        max_length=15,
        required=False,
        help_text="Enter your WhatsApp number.",
    )
    referral_code = forms.CharField(
        max_length=12,
        required=False,
        help_text="Enter a referral code if you have one.",
    )
    device_token = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "whatsapp_number", "referral_code", "device_token"]

    # Adding email existence validation
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_referral_code(self):
        referral_code = self.cleaned_data.get("referral_code")
        if referral_code and not Profile.objects.filter(referral_code=referral_code).exists():
            raise forms.ValidationError("Invalid referral code.")
        return referral_code



class NameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']

class UsernameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']

class EmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']

class BirthdayForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['birthday']  # Ensure you have a birthday field in your User model or extended user profile model

class PasswordForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput())
    new_password = forms.CharField(widget=forms.PasswordInput())
    new_password_confirm = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        new_password_confirm = cleaned_data.get("new_password_confirm")

        if new_password and new_password_confirm:
            if new_password != new_password_confirm:
                raise forms.ValidationError("New passwords do not match")
