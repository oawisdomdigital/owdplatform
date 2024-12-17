from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.contrib.auth import logout
from django.http import HttpResponse
from django.views.generic.base import View
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from django.urls import reverse
import json
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from .forms import UserCreationForm, ProfileForm, UserRegistrationForm, ContactForm, SubscriberForm, NameForm, UsernameForm, EmailForm, BirthdayForm, PasswordForm, ContactForm
from .models import Profile, Subscriber
import threading
from posts.forms import (
    BlogPostForm,
    BlogPost,
    Comment,
    MarketplaceItemForm,
    MarketplaceItemImageForm,
)
from posts.models import (
    Subscription,
    MarketplaceEntry,
    MarketplaceItem,
    MarketplaceItemImage,
    Wishlist,
    Cart,
)
from django.db.models import Q
import random
import string
from django.utils import timezone
from datetime import timedelta
from .models import User, OTP
from chat.models import PrivateChatMessage, PrivateChat, Notification
from django.contrib.auth.decorators import user_passes_test
from django.utils.html import format_html
from django.template.loader import render_to_string
import logging
logger = logging.getLogger(__name__)



def admin_check(user):
    return user.is_staff  # Define your own admin check logic

@user_passes_test(admin_check)
def approve_post(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    post.is_approved = True
    post.save()

    # Notify the post author about approval
    Notification.objects.create(
        user=post.author,
        message=f"Your post '{post.title}' meets our community guidelines and is now published on the home page.",
    )

    # Prepare the email content
    email_subject = "Your post is now live on the home page!"
    email_content = f"Your post '{post.title}' meets our community guidelines and is now published on the home page."

    # Render the email content using base_email.html
    email_body = render_to_string('base_email.html', {
        'email_subject': email_subject,
        'email_content': email_content,
        'current_year': timezone.now().year,
    })

    # Send email asynchronously
    def send_email_async():
        try:
            send_mail(
                subject=email_subject,
                message="",  # Empty text message
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[post.author.email],
                html_message=email_body,  # HTML email content
            )
        except Exception as e:
            logger.error(f"Failed to send email to {post.author.email}: {e}")

    threading.Thread(target=send_email_async).start()

    return redirect('home')  # Redirect to home or any other page


@user_passes_test(admin_check)
def reject_post(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    post.delete()

    # URL to the community guidelines page
    guidelines_url = request.build_absolute_uri('/community-guidelines/')

    # Notify the post author about rejection
    Notification.objects.create(
        user=post.author,
        message=format_html(
            "Your post '{title}' does not meet our community guidelines and has been removed. Please refer to our community guidelines. <a href='{url}'>Community Guidelines</a>",
            title=post.title,
            url=guidelines_url
        ),
    )

    # Prepare the email content
    email_subject = "Your post has been removed"
    email_content = f"Your post '{post.title}' does not meet our community guidelines and has been removed. Please refer to our community guidelines here: {guidelines_url}"

    # Render the email content using base_email.html
    email_body = render_to_string('base_email.html', {
        'email_subject': email_subject,
        'email_content': email_content,
        'current_year': timezone.now().year,
    })

    # Send email asynchronously
    def send_email_async():
        try:
            send_mail(
                subject=email_subject,
                message="",  # Empty text message
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[post.author.email],
                html_message=email_body,  # HTML email content
            )
        except Exception as e:
            logger.error(f"Failed to send email to {post.author.email}: {e}")

    threading.Thread(target=send_email_async).start()

    return redirect('home')  # Redirect to home or any other page



def generate_otp():
    return "".join(random.choices(string.digits, k=6))


def login_view(request):
    if request.method == "POST":
        # Get the form values
        username_or_email = request.POST.get("username_or_email")
        login_method = request.POST.get("login_method")
        password = request.POST.get("password", None)

        # Check if the provided username_or_email is an email address
        if "@" in username_or_email:
            try:
                user = User.objects.get(email=username_or_email)
                username = user.username
            except User.DoesNotExist:
                messages.error(request, "User does not exist.")
                return render(request, "login.html")
        else:
            username = username_or_email

        # OTP Login Method
        if login_method == "otp":
            if username:
                try:
                    user = User.objects.get(username=username)
                    otp_code = generate_otp()

                    # Create or update OTP record
                    otp, created = OTP.objects.get_or_create(user=user)
                    otp.otp_code = otp_code
                    otp.created_at = timezone.now()
                    otp.save()

                    # Prepare email content
                    email_subject = "Your OTP for login"
                    email_content = f"Your OTP for login is: {otp_code}"

                    # Render the email using base_email.html
                    email_body = render_to_string('base_email.html', {
                        'email_subject': email_subject,
                        'email_content': email_content,
                        'current_year': timezone.now().year,
                    })

                    # Send OTP to user's email asynchronously
                    def send_email_async():
                        try:
                            send_mail(
                                subject=email_subject,
                                message="",  # Empty text message
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[user.email],
                                html_message=email_body,  # HTML email content
                            )
                        except Exception as e:
                            logger.error(f"Failed to send OTP email to {user.email}: {e}")

                    threading.Thread(target=send_email_async).start()

                    messages.success(request, "OTP has been sent to your email.")
                    return redirect("verify_otp", username=username)

                except User.DoesNotExist:
                    messages.error(request, "User does not exist.")
            else:
                messages.error(request, "Invalid username or email.")

        # Password Login Method
        elif login_method == "password" and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Successfully logged in.")
                return redirect("home")  # Redirect to the home page or dashboard
            else:
                messages.error(request, "Invalid username or password.")

    return render(request, "login.html")


def verify_otp_view(request, username):
    if request.method == "POST":
        otp_code = request.POST.get("otp")

        try:
            user = User.objects.get(username=username)
            otp = OTP.objects.get(user=user)

            if otp.otp_code == otp_code and otp.is_valid():
                # OTP is correct and not expired
                otp.delete()  # Remove the OTP after successful verification

                login(request, user)
                messages.success(request, "Login successful.")
                return redirect("home")  # Redirect to your desired page after login

            else:
                messages.error(request, "Invalid or expired OTP. Please try again.")

        except User.DoesNotExist:
            messages.error(request, "User does not exist.")
        except OTP.DoesNotExist:
            messages.error(request, "OTP not found.")

    return render(request, "verify_otp.html", {"username": username})

def resend_otp_view(request, username):
    user = get_object_or_404(User, username=username)

    # Generate a new OTP
    otp_code = "".join(random.choices(string.digits, k=6))
    otp, created = OTP.objects.get_or_create(user=user)
    otp.otp_code = otp_code
    otp.created_at = timezone.now()
    otp.save()

    # Prepare email content
    email_subject = "Your new OTP for login"
    email_content = f"Your new OTP for login is: {otp_code}"

    # Render the email using base_email.html
    email_body = render_to_string('base_email.html', {
        'email_subject': email_subject,
        'email_content': email_content,
        'current_year': timezone.now().year,
    })

    # Send the new OTP to the user's email asynchronously
    def send_email_async():
        try:
            send_mail(
                subject=email_subject,
                message="",  # Empty text message
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=email_body,  # HTML email content
            )
        except Exception as e:
            logger.error(f"Failed to send OTP email to {user.email}: {e}")

    threading.Thread(target=send_email_async).start()

    messages.success(request, "A new OTP has been sent to your email.")
    return redirect("verify_otp", username=username)


def send_email_async(subject, message, from_email, recipient_list):
    # Function to send email in a separate thread
    send_mail(subject, message, from_email, recipient_list)

def register(request):
    referral_code = request.GET.get("referral_code", "")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.whatsapp_number = form.cleaned_data.get("whatsapp_number")
            user.save()

            # The profile creation will be handled by signals
            profile = Profile.objects.get(user=user)
            profile.coins = 5
            profile.whatsapp_number = user.whatsapp_number  # Save WhatsApp number in Profile
            profile.save()

            # Retrieve the device token from the POST data
            device_token = request.POST.get("device_token", "")
            if device_token:
                profile.device_token = device_token
                profile.save()

            referral_code = form.cleaned_data.get("referral_code")
            if referral_code:
                try:
                    referrer_profile = Profile.objects.get(referral_code=referral_code)
                    referrer_profile.coins += 5
                    referrer_profile.save()
                    profile.coins += 5
                    profile.save()

                    # Prepare email content for referrer
                    referrer_email_subject = "You have earned 5 coins!"
                    referrer_email_content = f"You have earned 5 coins for referring {user.username}."

                    # Render the email using base_email.html for referrer
                    referrer_email_body = render_to_string('base_email.html', {
                        'email_subject': referrer_email_subject,
                        'email_content': referrer_email_content,
                        'current_year': timezone.now().year,
                    })

                    # Send email to the referrer asynchronously
                    def send_referrer_email():
                        try:
                            send_mail(
                                subject=referrer_email_subject,
                                message="",  # Empty text message
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[referrer_profile.user.email],
                                html_message=referrer_email_body,  # HTML email content
                            )
                        except Exception as e:
                            logger.error(f"Failed to send email to {referrer_profile.user.email}: {e}")

                    threading.Thread(target=send_referrer_email).start()

                    # Prepare email content for the new user
                    user_email_subject = "Welcome and congrats on earning 5 coins!"
                    user_email_content = f"You have earned 5 coins for using the referral code from {referrer_profile.user.username}."

                    # Render the email using base_email.html for the new user
                    user_email_body = render_to_string('base_email.html', {
                        'email_subject': user_email_subject,
                        'email_content': user_email_content,
                        'current_year': timezone.now().year,
                    })

                    # Send email to the new user asynchronously
                    def send_user_email():
                        try:
                            send_mail(
                                subject=user_email_subject,
                                message="",  # Empty text message
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[user.email],
                                html_message=user_email_body,  # HTML email content
                            )
                        except Exception as e:
                            logger.error(f"Failed to send email to {user.email}: {e}")

                    threading.Thread(target=send_user_email).start()

                    Notification.objects.create(
                        user=referrer_profile.user,
                        message=f"You have earned 5 coins for referring {user.username}.",
                    )
                    Notification.objects.create(
                        user=user,
                        message=f"Welcome! You have earned 5 coins for using the referral code from {referrer_profile.user.username}.",
                    )

                except Profile.DoesNotExist:
                    pass

            username = form.cleaned_data.get("username")
            messages.success(request, f"Account created for {username}!")
            return redirect("login")
    else:
        form = UserRegistrationForm(initial={"referral_code": referral_code})

    return render(request, "register.html", {"form": form})



@login_required(login_url='/users/register/')
@csrf_exempt
@require_POST
def add_post(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.is_approved = False  # Mark as not approved by default
            post.save()

            # Get the subscribers of the author's profile
            profile = Profile.objects.get(user=request.user)
            subscribers = profile.subscribers.all()

            # Create notifications and send emails to each subscriber
            for subscriber in subscribers:
                profile_image_url = (
                    request.user.user_profile.profile_image.url
                    if request.user.user_profile and request.user.user_profile.profile_image
                    else ""
                )

                # Create a notification
                Notification.objects.create(
                    user=subscriber,
                    message=f"{request.user.username} has added a new post: {post.title}",
                    sender=request.user,
                    sender_profile_image=profile_image_url,
                )

                # Prepare email content for subscriber
                email_subject = "New Post Notification"
                email_content = f"{request.user.username} has added a new post: {post.title}\n\n{post.content}"

                # Render the email using base_email.html for subscriber
                email_body = render_to_string('base_email.html', {
                    'email_subject': email_subject,
                    'email_content': email_content,
                    'current_year': timezone.now().year,
                })

                # Send email to the subscriber asynchronously
                def send_subscriber_email():
                    try:
                        send_mail(
                            subject=email_subject,
                            message="",  # Empty text message
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[subscriber.email],
                            html_message=email_body,  # HTML email content
                        )
                    except Exception as e:
                        logger.error(f"Failed to send email to {subscriber.email}: {e}")

                threading.Thread(target=send_subscriber_email).start()

            # Notify admin superusers and provide links to approve, reject, and view the post
            admins = User.objects.filter(is_staff=True)
            post_detail_url = reverse('post_detail', args=[post.id])  # Link to the post detail page

            for admin in admins:
                approve_url = reverse('approve_post', args=[post.id])
                reject_url = reverse('reject_post', args=[post.id])

                # Prepare email content for admin
                admin_email_subject = "New Post Approval Required"
                admin_email_content = (
                    f"A new post titled '{post.title}' has been created by {request.user.username}. "
                    f"Please review it.\n\n"
                    f"View post: {request.build_absolute_uri(post_detail_url)}\n"
                    f"Approve: {request.build_absolute_uri(approve_url)}\n"
                    f"Reject: {request.build_absolute_uri(reject_url)}"
                )

                # Render the email using base_email.html for admin
                admin_email_body = render_to_string('base_email.html', {
                    'email_subject': admin_email_subject,
                    'email_content': admin_email_content,
                    'current_year': timezone.now().year,
                })

                # Send email to admin asynchronously
                def send_admin_email():
                    try:
                        send_mail(
                            subject=admin_email_subject,
                            message="",  # Empty text message
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[admin.email],
                            html_message=admin_email_body,  # HTML email content
                        )
                    except Exception as e:
                        logger.error(f"Failed to send email to {admin.email}: {e}")

                threading.Thread(target=send_admin_email).start()

                # Notify admin via Django notifications
                Notification.objects.create(
                    user=admin,
                    message=format_html(
                        "New post '{title}' by {username} requires your approval. "
                        "<a href='{post_detail_url}'>View post</a> | "
                        "<a href='{approve_url}'>Approve</a> | <a href='{reject_url}'>Reject</a>",
                        title=post.title,
                        username=request.user.username,
                        post_detail_url=request.build_absolute_uri(post_detail_url),
                        approve_url=request.build_absolute_uri(approve_url),
                        reject_url=request.build_absolute_uri(reject_url),
                    ),
                    sender=request.user,
                )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Post added successfully and is pending approval.",
                    "post": {
                        "id": post.id,  # Ensure 'id' is included
                        "title": post.title,
                        "content": post.content,
                        "image_url": post.image.url if post.image else "",
                        "author": post.author.username,
                        "created_at": post.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    },
                }
            )
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)



def custom_logout_view(request):
    logout(request)
    # Add any custom code here
    return redirect('home') 

@login_required(login_url='/users/register/')
def profile_update(request):
    user = request.user
    name_form = None
    username_form = None
    email_form = None
    password_form = PasswordForm()
    birthday_form = ProfileForm(instance=user.user_profile)

    if request.method == 'POST':
        if 'first_name' in request.POST or 'last_name' in request.POST:
            name_form = NameForm(request.POST, instance=user)
            if name_form.is_valid():
                name_form.save()
                messages.success(request, 'Name updated successfully!')
                return redirect('profile', username=user.username)
        elif 'username' in request.POST:
            username_form = UsernameForm(request.POST, instance=user)
            if username_form.is_valid():
                username_form.save()
                messages.success(request, 'Username updated successfully!')
                return redirect('profile', username=user.username)
        elif 'email' in request.POST:
            email_form = EmailForm(request.POST, instance=user)
            if email_form.is_valid():
                email_form.save()
                messages.success(request, 'Email updated successfully!')
                return redirect('profile', username=user.username)
        elif 'birthday' in request.POST or 'bio' in request.POST or 'about' in request.POST or 'profile_image' in request.FILES or 'cover_image' in request.FILES:
            profile = user.user_profile  # Using the related_name 'user_profile'
            birthday_form = ProfileForm(request.POST, request.FILES, instance=profile)
            if birthday_form.is_valid():
                birthday_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('profile', username=user.username)
        elif 'current_password' in request.POST:
            password_form = PasswordForm(request.POST)
            if password_form.is_valid():
                if user.check_password(password_form.cleaned_data['current_password']):
                    new_password = password_form.cleaned_data['new_password']
                    new_password_confirm = password_form.cleaned_data['new_password_confirm']
                    if new_password == new_password_confirm:
                        user.set_password(new_password)
                        user.save()
                        update_session_auth_hash(request, user)  # Keeps the user logged in
                        messages.success(request, 'Password updated successfully!')
                    else:
                        messages.error(request, 'New passwords do not match.')
                else:
                    messages.error(request, 'Current password is incorrect.')

    return render(request, 'profile_update.html', {
        'name_form': name_form,
        'username_form': username_form,
        'email_form': email_form,
        'password_form': password_form,
        'birthday_form': birthday_form
    })


@login_required(login_url='/users/register/')
def update_profile(request):
    if request.method == "POST":
        profile = request.user.user_profile
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile_image = (
                profile.profile_image
            )  # Preserve the profile image before saving
            cover_image = profile.cover_image  # Preserve the cover image before saving
            form.save()
            profile.refresh_from_db()  # Refresh the profile to get the updated values

            data = {
                "profile_image_url": (
                    profile.profile_image.url if profile.profile_image else ""
                ),
                "cover_image_url": (
                    profile.cover_image.url if profile.cover_image else ""
                ),
                "bio": profile.bio,
                "about": profile.about,
            }
            return JsonResponse(data)
        else:
            errors = form.errors.as_json()
            return JsonResponse({"errors": errors}, status=400)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)


def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True})
        else:
            errors = form.errors.as_json()
            return JsonResponse({"success": False, "errors": errors})
    return JsonResponse({"success": False, "errors": "Invalid request"})


@csrf_exempt
def subscribe_news(request):
    if request.method == "POST":
        email = request.POST.get("email")
        if email:
            subscriber, created = Subscriber.objects.get_or_create(email=email)
            if created:
                return JsonResponse(
                    {"success": True, "message": "Subscribed successfully."}
                )
            else:
                return JsonResponse(
                    {"success": False, "message": "Already subscribed."}
                )
        else:
            return JsonResponse({"success": False, "message": "Invalid email."})
    return JsonResponse({"success": False, "message": "Invalid request."})


class DeleteProfileImageView(View):
    def post(self, request, *args, **kwargs):
        try:
            profile = (
                request.user.user_profile
            )  # Access user profile using the correct related_name
        except Profile.DoesNotExist:
            return JsonResponse({"error": "Profile does not exist."}, status=400)

        if profile.profile_image:
            profile.profile_image.delete()
            profile.profile_image = None
            profile.save()
            return JsonResponse({"message": "Profile image deleted successfully."})
        else:
            return JsonResponse({"error": "Profile image does not exist."}, status=400)


class DeleteCoverImageView(View):
    def post(self, request, *args, **kwargs):
        try:
            profile = (
                request.user.user_profile
            )  # Access user profile using the correct related_name
        except Profile.DoesNotExist:
            return JsonResponse({"error": "Profile does not exist."}, status=400)

        if profile.cover_image:
            profile.cover_image.delete()
            profile.cover_image = None
            profile.save()
            return JsonResponse({"message": "Cover image deleted successfully."})
        else:
            return JsonResponse({"error": "Cover image does not exist."}, status=400)


# In views.py
@login_required(login_url='/users/register/')
def profile(request, username):
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)
    posts = BlogPost.objects.filter(author=user).order_by("-created_at")
    subscriber_count = profile.subscribers.count()
    subscribers = profile.subscribers.all()

    # Check if the current user is subscribed to the profile user
    is_subscribed = (
        profile.subscribers.filter(id=request.user.id).exists()
        if request.user.is_authenticated
        else False
    )

    # Check if the current user is the owner of the profile
    is_current_user = request.user == user

    # Get the latest MarketplaceEntry data if multiple exist
    marketplace_entry = MarketplaceEntry.objects.filter(user=user).first()

    # Get the wishlist and cart for the user
    wishlist = Wishlist.objects.filter(user=user).first()
    cart = Cart.objects.filter(user=user).first()

    # Fetch notifications for the current user
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    notifications_count = notifications.count()

    marketplace_items = MarketplaceItem.objects.filter(user=user)

    context = {
        "profile": profile,
        "posts": posts,
        "subscriber_count": subscriber_count,
        "user": user,
        "is_subscribed": is_subscribed,
        "subscribers": subscribers,
        "is_current_user": is_current_user,
        "coins": profile.coins,
        "marketplace_entry": marketplace_entry,
        "wishlist": wishlist,
        "cart": cart,
        "notifications": notifications,
        "notifications_count": notifications_count,
        "marketplace_items": marketplace_items,
    }

    return render(request, "users/profile.html", context)


@login_required(login_url='/users/register/')
def edit_item(request, item_id):
    item = get_object_or_404(MarketplaceItem, id=item_id, user=request.user)
    images = MarketplaceItemImage.objects.filter(item=item)

    if request.method == "POST":
        item_form = MarketplaceItemForm(request.POST, instance=item)
        image_form = MarketplaceItemImageForm(request.POST, request.FILES)

        if item_form.is_valid():
            item_form.save()
            if image_form.is_valid():
                image_instance = image_form.save(commit=False)
                image_instance.item = item
                image_instance.save()
            return redirect("profile", username=request.user.username)
    else:
        item_form = MarketplaceItemForm(instance=item)
        image_form = MarketplaceItemImageForm()

    context = {
        "item_form": item_form,
        "image_form": image_form,
        "item": item,
        "images": images,
    }
    return render(request, "edit_item.html", context)

@login_required(login_url='/users/register/')
def delete_image(request, image_id):
    image = get_object_or_404(
        MarketplaceItemImage, id=image_id, item__user=request.user
    )
    if request.method == "DELETE":
        image.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})


@login_required(login_url='/users/register/')
def delete_item(request, item_id):
    item = get_object_or_404(MarketplaceItem, id=item_id, user=request.user)
    if request.method == "DELETE":
        item.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})


def community_guidelines(request):
    return render(request, "community_guidelines.html", {"community_guidelines": community_guidelines})
