from django.shortcuts import render, redirect, get_object_or_404
from django.http import (
    HttpResponse,
    JsonResponse,
    HttpResponseForbidden,
    HttpResponseNotFound,
)
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from chat.models import (
    Room,
    Message,
    PrivateChat,
    PrivateChatMessage,
    Notification,
    Membership,
    GroupJoinRequest,
    RoomInvite,
    TypingStatus,
    MessageFile,
)
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.files.storage import default_storage
from django.urls import reverse
import os
from users.models import Profile
from .forms import RoomForm, GroupCreationForm
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import threading
from django.core.mail import send_mail
from django.conf import settings
import logging
from threading import Thread

logger = logging.getLogger(__name__)

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import PrivateChat, TypingStatus
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.generic import DetailView
from django.db.models import F
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(['POST'])
def react_to_message(request, message_id):
    emoji = request.data.get('reaction')

    if emoji:
        try:
            message = Message.objects.get(id=message_id)
            message.add_reaction(request.user, emoji)  # Add the reaction using the model method

            return Response({'status': 'success', 'reaction': emoji}, status=status.HTTP_200_OK)

        except Message.DoesNotExist:
            return Response({'status': 'error', 'message': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)

    return Response({'status': 'error', 'message': 'No emoji provided'}, status=status.HTTP_400_BAD_REQUEST)

@login_required(login_url='/users/register/')
@csrf_exempt
@require_POST
def notify_typing(request, chat_id):
    """Notify that the user is typing in a private chat"""
    is_typing = request.POST.get('typing') == 'true'
    chat = get_object_or_404(PrivateChat, id=chat_id)

    # Ensure the user is part of the chat
    if request.user not in [chat.user1, chat.user2]:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    # Update or create the typing status for the current user
    TypingStatus.objects.update_or_create(
        chat=chat,
        user=request.user,  # Update for the user who is typing
        defaults={
            'is_typing': is_typing,
            'last_updated': timezone.now() if is_typing else None
        }
    )

    return JsonResponse({'status': 'success'})

@login_required(login_url='/users/register/')
def check_typing_status(request, chat_id):
    """Check if the other user is typing in the private chat"""
    chat = get_object_or_404(PrivateChat, id=chat_id)

    # Ensure the user is part of the chat
    if request.user not in [chat.user1, chat.user2]:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    # Get the other user in the chat
    other_user = chat.user2 if request.user == chat.user1 else chat.user1

    # Check the typing status of the other user
    try:
        typing_status = TypingStatus.objects.get(chat=chat, user=other_user)

        # Check if the typing status was updated recently (within 5 seconds)
        if typing_status.is_typing and typing_status.last_updated:
            now = timezone.now()
            if (now - typing_status.last_updated).total_seconds() < 5:
                return JsonResponse({'is_typing': True})

    except TypingStatus.DoesNotExist:
        pass

    return JsonResponse({'is_typing': False})



@login_required(login_url='/users/register/')
def get_private_messages(request, chat_id):
    chat = get_object_or_404(PrivateChat, id=chat_id)

    # Check if the user is part of the chat
    if request.user not in [chat.user1, chat.user2]:
        return JsonResponse(
            {"error": "You do not have permission to view messages in this chat."},
            status=403,
        )

    # Fetch messages, including reply context
    messages = chat.messages.order_by("timestamp").values(
        "id",
        "sender__username",
        "message",
        "file",
        "timestamp",
        "read",
        "reply_to",  # Reply ID if the message is a reply
        "reply_to__message",  # Original message text (for replies)
        "reply_to__sender__username"  # Sender of the original message
    )

    return JsonResponse({"messages": list(messages)})



MAX_MESSAGES_PER_CHAT = 15  # Set the maximum number of messages allowed in a private chat

@login_required(login_url='/users/register/')
@csrf_exempt
@require_POST
def send_private_message(request):
    chat_id = request.POST.get("chat_id")
    message_content = request.POST.get("message")
    files = request.FILES.getlist("files")  # Get list of files
    reply_to = request.POST.get("reply_to")  # Get the ID of the message being replied to

    chat = get_object_or_404(PrivateChat, id=chat_id)

    # Ensure user is part of the chat
    if request.user not in [chat.user1, chat.user2]:
        return JsonResponse(
            {"error": "You do not have permission to send messages in this chat."},
            status=403,
        )

    # Create new message
    message = PrivateChatMessage.objects.create(
        chat=chat,
        sender=request.user,
        message=message_content,
        reply_to_id=reply_to if reply_to else None  # Handle reply
    )

    # Save files, if any
    file_urls = []
    for file in files:
        saved_path = default_storage.save(f"private_chat_files/{file.name}", file)
        file_url = default_storage.url(saved_path)
        message.file = saved_path
        message.save()
        file_urls.append(file_url)

    # Delete old messages if the chat has more than MAX_MESSAGES_PER_CHAT
    messages_in_chat = PrivateChatMessage.objects.filter(chat=chat).order_by('timestamp')
    if messages_in_chat.count() > MAX_MESSAGES_PER_CHAT:
        # Get the excess messages (first query)
        excess_messages = messages_in_chat[:messages_in_chat.count() - MAX_MESSAGES_PER_CHAT]

        # Fetch the IDs of excess messages to delete (second query)
        excess_message_ids = [msg.id for msg in excess_messages]

        # Delete the excess messages by their IDs
        PrivateChatMessage.objects.filter(id__in=excess_message_ids).delete()

    # Notify the other user via email if applicable
    other_user = chat.user2 if request.user == chat.user1 else chat.user1

    # Check if a notification for the same chat and sender already exists
    existing_notification = Notification.objects.filter(
        user=other_user,
        sender=request.user,
        message__contains=f"New message from <a href='/private_chat/{chat.id}/'>{request.user.username}</a>"
    ).exists()

    if not existing_notification:
        # If no existing notification, create a new one
        profile_image_url = (
            other_user.profile.user_profile.profile_image.url
            if hasattr(other_user, "profile") and hasattr(other_user.profile, "user_profile")
            else ""
        )

        Notification.objects.create(
            user=other_user,
            message=f"New message from <a href='/private_chat/{chat.id}/'>{request.user.username}</a>",
            sender=request.user,
            sender_profile_image=profile_image_url,
        )

        # Prepare email content using base_email.html
        email_subject = f"New Message from {request.user.username}"
        email_content = f"You have a new message in your personal chat from {request.user.username}."

        # Render the email template
        email_body = render_to_string('base_email.html', {
            'email_subject': email_subject,
            'email_content': email_content,
            'current_year': timezone.now().year,
        })

        # Asynchronous email sending function
        def send_email_async():
            try:
                send_mail(
                    subject=email_subject,
                    message="",  # Empty plain text message
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[other_user.email],
                    html_message=email_body,  # HTML email content
                )
            except Exception as e:
                logger.error(f"Failed to send chat email to {other_user.email}: {e}")

        # Start email sending in a separate thread
        threading.Thread(target=send_email_async).start()

    # Return the message and reply context
    return JsonResponse({
        "status": "success",
        "message_id": message.id,
        "file_urls": file_urls,
        "reply_to_message": message.reply_to.message if message.reply_to else None
    })



@login_required(login_url='/users/register/')
def create_private_chat(request, user_id):
    user2 = get_object_or_404(User, id=user_id)
    user1 = request.user

    if user1 == user2:
        return HttpResponseForbidden("You cannot chat with yourself.")

    # Ensure the smaller user ID comes first for consistency
    if user1.id < user2.id:
        chat, created = PrivateChat.objects.get_or_create(user1=user1, user2=user2)
    else:
        chat, created = PrivateChat.objects.get_or_create(user1=user2, user2=user1)

    # Redirect to the chat
    return redirect("private_chat", chat_id=chat.id)


def generate_invite_link(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    # Generate the invite link if not already generated
    if not room.invite_link:
        room.invite_link = request.build_absolute_uri(reverse('join_room', args=[room.id]))
        room.save()

    return JsonResponse({'invite_link': room.invite_link})

@login_required(login_url='/users/register/')
def join_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    # Check if the user is already a member of the room
    if Membership.objects.filter(user=request.user, room=room).exists():
        return redirect('room_detail', room_id=room.id) 

    # Check the room's privacy settings
    if room.privacy_settings == "admin_approval":  # Assuming privacy_settings is a JSONField with a key "requires_approval"
        # Create a join request and notify admins
        GroupJoinRequest.objects.create(user=request.user, room=room)
        notify_admins(request, room)  # Function to notify admins about the join request
        return JsonResponse(
            {
                "success": True,
                "message": "Your request to join has been submitted and is awaiting approval.",
            }
        )
    else:
        # Automatically add the user to the group
        Membership.objects.create(user=request.user, room=room, is_admin=False)

    # Redirect to the room page
    return redirect(room.get_absolute_url())

@login_required(login_url='/users/register/')
def assign_admin(request):
    if request.method == "POST":
        member_id = request.POST.get("member_id")
        membership = get_object_or_404(
            Membership, id=member_id, room__created_by=request.user
        )

        # Check if the user is already an admin
        if membership.is_admin:
            return JsonResponse(
                {"success": False, "error": "User is already an admin."}
            )

        membership.is_admin = True
        membership.save()
        return JsonResponse({"success": True, "message": "Admin role assigned."})


@login_required(login_url='/users/register/')
def revoke_admin(request):
    if request.method == "POST":
        member_id = request.POST.get("member_id")
        membership = get_object_or_404(
            Membership, id=member_id, room__created_by=request.user
        )

        # Check if the user is an admin
        if not membership.is_admin:
            return JsonResponse({"success": False, "error": "User is not an admin."})

        membership.is_admin = False
        membership.save()
        return JsonResponse({"success": True, "message": "Admin role revoked."})


@login_required(login_url='/users/register/')
def kick_member(request):
    if request.method == "POST":
        member_id = request.POST.get("member_id")
        membership = get_object_or_404(
            Membership, id=member_id, room__created_by=request.user
        )

        if membership.is_admin:
            return JsonResponse({"success": False, "error": "Cannot kick an admin."})

        membership.delete()
        return JsonResponse(
            {"success": True, "message": "Member kicked from the group."}
        )


@login_required(login_url='/users/register/')
def request_join(request):
    if request.method == "POST":
        data = json.loads(request.body)
        room_id = data.get("room_id")
        room = get_object_or_404(Room, id=room_id)

        if Membership.objects.filter(user=request.user, room=room).exists():
            return redirect('room_detail', room_id=room.id) 
        elif room.privacy_settings == "admin_approval":
            GroupJoinRequest.objects.create(user=request.user, room=room)
            notify_admins(request, room)
            return JsonResponse(
                {
                    "success": True,
                    "message": "Your request to join has been submitted and is awaiting approval.",
                }
            )
        else:
            Membership.objects.create(user=request.user, room=room, is_admin=False)
            return JsonResponse(
                {"success": True, "message": "You have been added to the group."}
            )

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


@login_required(login_url='/users/register/')
def approve_request(request, room_id, user_id):
    room = get_object_or_404(Room, id=room_id)
    user = get_object_or_404(User, id=user_id)

    # Create a membership for the user in the room
    Membership.objects.create(user=user, room=room, is_admin=False)

    # Optionally delete the join request
    GroupJoinRequest.objects.filter(user=user, room=room).delete()

    # Notify the user of approval
    Notification.objects.create(
        user=user,
        message=f"You have been approved to join the room '{room.group_name}'. <a href='{room.get_absolute_url()}'>Visit the room</a>.",
        sender=request.user,
        chat=None,
        is_broadcast=False,
    )

    messages.success(request, "Request approved and user added to the group.")
    return redirect(
        "notifications"
    )  # Redirect to the notifications page or any other relevant page


@login_required(login_url='/users/register/')
def reject_request(request, room_id, user_id):
    # Filter the join requests
    requests_to_reject = GroupJoinRequest.objects.filter(
        room_id=room_id, user_id=user_id, status="Pending"
    )

    if requests_to_reject.exists():
        request_to_reject = requests_to_reject.first()
        user = request_to_reject.user

        # Reject the request
        request_to_reject.status = "Rejected"
        request_to_reject.save()

        # Notify the user about the rejection
        Notification.objects.create(
            user=user,
            message=f"Your request to join the group '{request_to_reject.room.group_name}' has been rejected.",
            sender=request.user,
            sender_profile_image=None,  # Or provide the sender's profile image if available
            chat=None,
            is_broadcast=False,
        )

    return redirect("notifications")  # Redirect to notifications or another page


def notify_admins(request, room):
    admins = User.objects.filter(is_superuser=True)  # Adjust to your admin logic
    for admin in admins:
        profile_image_url = None
        if hasattr(admin, "profile"):
            profile_image = admin.profile.profile_image
            if profile_image:
                profile_image_url = profile_image.url

        # Create URLs for approving and rejecting the request
        approve_url = reverse(
            "approve_request", kwargs={"room_id": room.id, "user_id": request.user.id}
        )
        reject_url = reverse(
            "reject_request", kwargs={"room_id": room.id, "user_id": request.user.id}
        )

        message = (
            f"{request.user.username} has requested to join the group '{room.group_name}'. "
            f"<a href='{approve_url}'>Approve</a> | <a href='{reject_url}'>Reject</a>"
        )

        Notification.objects.create(
            user=admin,
            message=message,
            sender=request.user,
            sender_profile_image=profile_image_url,
            chat=None,
            is_broadcast=False,
        )


@login_required(login_url='/users/register/')
def leave_group(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    membership = get_object_or_404(Membership, room=room, user=request.user)
    membership.delete()
    return redirect("room_list")


@login_required(login_url='/users/register/')
def remove_member(request, room_id, user_id):
    room = get_object_or_404(Room, id=room_id)
    if Membership.objects.filter(room=room, user=request.user, is_admin=True).exists():
        membership = get_object_or_404(Membership, room=room, user_id=user_id)
        membership.delete()
    return redirect("group_members", room_id=room_id)


@login_required(login_url='/users/register/')
def create_group(request):
    if request.method == "POST":
        form = GroupCreationForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.is_group = True
            group.created_by = request.user
            group.save()
            Membership.objects.create(user=request.user, room=group, is_admin=True)
            return redirect(
                "room", room_id=group.id
            )  # Redirect to the room page after creation
        else:
            return render(
                request, "error_message.html", {"form": form, "errors": form.errors}
            )
    else:
        form = GroupCreationForm()

    return render(request, "create_group.html", {"form": form})


@login_required(login_url='/users/register/')
def edit_room(request):
    room_id = (
        request.POST.get("room_id")
        if request.method == "POST"
        else request.GET.get("room_id")
    )
    room = get_object_or_404(Room, id=room_id)

    if request.method == "POST":
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            form.save()
            return redirect("room", room_id=room.id)  # Use 'room' instead of 'group'
    else:
        form = RoomForm(instance=room)

    # Determine which privacy setting is selected
    privacy_everyone = room.privacy_settings == "everyone"
    privacy_admin_approval = room.privacy_settings == "admin_approval"

    return render(
        request,
        "edit_room.html",
        {
            "room_form": form,
            "privacy_everyone": privacy_everyone,
            "privacy_admin_approval": privacy_admin_approval,
        },
    )

@login_required(login_url='/users/register/')
def homechat(request):
    search_query = request.GET.get("search", "")
    all_rooms = Room.objects.all()
    user_profile = get_object_or_404(Profile, user=request.user)

    if search_query:
        all_rooms = all_rooms.filter(group_name__icontains=search_query)

    # Fetch memberships for the current user
    user_memberships = Membership.objects.filter(user=request.user)

    # Preprocess rooms to add a can_join flag and membership status
    for room in all_rooms:
        # Ensure privacy_settings is a dictionary
        try:
            privacy_settings = json.loads(room.privacy_settings)
        except (TypeError, json.JSONDecodeError):
            privacy_settings = {}

        # Determine if the room can be joined
        room.can_join = privacy_settings.get("who_can_join") != "everyone"

        # Check if the user is a member or admin of the room
        room.is_member = user_memberships.filter(room=room).exists()
        room.is_admin = user_memberships.filter(room=room, is_admin=True).exists()

    # Get rooms created by the user
    user_rooms = Room.objects.filter(created_by=user_profile.user)

    return render(
        request, "homechat.html", {"rooms": all_rooms, "user_rooms": user_rooms}
    )

@login_required(login_url='/users/register/')
def room(request, room_id):
    username = request.user.username
    profile_image = (
        request.user.user_profile.profile_image.url
        if request.user.user_profile.profile_image
        else None
    )
    room_details = get_object_or_404(Room, id=room_id)

    membership = Membership.objects.filter(user=request.user, room=room_details).first()
    is_member = membership is not None
    is_admin = membership.is_admin if is_member else False

    privacy_settings = room_details.privacy_settings
    if isinstance(privacy_settings, str):
        try:
            privacy_settings = json.loads(privacy_settings)
        except json.JSONDecodeError:
            privacy_settings = {}

    privacy_setting = privacy_settings.get("privacy", "")

    if privacy_setting == "admin_approval" and not is_member:
        return redirect("request_to_join_page")

    if not is_member and privacy_setting != "admin_approval":
        return HttpResponseForbidden("You do not have access to this room.")

    total_member_count = Membership.objects.filter(room=room_details).count()

    return render(
        request,
        "room.html",
        {
            "username": username,
            "profile_image": profile_image,
            "room": room_details,
            "room_details": room_details,
            "user_is_admin": is_admin,
            "members": Membership.objects.filter(room=room_details),
            "total_member_count": total_member_count,
        },
    )

class RoomDetailView(DetailView):
    model = Room
    template_name = 'room_detail.html'  # Specify your template here
    context_object_name = 'room'  # This will be the context variable in your template

    def get_queryset(self):
        return Room.objects.filter(id=self.kwargs['room_id'])


MAX_MESSAGES_PER_ROOM = 100  # Set the maximum number of messages allowed in a room

@login_required(login_url='/users/register/')
def send(request):
    if request.method == "POST":
        message_content = request.POST.get('message')
        room_id = request.POST.get('room_id')
        username = request.POST.get('username')
        reply_to_id = request.POST.get('reply_to')
        forwarded_from_id = request.POST.get('forwarded_from')

        room = Room.objects.get(id=room_id)
        user = User.objects.get(username=username)

        reply_to_message = Message.objects.get(id=reply_to_id) if reply_to_id else None

        # Create the new message
        message = Message.objects.create(
            room=room,
            user=user,
            content=message_content,
            reply_to=reply_to_message,
            forwarded_from=None
        )
        message.seen_by.add(user)

        for file in request.FILES.getlist('files'):
            MessageFile.objects.create(message=message, file=file)

        # Check the number of messages in the room
        messages_in_room = Message.objects.filter(room=room).order_by('timestamp')
        if messages_in_room.count() > MAX_MESSAGES_PER_ROOM:
            # Get the excess messages (first query)
            excess_messages = messages_in_room[:messages_in_room.count() - MAX_MESSAGES_PER_ROOM]

            # Fetch the IDs of excess messages to delete (second query)
            excess_message_ids = [msg.id for msg in excess_messages]

            # Delete the excess messages by their IDs
            Message.objects.filter(id__in=excess_message_ids).delete()

        # Notify other users who are part of the room (this part of the code remains unchanged)
        other_users = Membership.objects.filter(room=room).exclude(user=user)
        for membership in other_users:
            other_user = membership.user


            if not membership.has_received_notification:
                # Create notification
                Notification.objects.create(
                    user=other_user,
                    message=f"New message in <a href='{request.build_absolute_uri(reverse('room_detail', args=[room.id]))}'>{room.group_name or 'a room'}</a> from {user.username}",
                    sender=user,
                    sender_profile_image=user.user_profile.profile_image.url if hasattr(user, 'user_profile') and user.user_profile.profile_image else None
                )

                # Prepare the email context
                email_context = {
                    'other_user_username': other_user.username,
                    'sender_username': user.username,
                    'message_content': message_content,
                    'room_id': room.id,
                    'room_name': room.group_name or 'a room'
                }

                # Render the email content from the template
                email_subject = f"New Message in {room.group_name or 'a room'}"
                email_html_message = render_to_string('new_message_email.html', email_context)
                email_plain_message = strip_tags(email_html_message)

                # Send the email asynchronously
                def send_email_async():
                    try:
                        send_mail(
                            subject=email_subject,
                            message=email_plain_message,
                            html_message=email_html_message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[other_user.email],
                        )
                        # Update the membership record to indicate notification was sent
                        membership.has_received_notification = True
                        membership.save()  # Save the updated status
                    except Exception as e:
                        logger.error(f"Failed to send email to {other_user.email}: {e}")

                threading.Thread(target=send_email_async).start()

        return JsonResponse({"message": "Message sent successfully"})


@login_required(login_url='/users/register/')
def getMessages(request, room_id):
    try:
        room = Room.objects.get(id=room_id)
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)

    # Get pinned and non-pinned messages separately
    pinned_messages = Message.objects.filter(room=room, is_pinned=True).order_by('timestamp')
    non_pinned_messages = Message.objects.filter(room=room, is_pinned=False).order_by('timestamp')

    # Combine the lists: pinned messages first
    messages = list(pinned_messages) + list(non_pinned_messages)

    messages_with_profile = []

    for msg in messages:
        profile_image = (
            msg.user.user_profile.profile_image.url
            if hasattr(msg.user, 'user_profile') and msg.user.user_profile.profile_image
            else None
        )
        profile_url = reverse('profile', args=[msg.user.username])

        forwarded_message_content = None
        if msg.forwarded_from:
            forwarded_messages = Message.objects.filter(user__username=msg.forwarded_from)
            if forwarded_messages.exists():
                latest_forwarded_message = forwarded_messages.order_by('-timestamp').first()
                if latest_forwarded_message:
                    forwarded_message_content = latest_forwarded_message.content

        reply_to_msg = None
        if msg.reply_to:
            reply_to_msg = msg.reply_to.content

        seen_by_users = msg.seen_by.all()
        seen_by_count = seen_by_users.count()
        seen_by_usernames = [user.username for user in seen_by_users]

        reactions_data = {}
        if msg.reactions:
            reactions_data = msg.get_reactions()  # Use the `get_reactions` method

        messages_with_profile.append({
            'id': msg.id,
            'user': msg.user.username,
            'profile_image': profile_image,
            'profile_url': profile_url,
            'value': msg.content,
            'reply_to': reply_to_msg,
            'forwarded_from': msg.forwarded_from,
            'forwarded_message_content': forwarded_message_content,
            'is_pinned': msg.is_pinned,
            'date': msg.timestamp.strftime('%Y-%m-%d %H:%M'),
            'files': [file.file.url for file in msg.files.all()],
            'is_admin': request.user.is_staff,
            'reactions': reactions_data,  # Use the `get_reactions` method directly
            'seen_by_count': seen_by_count,
            'seen_by_usernames': seen_by_usernames
        })

        if request.user not in msg.seen_by.all():
            msg.seen_by.add(request.user)
            msg.save()

    return JsonResponse({'messages': messages_with_profile}, safe=False)





def seen_by(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    seen_by_users = message.seen_by.all()

    data = {
        'seen_by': [
            {
                'username': user.username,
                'profile_image': user.user_profile.profile_image.url if user.user_profile.profile_image else 'https://img.icons8.com/color/48/000000/circled-user-male-skin-type-5--v1.png'  # Adjust the path to your default image
            }
            for user in seen_by_users
        ]
    }

    return JsonResponse(data)



@login_required(login_url='/users/register/')
def delete_room(request, room_id):
    if request.method == "POST":
        room = get_object_or_404(Room, id=room_id)
        if room.created_by == request.user:
            room.delete()
            return JsonResponse({"success": True})
        else:
            return JsonResponse(
                {
                    "success": False,
                    "error": "You do not have permission to delete this room.",
                }
            )
    return JsonResponse({"success": False, "error": "Invalid request."})

def delete_chat_message(request, message_id):
    if request.method == 'POST':
        message = get_object_or_404(Message, id=message_id)

        message.delete()
        return JsonResponse({'status': 'success', 'message': 'Message deleted successfully.'})


@login_required(login_url='/users/register/')
def pinMessage(request, message_id):
    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return JsonResponse({"error": "Message not found"}, status=404)

    # Toggle pin state
    message.is_pinned = not message.is_pinned
    message.save()

    if message.is_pinned:
        return JsonResponse({"status": "Message pinned successfully"})
    else:
        return JsonResponse({"status": "Message unpinned successfully"})



@login_required(login_url='/users/register/')
@csrf_exempt
def mark_notifications_as_read(request):
    if request.method == "POST":
        notifications = Notification.objects.filter(user=request.user, is_read=False)
        notifications.update(is_read=True)
        return JsonResponse({"success": True})
    return JsonResponse({"error": "Invalid request method"}, status=400)


@login_required(login_url='/users/register/')
@csrf_exempt
def get_notifications_count(request):
    if request.method == "GET":
        notifications_count = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
        return JsonResponse({"count": notifications_count})
    return JsonResponse({"error": "Invalid request method"}, status=400)


@login_required(login_url='/users/register/')
def all_chats(request):
    chats = PrivateChat.objects.filter(user1=request.user) | PrivateChat.objects.filter(
        user2=request.user
    )

    chats_with_profiles = []
    for chat in chats:
        if chat.user1 == request.user:
            other_user = chat.user2
        else:
            other_user = chat.user1

        other_user_profile = other_user.user_profile
        profile_image_url = (
            other_user_profile.profile_image.url
            if other_user_profile.profile_image
            else "/static/default-profile-pic.png"
        )

        chats_with_profiles.append(
            {
                "chat": chat,
                "other_user": other_user,
                "profile_image_url": profile_image_url,
            }
        )

    return render(
        request, "all_chats.html", {"chats_with_profiles": chats_with_profiles}
    )


@login_required(login_url='/users/register/')
def notifications_page(request):
    # Get all notifications for the user
    notifications = (
        Notification.objects.filter(user=request.user)
        .select_related("user", "sender", "chat")
        .order_by("-timestamp")
    )

    # Prepare a list to store notification data with profile image URLs and verification status
    notifications_with_images = []
    for notification in notifications:
        # Get the profile associated with the notification sender
        sender_profile = getattr(notification.sender, "user_profile", None)
        profile_image_url = (
            sender_profile.profile_image.url
            if sender_profile and sender_profile.profile_image
            else "/static/default-profile-pic.png"
        )
        is_verified = sender_profile.is_verified if sender_profile else False

        # Initialize join_request as None
        join_request = None

        # Check if this notification is related to a join request
        if hasattr(notification, "join_request"):
            join_request_id = getattr(notification.join_request, "id", None)
            if join_request_id:
                join_request = GroupJoinRequest.objects.filter(
                    id=join_request_id
                ).first()

        # Append notification data including profile image URL, verification status, and join request details
        notifications_with_images.append(
            {
                "message": notification.message,
                "timestamp": notification.timestamp,
                "profile_image": profile_image_url,
                "is_verified": is_verified,
                "chat": notification.chat,  # Include chat if needed
                "join_request": join_request,  # Include join request details if available
            }
        )

    # Pass the notifications data to the template
    return render(
        request, "notifications.html", {"notifications": notifications_with_images}
    )


@login_required(login_url='/users/register/')
def get_private_messages(request, chat_id):
    chat = get_object_or_404(PrivateChat, id=chat_id)

    # Check if the user is part of the chat
    if request.user not in [chat.user1, chat.user2]:
        return JsonResponse(
            {"error": "You do not have permission to view messages in this chat."},
            status=403,
        )

    # Fetch messages, including reply context
    messages = chat.messages.order_by("timestamp").values(
        "id",
        "sender__username",
        "message",
        "file",
        "timestamp",
        "read",
        "reply_to",  # Reply ID if the message is a reply
        "reply_to__message"  # Original message text (for replies)
    )

    return JsonResponse({"messages": list(messages)})


@csrf_exempt
@login_required(login_url='/users/register/')
@require_POST
def mark_messages_as_read(request):
    try:
        data = json.loads(request.body)
        chat_id = data.get("chat_id")
        chat = get_object_or_404(PrivateChat, id=chat_id)
        other_user = chat.user2 if request.user == chat.user1 else chat.user1

        chat.messages.filter(sender=other_user, read=False).update(read=True)

        return JsonResponse({"success": True})
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)


@login_required(login_url='/users/register/')
def create_private_chat(request, user_id):
    user2 = get_object_or_404(User, id=user_id)
    user1 = request.user

    if user1 == user2:
        return HttpResponseForbidden("You cannot chat with yourself.")

    # Ensure the smaller user ID comes first for consistency
    if user1.id < user2.id:
        chat, created = PrivateChat.objects.get_or_create(user1=user1, user2=user2)
    else:
        chat, created = PrivateChat.objects.get_or_create(user1=user2, user2=user1)

    # Redirect to the chat
    return redirect("private_chat", chat_id=chat.id)


@login_required(login_url='/users/register/')
def private_chat_view(request, chat_id):
    chat = get_object_or_404(PrivateChat, id=chat_id)

    # Ensure the current user is part of the chat
    if request.user not in [chat.user1, chat.user2]:
        return HttpResponseForbidden("You are not allowed to view this chat.")

    messages = PrivateChatMessage.objects.filter(chat=chat)

    other_user = chat.user1 if chat.user2 == request.user else chat.user2

    return render(request, 'private_chat.html', {
        'chat': chat,
        'other_user': other_user,
        'messages': messages
    })

@login_required(login_url='/users/register/')
@csrf_exempt
def delete_message(request):
    if request.method == 'POST':
        message_id = request.POST.get('message_id')

        try:
            message = PrivateChatMessage.objects.get(id=message_id)
            # Add authorization check if needed (e.g., if the user is the sender)
            message.delete()

            return JsonResponse({'status': 'success'})
        except PrivateChatMessage.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Message not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@login_required(login_url='/users/register/')
def clear_all_notifications(request):
    if request.method == "POST":
        # Delete all notifications for the logged-in user
        notifications = Notification.objects.filter(user=request.user)
        notifications.delete()

        # Reset the `has_received_notification` flag for all memberships of the user
        memberships = Membership.objects.filter(user=request.user, has_received_notification=True)
        memberships.update(has_received_notification=False)  # Set the flag to False

        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error", "message": "Invalid request"})
