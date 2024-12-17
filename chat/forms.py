from django import forms
import json
from .models import Room, Membership, Message


class GroupCreationForm(forms.ModelForm):
    PRIVACY_CHOICES = [
        ("everyone", "Everyone"),
        ("admin_approval", "Admin approval"),
    ]

    privacy_settings = forms.ChoiceField(
        choices=PRIVACY_CHOICES,
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    group_guidelines = forms.CharField(
        widget=forms.Textarea(
            attrs={"placeholder": "Enter group guidelines", "class": "form-control"}
        ),
        required=False,
    )

    class Meta:
        model = Room
        fields = [
            "group_name",
            "group_description",
            "group_image",
            "privacy_settings",
            "group_guidelines",
        ]
        widgets = {
            "group_name": forms.TextInput(attrs={"class": "form-control"}),
            "group_description": forms.Textarea(attrs={"class": "form-control"}),
            "group_image": forms.FileInput(attrs={"class": "form-control"}),
        }



class RoomForm(forms.ModelForm):
    PRIVACY_CHOICES = [
        ("everyone", "Everyone"),
        ("admin_approval", "Admin approval"),
    ]

    privacy_settings = forms.ChoiceField(
        choices=PRIVACY_CHOICES,
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    group_guidelines = forms.CharField(
        widget=forms.Textarea(attrs={"placeholder": "Enter group guidelines"}),
        required=False,
    )

    class Meta:
        model = Room
        fields = [
            "group_name",
            "group_description",
            "group_image",
            "privacy_settings",
            "group_guidelines",
        ]


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["content", "is_reply", "reply_to"]
