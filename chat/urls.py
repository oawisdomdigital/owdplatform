from django.urls import path
from . import views

urlpatterns = [
    path('addReaction/<int:message_id>/', views.react_to_message, name='react_to_message'),

    # URL for retrieving reactions for a specific message
    path('rooms/<int:room_id>/', views.RoomDetailView.as_view(), name='room_detail'),
    path('seenBy/<int:message_id>/', views.seen_by, name='seen_by'),
    path('deleteChatMessage/<int:message_id>/', views.delete_chat_message, name='delete_chat_message'),
    path('pinMessage/<int:message_id>/', views.pinMessage, name='pin_message'),
    path('deleteMessage/<int:message_id>/', views.delete_message, name='delete_message'),
    path('private_chat/notify_typing/<int:chat_id>/', views.notify_typing, name='notify_typing'),

    # URL to check if the other user is typing
    path('private_chat/check_typing_status/<int:chat_id>/', views.check_typing_status, name='check_typing_status'),
    path('private_chat/delete_message/', views.delete_message, name='delete_message'),
    path('private_chat/<int:chat_id>/', views.private_chat_view, name='private_chat'),
    path('generate_invite_link/<int:room_id>/', views.generate_invite_link, name='generate_invite_link'),
    path('join_room/<int:room_id>/', views.join_room, name='join_room'),
    path(
        "approve-request/<int:room_id>/<int:user_id>/",
        views.approve_request,
        name="approve_request",
    ),
    path(
        "reject-request/<int:room_id>/<int:user_id>/",
        views.reject_request,
        name="reject_request",
    ),
    path("request-to-join/", views.request_join, name="request-to-join"),
    path("leave_group/<int:room_id>/", views.leave_group, name="leave_group"),
    path(
        "remove_member/<int:room_id>/<int:user_id>/",
        views.remove_member,
        name="remove_member",
    ),
    path("create_group/", views.create_group, name="create_group"),
    path("edit_room/", views.edit_room, name="edit_room"),
    path("homechat/", views.homechat, name="homechat"),
    path("delete_room/<int:room_id>/", views.delete_room, name="delete_room"),
    path("room/<int:room_id>/", views.room, name="room_detail"),
    path("send/", views.send, name="send_message"),
    path("getMessages/<int:room_id>/", views.getMessages, name="get_messages"),
    # URL pattern for creating a private chat
    path(
        "create_private_chat/<int:user_id>/",
        views.create_private_chat,
        name="create_private_chat",
    ),
    path("notifications/", views.notifications_page, name="notifications"),
    path("all_chats/", views.all_chats, name="all_chats"),
    # URL pattern for viewing a private chat
    path("private_chat/<int:chat_id>/", views.private_chat_view, name="private_chat"),
    # URL pattern for sending a private message
    path(
        "private_chat/send_private_message/",
        views.send_private_message,
        name="send_private_message",
    ),
    # URL pattern for marking a message as read
    path(
        "private_chat/mark_messages_as_read/",
        views.mark_messages_as_read,
        name="mark_messages_as_read",
    ),
    # URL pattern for getting private messages
    path(
        "private_chat/get_private_messages/<int:chat_id>/",
        views.get_private_messages,
        name="get_private_messages",
    ),
    # URL pattern for getting notifications count
    path(
        "notifications/get_count/",
        views.get_notifications_count,
        name="get_notifications_count",
    ),
    # URL pattern for marking notifications as read
    path(
        "notifications/mark_as_read/",
        views.mark_notifications_as_read,
        name="mark_notifications_as_read",
    ),
    path(
        "notifications/clear_all/",
        views.clear_all_notifications,
        name="clear_all_notifications",
    ),
]
