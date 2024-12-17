from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Room,
    Message,
    PrivateChat,
    PrivateChatMessage,
    Notification,
    User,
    Membership,
    GroupJoinRequest,
)


class MembershipAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "room",
        "is_admin",
        "joined_at",
        "mute_notifications",
        "custom_notification_tone",
    )
    list_filter = ("room", "is_admin", "joined_at")
    search_fields = ("user__username", "room__group_name")


class GroupJoinRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "room", "created_at", "status")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "room__group_name")


@admin.register(PrivateChat)
class PrivateChatAdmin(admin.ModelAdmin):
    list_display = ("id", "user1", "user2")  # Removed created_at
    search_fields = ("user1__username", "user2__username")


@admin.register(PrivateChatMessage)
class PrivateChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "chat", "sender", "message", "file", "timestamp")
    search_fields = ("message", "sender__username", "chat__id")
    list_filter = ("timestamp", "chat")


class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "message",
        "is_read",
        "timestamp",
        "display_sender_profile_image",
    )
    list_filter = ("is_read", "timestamp")
    search_fields = ("user__username", "message")
    readonly_fields = ("timestamp",)  # Make timestamp read-only

    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read."""
        updated_count = queryset.update(is_read=True)
        self.message_user(request, f"{updated_count} notifications marked as read.")

    mark_as_read.short_description = "Mark selected notifications as read"

    def display_sender_profile_image(self, obj):
        """Display the sender's profile image in the admin list view."""
        if obj.sender:
            profile = getattr(obj.sender, "user_profile", None)
            if profile and profile.profile_image:
                return format_html(
                    '<img src="{}" width="50" height="50" style="border-radius:50%;" />',
                    profile.profile_image.url,
                )
        return "No Image"

    display_sender_profile_image.short_description = "Sender Profile Image"

    @admin.action(description="Send notification to all users")
    def send_notification_to_all(self, request, queryset):
        for notification in queryset:
            users = User.objects.all()
            for user in users:
                Notification.objects.create(
                    user=user,
                    message=notification.message,
                    sender=notification.sender,
                    sender_profile_image=notification.sender_profile_image,
                    is_broadcast=True,  # Mark it as a broadcast notification
                )

    actions = [mark_as_read, send_notification_to_all]


admin.site.register(Membership, MembershipAdmin)
admin.site.register(GroupJoinRequest, GroupJoinRequestAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Room)
admin.site.register(Message)
