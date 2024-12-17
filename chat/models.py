from django.contrib.auth.models import User
from django.db import models
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from users.models import Profile
from django.urls import reverse
from django.utils.crypto import get_random_string
import os
from django.contrib.auth import get_user_model
import json

class ChatFile(models.Model):
    file = models.FileField(upload_to='chats/')

    def delete(self, *args, **kwargs):
        if self.file and os.path.isfile(self.file.path):
            os.remove(self.file.path)
        super().delete(*args, **kwargs)


class Room(models.Model):
    is_group = models.BooleanField(default=False)
    group_name = models.CharField(max_length=255, null=True, blank=True)
    group_description = models.TextField(null=True, blank=True)
    group_image = models.ImageField(upload_to="group_images/", null=True, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_rooms", null=True
    )
    invite_link = models.URLField(null=True, blank=True)
    privacy_settings = models.JSONField(default=dict)
    group_guidelines = models.TextField(null=True, blank=True)
    def get_absolute_url(self):
        return reverse("room", args=[self.id])



class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_reply = models.BooleanField(default=False)
    reply_to = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="replies"
    )
    is_forwarded = models.BooleanField(default=False)
    forwarded_from = models.CharField(max_length=255, null=True, blank=True)
    read = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    seen_by = models.ManyToManyField(User, related_name='seen_messages', blank=True)
    
    reactions = models.CharField(max_length=1024, default='{}', blank=True)  # Store reactions as a JSON string

    def add_reaction(self, user, emoji):
        """Add or update the user's reaction for this message."""
        reactions_dict = json.loads(self.reactions)

        # First, remove any existing reaction by the user
        for existing_emoji in list(reactions_dict.keys()):
            if user.id in reactions_dict[existing_emoji]:
                reactions_dict[existing_emoji].remove(user.id)
                if not reactions_dict[existing_emoji]:  # Remove the emoji if no users are left
                    del reactions_dict[existing_emoji]

        # Now add the new emoji reaction
        if emoji not in reactions_dict:
            reactions_dict[emoji] = []

        reactions_dict[emoji].append(user.id)  # Add user ID to the new emoji reaction

        self.reactions = json.dumps(reactions_dict)
        self.save()

    def get_reactions(self):
        """Get a dictionary of reactions and their user count."""
        reactions_dict = json.loads(self.reactions)
        return {emoji: len(user_ids) for emoji, user_ids in reactions_dict.items()}



class MessageFile(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='message_files/')

    def __str__(self):
        return f"File for message {self.message.id}"

class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    mute_notifications = models.BooleanField(default=False)
    custom_notification_tone = models.CharField(max_length=255, null=True, blank=True)
    has_received_notification = models.BooleanField(default=False)


class GroupJoinRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, default="Pending"
    )  # Status could be Pending, Accepted, or Rejected

    def __str__(self):
        return f"Request from {self.user} to join {self.room}"


class PrivateChat(models.Model):
    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="user1_chats", on_delete=models.CASCADE
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="user2_chats", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"Chat between {self.user1.username} and {self.user2.username}"

class PrivateChatMessage(models.Model):
    chat = models.ForeignKey(
        PrivateChat, related_name="messages", on_delete=models.CASCADE
    )
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to="private_chat_files/", null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    is_reply = models.BooleanField(default=False)
    reply_to = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="replies"
    )
    is_forwarded = models.BooleanField(default=False)
    forwarded_from = models.CharField(max_length=255, null=True, blank=True)
    is_pinned = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} in chat {self.chat.id}"

    class Meta:
        ordering = ['timestamp']


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="notifications", on_delete=models.CASCADE
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="sent_notifications",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    sender_profile_image = models.ImageField(
        upload_to="profile_images/", null=True, blank=True
    )
    chat = models.ForeignKey(
        "PrivateChat",
        related_name="notifications",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    is_broadcast = models.BooleanField(default=False)
    join_request = models.ForeignKey(
        "GroupJoinRequest",
        related_name="notifications",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )


class RoomInvite(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    invite_code = models.CharField(max_length=10, unique=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = get_random_string(10)
        super().save(*args, **kwargs)


User = get_user_model()

class TypingStatus(models.Model):
    chat = models.ForeignKey('PrivateChat', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # The user who should see the typing status
    is_typing = models.BooleanField(default=False)
    last_updated = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} typing in chat {self.chat.id}"
    
