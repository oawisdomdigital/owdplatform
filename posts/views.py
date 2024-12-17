from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import logging
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.db.models import Q
from django.views.decorators.http import require_POST, require_http_methods
from django.urls import reverse
import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.models import AnonymousUser
from django.db import transaction
import threading
from itertools import chain
from operator import attrgetter

from .models import (
    MarketplaceItem,
    Adsposts,
    DigitalMarketing,
    Coding,
    Graphics,
    CyberSecurity,
    Digital_marketing_b,
    Digital_marketing_a,
    Digital_marketing_p,
    Coding_b,
    Coding_a,
    Coding_p,
    Graphic_b,
    Graphic_a,
    Graphic_p,
    CyberSecurity_b,
    CyberSecurity_a,
    CyberSecurity_p,
    Videoediting_b,
    Videoediting_a,
    Videoediting_p,
    BusinessRegistration,
    WebsiteRequirement,
    FacebookAdRequirement,
    DomainHostingRequirement,
    Data_analysis,
    Data_analysis_b,
    Data_analysis_a,
    Data_analysis_p,
    Android_app,
    Desktop_app,
    Useful_resource,
    BlogPost,
    Comment,
    DataPurchase,
    Material,
    MotivationalBook,
    AIIntegrationRequest,
    VideoEditing,
    Subscription,
    FileUpload,
    MarketplaceEntry,
    MarketplaceItemImage,
    Wishlist,
    Cart,
    CartItem,
    SiteSetting,
)
from users.models import Profile
from .forms import (
    MessageForm,
    BusinessRegistrationForm,
    DomainHostingRequirementForm,
    FacebookAdRequirementForm,
    WebsiteRequirementForm,
    MarketplaceForm,
    MarketplaceItemForm,
    MarketplaceItemImageForm,
    BlogPostForm,
    CommentForm,
    AIIntegrationRequestForm,
    DataPurchaseForm,
    UsefulResourceForm,
)
from django.shortcuts import redirect
from django.http import JsonResponse
from .forms import WebsiteRequirementForm
from django.contrib import messages
from django.core.mail import send_mail
from chat.models import Notification
from django.conf import settings
from django.http import HttpResponseForbidden
from .models import YouTubePost, YoutubeComment
from django.utils import timezone
from django.views import View
from django.template.loader import render_to_string
from django.http import Http404
from django.views import View

logger = logging.getLogger(__name__)
import re

def ebooks(request):
    # Query all books from the database
    books = MotivationalBook.objects.all().order_by('-created_at')

    # Pass the books to the template
    return render(request, "ebooks.html", {"books": books})

def sitemap(request):
    return render(request, "sitemap.xml")

def owdservices(request):
    return render(request, "owd_services.html")


@require_POST
def save_fcm_token(request):
    user = request.user
    data = json.loads(request.body)
    fcm_token = data.get('token')

    if user.is_authenticated and fcm_token:
        user.user_profile.fcm_token = fcm_token  # Save token to profile
        user.user_profile.save()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'error': 'Invalid request or user not authenticated'}, status=400)


@login_required(login_url='/users/register/')
@login_required
def delete_youtube_comment(request, comment_id):
    if request.method == 'POST':
        comment = get_object_or_404(YoutubeComment, id=comment_id, user=request.user)

        if comment:
            comment.delete()
            return JsonResponse({'success': True})

    return JsonResponse({'error': 'Comment could not be deleted'}, status=400)


@require_POST
def like_youtube_post(request, video_id):
    youtube_post = get_object_or_404(YouTubePost, video_id=video_id)
    user = request.user

    if user.is_authenticated:
        if user in youtube_post.likes.all():
            youtube_post.likes.remove(user)
            liked = False
        else:
            youtube_post.likes.add(user)
            liked = True
        youtube_post.save()
        total_likes = youtube_post.total_likes
        return JsonResponse({'liked': liked, 'total_likes': total_likes})
    else:
        # Redirect to register.html if unauthenticated
        return JsonResponse({'redirect': '/users/register/'}, status=401)


@require_POST
def comment_youtube_post(request, video_id):
    youtube_post = get_object_or_404(YouTubePost, video_id=video_id)
    user = request.user

    if user.is_authenticated:
        data = json.loads(request.body)
        text = data.get('text')

        if text:
            comment = YoutubeComment.objects.create(
                youtube_post=youtube_post,
                user=user,
                text=text,
                created_at=timezone.now()
            )
            return JsonResponse({
                'user': user.username,
                'text': text,
                'created_at': comment.created_at.isoformat()
            })
        return JsonResponse({'error': 'No comment text provided.'}, status=400)
    else:
        # Redirect to register.html if unauthenticated
        return JsonResponse({'redirect': '/users/register/'}, status=401)

def share_youtube_post(request, video_id):
    youtube_post = get_object_or_404(YouTubePost, video_id=video_id)

    # Generate the link to the YouTube post detail page
    shared_link = request.build_absolute_uri(reverse('youtube_post_detail', args=[youtube_post.video_id]))

    # Construct the response data
    response_data = {
        'title': youtube_post.title,
        'shared_link': shared_link
    }

    return JsonResponse(response_data)


class YouTubePostDetailView(View):
    def get(self, request, video_id):
        try:
            # Fetch all posts with the same video_id
            posts = YouTubePost.objects.filter(video_id=video_id)
            if posts.count() > 1:
                # Keep the first post and delete the duplicates
                primary_post = posts.first()
                posts.exclude(id=primary_post.id).delete()
            else:
                # If no duplicates, fetch the single post
                primary_post = posts.first()
            
            if not primary_post:
                raise Http404("YouTube post not found.")

            # Fetch related posts
            related_posts = YouTubePost.objects.filter(
                title__icontains=primary_post.title.split()[0],
                description__icontains=primary_post.description.split()[0]
            ).exclude(video_id=video_id)

            # Prepare context for rendering
            context = {
                'post': primary_post,
                'related_posts': related_posts,
            }
            return render(request, 'youtube_post_detail.html', context)
        
        except Exception as e:
            # Log the exception if needed
            logger.error(f"Error in YouTubePostDetailView: {e}")
            raise Http404("Error occurred while retrieving the YouTube post.")

@login_required(login_url='/users/register/')
def edit_resource(request, resource_id):
    resource = get_object_or_404(Useful_resource, id=resource_id)

    if request.method == 'POST':
        form = UsefulResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, 'Resource updated successfully!')
            return redirect('useful_resources')
    else:
        form = UsefulResourceForm(instance=resource)

    return render(request, 'edit_resource.html', {'form': form, 'resource': resource})

@login_required(login_url='/users/register/')
def delete_resource(request, resource_id):
    resource = get_object_or_404(Useful_resource, id=resource_id)

    if request.method == 'POST':
        resource.delete()
        messages.success(request, 'Resource deleted successfully!')
        return redirect('useful_resources')

    return render(request, 'confirm_delete.html', {'resource': resource})

@login_required(login_url='/users/register/')
def upload_useful_resource(request):
    if request.method == 'POST':
        form = UsefulResourceForm(request.POST, request.FILES)
        if form.is_valid():
            # Create a new Useful_resource instance but don't save it to the database yet
            resource = form.save(commit=False)
            # Set the author of the resource to the current user
            resource.author = request.user
            # Save the resource instance to the database
            resource.save()
            messages.success(request, 'Resource uploaded successfully!')
            return redirect('useful_resources')  # Redirect to the page showing all resources or another relevant page
    else:
        form = UsefulResourceForm()

    return render(request, 'error_message.html', {'form': form})


@login_required(login_url='/users/register/')
def get_referral_link(request):
    try:
        profile = request.user.user_profile
    except Profile.DoesNotExist:
        return JsonResponse({"error": "Profile not found"}, status=404)

    referral_code = profile.referral_code
    referral_link = (
        f"{request.build_absolute_uri('/users/register/')}?referral_code={referral_code}"
    )
    return JsonResponse({"referral_link": referral_link})


def referral_link(request, referral_code):
    try:
        profile = Profile.objects.get(referral_code=referral_code)
        return redirect(f"/users/register/?referral_code={referral_code}")
    except Profile.DoesNotExist:
        return render(request, "error_message.html", status=404)


@login_required(login_url='/users/register/')
def get_coins(request):
    profile = request.user.user_profile

    if request.method == "POST":
        coins_amount = int(request.POST.get("coins_amount"))
        payment_option = request.POST.get("payment_option")

        if payment_option == "paystack":
            amount = coins_amount * 50  # Convert to amount in Kobo
            return redirect(f"https://paystack.com/pay/owd?amount={amount}")

        elif payment_option == "PayPal":
            return redirect(
                "https://paypal.me/oawisdomdigitalfirm?country.x=LS&locale.x=en_US"
            )

        elif payment_option == "USD_bank_transfer":
            user = request.user
            sender = User.objects.filter(is_superuser=True).first()

            if not sender:
                return HttpResponse("No admin user found to send notifications.")

            sender_profile_image = Profile.objects.get(user=sender).profile_image.url

            # Naira bank details
            naira_bank_details = {
                "account_name": "Oti Alid Wisdom",
                "bank": "MoniePoint Microfinance Bank",
                "account_number": "7081668601",
                "account_type": "Savings",
            }

            # USD bank details
            usd_bank_details = {
                "account_name": "ALID WISDOM OTI",
                "bank": "WELLS FARGO BANK, N.A.",
                "account_number": "1234567890",
                "routing_number": "987654321",
                "swift_code": "ABCDUS33",
                "account_type": "Checking",
                "address": "9450 Southwest Gemini Drive, Beaverton, OR, 97008, USA.",
            }

            # Combined notification message with Naira and USD details
            notification_message = f"""
            <h6>Make your transfer either in Naira or Dollar:</h6>
            <h6><strong>Naira Bank Transfer:</strong></h6>
            <p><strong>Account Name:</strong> {naira_bank_details['account_name']}</p>
            <p><strong>Bank:</strong> {naira_bank_details['bank']}</p>
            <p><strong>Account Number:</strong> {naira_bank_details['account_number']}</p>
            <p><strong>Account Type:</strong> {naira_bank_details['account_type']}</p>
            <hr>
            <h6><strong>Dollar Bank Transfer:</strong></h6>
            <p><strong>Account Name:</strong> {usd_bank_details['account_name']}</p>
            <p><strong>Bank:</strong> {usd_bank_details['bank']}</p>
            <p><strong>Account Number:</strong> {usd_bank_details['account_number']}</p>
            <p><strong>Routing Number:</strong> {usd_bank_details['routing_number']}</p>
            <p><strong>Swift Code:</strong> {usd_bank_details['swift_code']}</p>
            <p><strong>Account Type:</strong> {usd_bank_details['account_type']}</p>
            <p><strong>Address:</strong> {usd_bank_details['address']}</p>
            """

            Notification.objects.create(
                user=user,
                message=notification_message,
                is_read=False,
                sender=sender,
                sender_profile_image=sender_profile_image,
            )

            # Email content
            email_subject = "Payment Instructions for Your Coins"
            email_content = f"""
            Dear {user.username},

            Please make your payment using one of the following options:

            Naira Bank Transfer:
            Account Name: {naira_bank_details['account_name']}
            Bank: {naira_bank_details['bank']}
            Account Number: {naira_bank_details['account_number']}
            Account Type: {naira_bank_details['account_type']}

            Dollar Bank Transfer:
            Account Name: {usd_bank_details['account_name']}
            Bank: {usd_bank_details['bank']}
            Account Number: {usd_bank_details['account_number']}
            Routing Number: {usd_bank_details['routing_number']}
            Swift Code: {usd_bank_details['swift_code']}
            Account Type: {usd_bank_details['account_type']}
            Address: {usd_bank_details['address']}

            Kindly ensure to include your username as the reference when making the payment.

            Best regards,
            OA Wisdom Digital Firm
            """

            # Render the email template
            email_body = render_to_string('base_email.html', {
                'email_subject': email_subject,
                'email_content': email_content,
                'current_year': timezone.now().year,
            })

            # Function to send email asynchronously
            def send_email_async():
                send_mail(
                    email_subject,
                    "",  # Empty text message
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=email_body,  # HTML email content
                )

            threading.Thread(target=send_email_async).start()

            return HttpResponse("Bank transfer details have been sent to your email. Please check your notifications and complete the payment to proceed.")

    return render(request, "get_coins.html", {"profile": profile})


def get_verified(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            profile = get_object_or_404(Profile, user=request.user)
            payment_option = request.POST.get("payment_option")

            if payment_option == "paystack":
                amount = 5000  # Amount in Kobo (5,000 NGN)
                paystack_url = f"https://paystack.com/pay/owd-verification?amount={amount}"
                return redirect(paystack_url)

            elif payment_option == "PayPal":
                paypal_url = "https://paypal.me/oawisdomdigitalfirm?country.x=LS&locale.x=en_US"
                return redirect(paypal_url)

            elif payment_option == "USD_bank_transfer":
                user = request.user
                sender = User.objects.filter(is_superuser=True).first()

                if not sender:
                    return HttpResponse("No admin user found to send notifications.")

                sender_profile_image = Profile.objects.get(user=sender).profile_image.url

                # Naira bank details
                naira_bank_details = {
                    "account_name": "Oti Alid Wisdom",
                    "bank": "MoniePoint Microfinance Bank",
                    "account_number": "7081668601",
                    "account_type": "Savings",
                }

                # USD bank details
                usd_bank_details = {
                    "account_name": "ALID WISDOM OTI",
                    "bank": "WELLS FARGO BANK, N.A.",
                    "account_number": "1234567890",
                    "routing_number": "987654321",
                    "swift_code": "ABCDUS33",
                    "account_type": "Checking",
                    "address": "9450 Southwest Gemini Drive, Beaverton, OR, 97008, USA.",
                }

                # Combined notification message with Naira and USD details
                notification_message = f"""
                <h6>Make your transfer either in Naira or Dollar:</h6>
                <h6><strong>Naira Bank Transfer:</strong></h6>
                <p><strong>Account Name:</strong> {naira_bank_details['account_name']}</p>
                <p><strong>Bank:</strong> {naira_bank_details['bank']}</p>
                <p><strong>Account Number:</strong> {naira_bank_details['account_number']}</p>
                <p><strong>Account Type:</strong> {naira_bank_details['account_type']}</p>
                <hr>
                <h6><strong>Dollar Bank Transfer:</strong></h6>
                <p><strong>Account Name:</strong> {usd_bank_details['account_name']}</p>
                <p><strong>Bank:</strong> {usd_bank_details['bank']}</p>
                <p><strong>Account Number:</strong> {usd_bank_details['account_number']}</p>
                <p><strong>Routing Number:</strong> {usd_bank_details['routing_number']}</p>
                <p><strong>Swift Code:</strong> {usd_bank_details['swift_code']}</p>
                <p><strong>Account Type:</strong> {usd_bank_details['account_type']}</p>
                <p><strong>Address:</strong> {usd_bank_details['address']}</p>
                """

                Notification.objects.create(
                    user=user,
                    message=notification_message,
                    is_read=False,
                    sender=sender,
                    sender_profile_image=sender_profile_image,
                )

                # Email content
                email_subject = "Payment Instructions for Your Verification"
                email_content = f"""
                Dear {user.username},

                Please make your payment using one of the following options:

                Naira Bank Transfer:
                Account Name: {naira_bank_details['account_name']}
                Bank: {naira_bank_details['bank']}
                Account Number: {naira_bank_details['account_number']}
                Account Type: {naira_bank_details['account_type']}

                Dollar Bank Transfer:
                Account Name: {usd_bank_details['account_name']}
                Bank: {usd_bank_details['bank']}
                Account Number: {usd_bank_details['account_number']}
                Routing Number: {usd_bank_details['routing_number']}
                Swift Code: {usd_bank_details['swift_code']}
                Account Type: {usd_bank_details['account_type']}
                Address: {usd_bank_details['address']}

                Kindly ensure to include your username as the reference when making the payment.

                Best regards,
                OA Wisdom Digital Firm
                """

                # Render the email template
                email_body = render_to_string('base_email.html', {
                    'email_subject': email_subject,
                    'email_content': email_content,
                    'current_year': timezone.now().year,
                })

                # Function to send email asynchronously
                def send_email_async():
                    send_mail(
                        email_subject,
                        "",  # Empty text message
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        html_message=email_body,  # HTML email content
                    )

                threading.Thread(target=send_email_async).start()

                return HttpResponse("Bank transfer details have been sent to your email. Please check your notifications and complete the payment to proceed.")

            elif payment_option == "coins":
                if profile.coins >= 100:
                    profile.coins -= 100
                    profile.is_verified = True
                    profile.save()

                    notification_message = f"{profile.user.username} has been successfully verified using coins."
                    users = User.objects.all()
                    for user in users:
                        Notification.objects.create(
                            user=user,
                            message=notification_message,
                            is_broadcast=True,
                            sender=request.user,
                            sender_profile_image=profile.profile_image.url,
                        )

                    messages.success(
                        request, "You have been successfully verified using coins!"
                    )

                    return redirect("home")

                else:
                    messages.error(
                        request, "You do not have enough coins. Please buy more coins."
                    )
                    return redirect("buy_coins")

            else:
                return redirect("https://paystack.com/pay/owd-verification?amount=0")

        else:
            return render(request, "home.html")
    else:
        return redirect("register")

def buy_coins(request):
    # Get the user's profile
    profile = request.user.user_profile

    # Pass profile data to the template
    context = {
        "profile": profile,
    }
    return render(request, "buy_coins.html", context)


def marketplace_item_detail(request, item_id):
    item = get_object_or_404(MarketplaceItem, pk=item_id)
    # Example of filtering related items based on a different criterion
    related_items = MarketplaceItem.objects.exclude(pk=item_id).order_by("-created_at")[
        :5
    ]

    context = {
        "item": item,
        "related_items": related_items,
    }

    return render(request, "marketplace_item_detail.html", context)

@login_required(login_url='/users/register/')
def add_to_wishlist(request, item_id):
    if request.method == "POST":
        item = get_object_or_404(MarketplaceItem, pk=item_id)

        if request.user.is_authenticated:
            wishlist, created = Wishlist.objects.get_or_create(user=request.user)
            wishlist.items.add(item)
            wishlist.save()

            # Create a notification for the item owner
            Notification.objects.create(
                user=item.user,
                message=f"{request.user.username} has added your item '{item.name}' to their wishlist.",
                is_read=False,
                sender=request.user,
                sender_profile_image=(
                    request.user.user_profile.profile_image.url
                    if request.user.user_profile.profile_image
                    else None
                ),
                chat=None,
            )

            # Prepare email content
            email_subject = "Your Item Has Been Added to a Wishlist"
            email_content = f"Hello {item.user.username},\n\nYour item '{item.name}' has been added to a wishlist by {request.user.username}."

            # Render the email template
            email_body = render_to_string('base_email.html', {
                'email_subject': email_subject,
                'email_content': email_content,
                'current_year': timezone.now().year,
            })

            # Function to send email asynchronously
            def send_email():
                send_mail(
                    email_subject,
                    "",  # Empty text message
                    settings.DEFAULT_FROM_EMAIL,
                    [item.user.email],
                    html_message=email_body,  # HTML email content
                )

            # Start email sending in a separate thread
            threading.Thread(target=send_email).start()

            return JsonResponse({"success": True}, status=200)
        else:
            return JsonResponse(
                {"success": False, "redirect": reverse("login")}, status=403
            )
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

@login_required(login_url='/users/register/')
def contact_seller(request, item_id):
    item = get_object_or_404(MarketplaceItem, pk=item_id)
    if request.method == "POST":
        message = request.POST.get("message")
        subject = f"Interest in your item: {item.name}"
        sender = request.user.email
        recipient = item.user.email

        # Prepare email content using base_email.html
        email_content = render_to_string('base_email.html', {
            'email_subject': subject,
            'email_content': f"Message from {request.user.username}: {message}",
            'current_year': timezone.now().year,
        })

        # Send an email to the seller asynchronously
        threading.Thread(
            target=send_email_async,
            args=(subject, email_content, sender, [recipient])
        ).start()

        return redirect("home")  # Redirect to a success page or the home page

@login_required(login_url='/users/register/')
def add_to_cart(request, item_id):
    item = get_object_or_404(MarketplaceItem, pk=item_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, item=item)

    if not created:
        cart_item.quantity += 1
        cart_item.save()
    else:
        cart_item.quantity = 1
        cart_item.save()

    # Create a notification for the item owner
    Notification.objects.create(
        user=item.user,  # Assuming `owner` is a field in MarketplaceItem
        message=f"{request.user.username} has added your item '{item.name}' to their cart.",
        is_read=False,
        sender=request.user,
        sender_profile_image=(
            request.user.user_profile.profile_image.url
            if request.user.user_profile.profile_image
            else None
        ),
        chat=None,  # Optional, if you have chat functionality
    )

    # Prepare email content using base_email.html
    email_subject = "Your Item Has Been Added to a Cart"
    email_content = f"Hello {item.user.username},\n\nYour item '{item.name}' has been added to a cart by {request.user.username}."

    # Render the email template
    email_body = render_to_string('base_email.html', {
        'email_subject': email_subject,
        'email_content': email_content,
        'current_year': timezone.now().year,
    })

    # Function to send the email asynchronously
    def send_email():
        try:
            send_mail(
                subject=email_subject,
                message="",  # Empty plain text message
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[item.user.email],
                html_message=email_body,  # HTML email content
            )
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    # Send the email asynchronously in a separate thread
    threading.Thread(target=send_email).start()

    return redirect("cart_view")



def cart_view(request):
    cart = Cart.objects.get(user=request.user)
    cart_items = cart.cart_items.all()  # Get all CartItems in the cart

    return render(request, "cart_view.html", {"cart": cart, "cart_items": cart_items})

@login_required(login_url='/users/register/')
def add_marketplace_item(request):
    if request.method == "POST":
        item_form = MarketplaceItemForm(request.POST)

        if item_form.is_valid():
            # Save the marketplace item
            item = item_form.save(commit=False)
            item.user = request.user  # Assuming a user is logged in
            item.save()

            # Handle multiple image uploads
            images = request.FILES.getlist('images')
            for image in images:
                MarketplaceItemImage.objects.create(item=item, image=image)

            messages.success(request, "Marketplace item added successfully!")
            return redirect('home')  # Redirect to a page showing the items
        else:
            messages.error(request, "There was an error with your submission.")

    else:
        item_form = MarketplaceItemForm()

    return render(request, 'home.html', {'item_form': item_form})

@login_required(login_url='/users/register/')
def join_marketplace(request):
    try:
        marketplace_entry = MarketplaceEntry.objects.get(user=request.user)
    except MarketplaceEntry.DoesNotExist:
        marketplace_entry = None

    if request.method == "POST":
        form = MarketplaceForm(request.POST, request.FILES, instance=marketplace_entry)
        if form.is_valid():
            marketplace_entry = form.save(commit=False)
            marketplace_entry.user = request.user
            marketplace_entry.save()
            return redirect("profile", username=request.user.username)
    else:
        form = MarketplaceForm(instance=marketplace_entry)

    return render(request, "join_marketplace.html", {"form": form})


def search_marketplace(request):
    query = request.GET.get("query")
    profiles = []
    user_profiles_list = []  # List to store user profiles separately
    blog_posts = []
    youtube_posts = []
    marketplace_items = []

    if query:
        # Search for marketplace users
        marketplace_entries = MarketplaceEntry.objects.filter(
            Q(user__username__icontains=query)
            | Q(occupation__icontains=query)
            | Q(sell_or_service__icontains=query)
            | Q(product_or_service__icontains=query)
            | Q(office_address__icontains=query)
            | Q(years_experience__icontains=query)
            | Q(specialty__icontains=query)
            | Q(phone_number1__icontains=query)
            | Q(phone_number2__icontains=query)
            | Q(portfolio_link__icontains=query)
        )
        profiles = [
            (entry, Profile.objects.get(user=entry.user)) for entry in marketplace_entries
        ]

        # Search for user profiles (not from marketplace)
        user_profiles = User.objects.filter(username__icontains=query)
        for user in user_profiles:
            try:
                profile = Profile.objects.get(user=user)
                user_profiles_list.append((profile, profile.subscribers.count()))
            except Profile.DoesNotExist:
                continue

        # Search for blog posts
        blog_posts = BlogPost.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query) | Q(tags__icontains=query)
        )

        # Search for YouTube videos
        youtube_posts = YouTubePost.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

        # Search for marketplace items
        marketplace_items = MarketplaceItem.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    return render(
        request,
        "search_results.html",
        {
            "profiles": profiles,
            "user_profiles_list": user_profiles_list,  # Pass the list of user profiles
            "blog_posts": blog_posts,
            "youtube_posts": youtube_posts,
            "marketplace_items": marketplace_items,
            "query": query,
        }
    )

def upload_message(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            form = MessageForm(request.POST)

            if form.is_valid():
                # Create a new Message instance
                message = form.save(commit=False)
                message.user = (
                    request.user
                )  # Ensure the user is attached to the message
                message.save()

                # Handle file uploads
                files = request.FILES.getlist("files")  # Use getlist for multiple files
                for file in files:
                    FileUpload.objects.create(message=message, file=file)

                # Get the adspost_id and payment_option from the form
                adspost_id = request.POST.get("adspost_id")
                payment_option = request.POST.get("payment_option")

                amount = 0  # Default amount if no adspost is provided

                if adspost_id:
                    try:
                        # Try to get the Adsposts object
                        adspost = get_object_or_404(Adsposts, id=adspost_id)

                        # Extract price from adspost.name (assuming it's included)
                        amount_match = re.search(r"#([\d,]+)", adspost.name)
                        if amount_match:
                            raw_amount = amount_match.group(1).replace(",", "")
                            amount = int(raw_amount) * 100  # Convert Naira to Kobo

                        else:
                            return render(
                                request,
                                "error_message.html",
                                {
                                    "error": "Price information not found in adspost name."
                                },
                            )

                    except Adsposts.DoesNotExist:
                        return render(
                            request,
                            "error_message.html",
                            {"error": "Adspost not found."},
                        )

                # Handle different payment options based on payment_option
                if payment_option == "paystack":
                    # Redirect to Paystack payment URL
                    default_redirect_url = (
                        f"https://paystack.com/pay/owd?amount={amount}"
                    )
                    return redirect(default_redirect_url)

                elif payment_option == "PayPal":
                    # Redirect to PayPal payment URL
                    paypal_url = "https://paypal.me/oawisdomdigitalfirm?country.x=LS&locale.x=en_US"
                    return redirect(paypal_url)

                elif payment_option == "USD bank_transfer":
                    # Handle bank transfer option
                    user = request.user
                    profile = Profile.objects.get(user=user)

                    # Get the first superuser as the sender
                    sender = User.objects.filter(is_superuser=True).first()

                    if not sender:
                        return HttpResponse(
                            "No admin user found to send notifications."
                        )

                    sender_profile_image = Profile.objects.get(
                        user=sender
                    ).profile_image.url

                    # Naira bank details
                    naira_bank_details = {
                        "account_name": "Oti Alid Wisdom",
                        "bank": "MoniePoint Microfinance Bank",
                        "account_number": "7081668601",
                        "account_type": "Savings",
                    }

                    # USD bank details
                    usd_bank_details = {
                        "account_name": "ALID WISDOM OTI",
                        "bank": "WELLS FARGO BANK, N.A.",
                        "account_number": "1234567890",
                        "routing_number": "987654321",
                        "swift_code": "ABCDUS33",
                        "account_type": "Checking",
                        "address": "9450 Southwest Gemini Drive, Beaverton, OR, 97008, USA.",
                    }

                    # Combined notification message with Naira and USD details
                    notification_message = f"""
                    <h6>Make your transfer either in Naira or Dollar:</h6>
                    <h6><strong>Naira Bank Transfer:</strong></h6>
                    <p><strong>Account Name:</strong> {naira_bank_details['account_name']}</p>
                    <p><strong>Bank:</strong> {naira_bank_details['bank']}</p>
                    <p><strong>Account Number:</strong> {naira_bank_details['account_number']}</p>
                    <p><strong>Account Type:</strong> {naira_bank_details['account_type']}</p>
                    <hr>
                    <h6><strong>Dollar Bank Transfer:</strong></h6>
                    <p><strong>Account Name:</strong> {usd_bank_details['account_name']}</p>
                    <p><strong>Bank:</strong> {usd_bank_details['bank']}</p>
                    <p><strong>Account Number:</strong> {usd_bank_details['account_number']}</p>
                    <p><strong>Routing Number:</strong> {usd_bank_details['routing_number']}</p>
                    <p><strong>Swift Code:</strong> {usd_bank_details['swift_code']}</p>
                    <p><strong>Account Type:</strong> {usd_bank_details['account_type']}</p>
                    <p><strong>Address:</strong> {usd_bank_details['address']}</p>
                    """

                    Notification.objects.create(
                        user=user,
                        message=notification_message,
                        is_read=False,
                        sender=sender,
                        sender_profile_image=sender_profile_image,
                    )

                    # Email content
                    email_subject = "Payment Instructions for Your Sponsored Ads Campaign"
                    email_content = f"""
                    Dear {user.username},

                    Please make your payment using one of the following options:

                    Naira Bank Transfer:
                    Account Name: {naira_bank_details['account_name']}
                    Bank: {naira_bank_details['bank']}
                    Account Number: {naira_bank_details['account_number']}
                    Account Type: {naira_bank_details['account_type']}

                    Dollar Bank Transfer:
                    Account Name: {usd_bank_details['account_name']}
                    Bank: {usd_bank_details['bank']}
                    Account Number: {usd_bank_details['account_number']}
                    Routing Number: {usd_bank_details['routing_number']}
                    Swift Code: {usd_bank_details['swift_code']}
                    Account Type: {usd_bank_details['account_type']}
                    Address: {usd_bank_details['address']}

                    Kindly ensure to include your username as the reference when making the payment.

                    Best regards,
                    OA Wisdom Digital Firm
                    """

                    # Render the email template
                    email_body = render_to_string('base_email.html', {
                        'email_subject': email_subject,
                        'email_content': email_content,
                        'current_year': timezone.now().year,
                    })

                    # Function to send email asynchronously
                    def send_email_async():
                        send_mail(
                            email_subject,
                            "",  # Empty text message
                            settings.DEFAULT_FROM_EMAIL,
                            [user.email],
                            html_message=email_body,  # HTML email content
                        )

                    threading.Thread(target=send_email_async).start()

                    return HttpResponse("Bank transfer details have been sent to your email. Please check your notifications and complete the payment to proceed.")

                else:
                    # If no specific payment option is selected, redirect to a default page
                    return redirect("https://paystack.com/pay/owd?amount=0")

            else:
                # Handle form validation errors
                if request.is_ajax():
                    return JsonResponse({"error": form.errors}, status=400)
                else:
                    return render(
                        request,
                        "error_message.html",
                        {
                            "form": form,
                            "error": "Form is invalid. Please correct the errors and try again.",
                        },
                    )

        else:
            form = MessageForm()

        return render(request, "message_form.html", {"form": form})
    else:
        return redirect("register")


def home(request):
    profile = None
    posts = BlogPost.objects.filter(is_approved=True).order_by("-created_at")
    subscriptions = []
    marketplace_entry_exists = False
    notifications_count = 0

    if request.user.is_authenticated:
        profile = Profile.objects.filter(user=request.user).first()
        subscriptions = [
            post.author.id
            for post in posts
            if Profile.objects.filter(
                user=post.author, subscribers=request.user
            ).exists()
        ]
        marketplace_entry_exists = MarketplaceEntry.objects.filter(
            user=request.user
        ).exists()

        notifications = Notification.objects.filter(user=request.user, is_read=False)
        notifications_count = notifications.count()
    else:
        request.user = AnonymousUser()  # Explicitly set to AnonymousUser

    marketplace_items = MarketplaceItem.objects.all()
    for item in marketplace_items:
        item.increment_view_count()

    context = {
        "posts": posts,
        "marketplace_items": marketplace_items,
        "adsposts": Adsposts.objects.all(),
        "comments": Comment.objects.all(),
        "data_purchase": DataPurchase.objects.all(),
        "materials": Material.objects.all(),
        "motivational_books": MotivationalBook.objects.all(),
        "user": request.user,
        "profile": profile,
        "subscriptions": subscriptions,
        "marketplace_entry_exists": marketplace_entry_exists,
        "notifications": notifications if request.user.is_authenticated else [],
        "notifications_count": notifications_count,
    }
    return render(request, "home.html", context)


def mixed_content_api(request):
    user = request.user

    # Fetch YouTube posts
    youtube_posts = YouTubePost.objects.all().order_by('-published_at')
    youtube_data = [
        {
            'type': 'youtube',
            'title': post.title,
            'description': post.description,
            'video_id': post.video_id,
            'published_at': post.published_at.isoformat(),
            'thumbnail_url': post.thumbnail_url,
            'total_likes': post.total_likes,
            'liked': user.is_authenticated and user in post.likes.all(),
        }
        for post in youtube_posts
    ]

    # Fetch Blog posts
    blog_posts = BlogPost.objects.filter(is_approved=True).order_by('-created_at')
    blog_data = [
        {
            'type': 'blog',
            'title': post.title,
            'content': post.content,
            'image': post.image.url,
            'url': post.get_absolute_url(),
            'created_at': post.created_at.isoformat(),
            'total_likes': post.total_likes(),
            'liked': user.is_authenticated and user in post.likes.all(),
        }
        for post in blog_posts
    ]

    # Combine and sort by date
    combined_data = sorted(
        chain(youtube_data, blog_data),
        key=lambda x: x['published_at'] if x['type'] == 'youtube' else x['created_at'],
        reverse=True
    )

    return JsonResponse(combined_data, safe=False)


@login_required(login_url='/users/register/')
def share_marketplace_item(request, item_id):
    # Fetch the marketplace item
    item = get_object_or_404(MarketplaceItem, pk=item_id)

    # Construct the shared link URL to the item's detail page
    shared_link = request.build_absolute_uri(
        reverse("marketplace_item_detail", kwargs={"item_id": item.id})
    )

    # Prepare the JSON response
    data = {
        "title": item.name,
        "description": item.description,
        "shared_link": shared_link,
    }

    # Create a notification for the item owner
    Notification.objects.create(
        user=item.user,
        message=f"Your item '{item.name}' has been shared.",
        is_read=False,
        sender=request.user,
        sender_profile_image=(
            request.user.user_profile.profile_image.url
            if request.user.user_profile.profile_image
            else None
        ),
        chat=None,  # Optional, if you have chat functionality
    )

    # Email content for the item owner
    email_subject = f"Item Shared: {item.name}"
    email_content = f"""
        <p>Hello {item.user.username},</p>
        <p>Your item <strong>{item.name}</strong> has been shared.</p>
        <p>Check it out <a href="{shared_link}">here</a>.</p>
    """

    # Render the email template with the dynamic content
    email_body = render_to_string('base_email.html', {
        'email_subject': email_subject,
        'email_content': email_content,
        'current_year': timezone.now().year,
    })

    # Function to send email asynchronously
    def send_email_async():
        try:
            send_mail(
                subject=email_subject,
                message="",  # Empty text message, because we're using HTML email
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[item.user.email],
                html_message=email_body,  # Use the rendered HTML template
            )
        except Exception as e:
            logger.error(f"Failed to send email to {item.user.email}: {e}")

    # Send the email in a separate thread to avoid blocking
    threading.Thread(target=send_email_async).start()

    return JsonResponse(data)


@login_required(login_url='/users/register/')
@require_POST
def subscribe_author(request, author_id):
    try:
        author = User.objects.get(id=author_id)
        profile = Profile.objects.get(user=author)

        if request.user == author:
            return JsonResponse({"error": "Cannot subscribe to yourself"}, status=400)

        if request.user in profile.subscribers.all():
            # Unsubscribe
            profile.subscribers.remove(request.user)
            profile.coins -= 1  # Deduct 1 coin
            subscribed = False

            # Create a notification for the profile owner
            Notification.objects.create(
                user=author,
                message=f"{request.user.username} has unsubscribed from you. You have lost one coin.",
                is_read=False,
                sender=request.user,
                sender_profile_image=(
                    request.user.user_profile.profile_image.url
                    if request.user.user_profile.profile_image
                    else None
                ),
                chat=None,  # Optional, if you have chat functionality
            )

            # Email content for the unsubscribe action
            email_subject = "Unsubscriber Alert"
            email_content = f"""
                <p>Hello {author.username},</p>
                <p>{request.user.username} has unsubscribed from you. You have lost one coin.</p>
            """

        else:
            # Subscribe
            profile.subscribers.add(request.user)
            profile.coins += 1  # Award 1 coin
            subscribed = True

            # Create a notification for the profile owner
            Notification.objects.create(
                user=author,
                message=f"{request.user.username} has subscribed to you. You have earned one coin.",
                is_read=False,
                sender=request.user,
                sender_profile_image=(
                    request.user.user_profile.profile_image.url
                    if request.user.user_profile.profile_image
                    else None
                ),
                chat=None,  # Optional, if you have chat functionality
            )

            # Email content for the subscribe action
            email_subject = "New Subscriber"
            email_content = f"""
                <p>Hello {author.username},</p>
                <p>You have a new subscriber: {request.user.username}. You have earned one coin.</p>
            """

        # Render the email template with the dynamic content
        email_body = render_to_string('base_email.html', {
            'email_subject': email_subject,
            'email_content': email_content,
            'current_year': timezone.now().year,
        })

        # Function to send email asynchronously
        def send_email_async():
            try:
                send_mail(
                    subject=email_subject,
                    message="",  # Empty text message, because we're using HTML email
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[author.email],
                    html_message=email_body,  # Use the rendered HTML template
                )
            except Exception as e:
                logger.error(f"Failed to send email to {author.email}: {e}")

        # Send the email in a separate thread to avoid blocking
        threading.Thread(target=send_email_async).start()

        profile.save()  # Save profile changes

        return JsonResponse({"subscribed": subscribed})

    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Profile.DoesNotExist:
        return JsonResponse({"error": "Profile not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



def website_requirement(request):
    if request.method == "POST":
        form = WebsiteRequirementForm(request.POST, request.FILES)
        payment_option = request.POST.get("payment_option")

        if form.is_valid():
            website_requirement = form.save(commit=False)

            if website_requirement.budget_naira:
                exchange_rate = 414
                website_requirement.budget_usd = float(website_requirement.budget_naira) / exchange_rate
                website_requirement.save()

                if payment_option == "paystack":
                    paystack_base_url = "https://paystack.com/pay/owd"
                    amount_in_kobo = int(website_requirement.budget_naira * 100)
                    reference = website_requirement.id
                    paystack_url = f"{paystack_base_url}?amount={amount_in_kobo}&reference={reference}"
                    return redirect(paystack_url)

                elif payment_option == "PayPal":
                    PayPal_url = "https://paypal.me/oawisdomdigitalfirm?country.x=LS&locale.x=en_US"
                    return redirect(PayPal_url)

                elif payment_option == "USD bank_transfer" or payment_option == "Naira bank_transfer":
                    user = request.user
                    profile = Profile.objects.get(user=user)
                    sender = User.objects.filter(is_superuser=True).first()

                    if sender is None:
                        return HttpResponse("No admin user found to send notifications.")

                    sender_profile_image = None
                    try:
                        sender_profile = Profile.objects.get(user=sender)
                        sender_profile_image = sender_profile.profile_image.url
                    except Profile.DoesNotExist:
                        sender_profile_image = "/path/to/default/image.jpg"  # Replace with default image path

                    # Naira bank details
                    naira_bank_details = {
                        "account_name": "Oti Alid Wisdom",
                        "bank": "MoniePoint Microfinance Bank",
                        "account_number": "7081668601",
                        "account_type": "Savings",
                    }

                    # USD bank details
                    usd_bank_details = {
                        "account_name": "ALID WISDOM OTI",
                        "bank": "WELLS FARGO BANK, N.A.",
                        "account_number": "1234567890",
                        "routing_number": "987654321",
                        "swift_code": "ABCDUS33",
                        "account_type": "Checking",
                        "address": "9450 Southwest Gemini Drive, Beaverton, OR, 97008, USA.",
                    }

                    # Combined notification message with Naira and USD details
                    notification_message = f"""
                    <h6>Make your transfer either in Naira or Dollar:</h6>
                    <h6><strong>Naira Bank Transfer:</strong></h6>
                    <p><strong>Account Name:</strong> {naira_bank_details['account_name']}</p>
                    <p><strong>Bank:</strong> {naira_bank_details['bank']}</p>
                    <p><strong>Account Number:</strong> {naira_bank_details['account_number']}</p>
                    <p><strong>Account Type:</strong> {naira_bank_details['account_type']}</p>
                    <hr>
                    <h6><strong>Dollar Bank Transfer:</strong></h6>
                    <p><strong>Account Name:</strong> {usd_bank_details['account_name']}</p>
                    <p><strong>Bank:</strong> {usd_bank_details['bank']}</p>
                    <p><strong>Account Number:</strong> {usd_bank_details['account_number']}</p>
                    <p><strong>Routing Number:</strong> {usd_bank_details['routing_number']}</p>
                    <p><strong>Swift Code:</strong> {usd_bank_details['swift_code']}</p>
                    <p><strong>Account Type:</strong> {usd_bank_details['account_type']}</p>
                    <p><strong>Address:</strong> {usd_bank_details['address']}</p>
                    """

                    Notification.objects.create(
                        user=user,
                        message=notification_message,
                        is_read=False,
                        sender=sender,
                        sender_profile_image=sender_profile_image,
                    )

                    # Email content
                    email_subject = "Payment Instructions for Your Website Requirement"
                    email_content = f"""
                    Dear {user.username},

                    Please make your payment using one of the following options:

                    Naira Bank Transfer:
                    Account Name: {naira_bank_details['account_name']}
                    Bank: {naira_bank_details['bank']}
                    Account Number: {naira_bank_details['account_number']}
                    Account Type: {naira_bank_details['account_type']}

                    Dollar Bank Transfer:
                    Account Name: {usd_bank_details['account_name']}
                    Bank: {usd_bank_details['bank']}
                    Account Number: {usd_bank_details['account_number']}
                    Routing Number: {usd_bank_details['routing_number']}
                    Swift Code: {usd_bank_details['swift_code']}
                    Account Type: {usd_bank_details['account_type']}
                    Address: {usd_bank_details['address']}

                    Kindly ensure to include your username as the reference when making the payment.

                    Best regards,
                    OA Wisdom Digital Firm
                    """

                    # Render the email template
                    email_body = render_to_string('base_email.html', {
                        'email_subject': email_subject,
                        'email_content': email_content,
                        'current_year': timezone.now().year,
                    })

                    # Function to send email asynchronously
                    def send_email_async():
                        send_mail(
                            email_subject,
                            "",  # Empty message for plain text
                            settings.DEFAULT_FROM_EMAIL,
                            [user.email],
                            html_message=email_body,  # HTML content
                        )

                    # Send email in a separate thread
                    threading.Thread(target=send_email_async).start()

                    return HttpResponse("Bank transfer details have been sent to your email. Please check your notifications and complete the payment to proceed.")
            else:
                return HttpResponse("Budget is required; budget determines quality.")
        else:
            return JsonResponse({"error": form.errors}, status=400)

    else:
        form = WebsiteRequirementForm()

    return render(request, "error_message.html", {"form": form})


def domain_hosting_request(request):
    if request.method == "POST":
        form = DomainHostingRequirementForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                domain_hosting_request = form.save(commit=False)
                domain_hosting_request.save()

                payment_option = request.POST.get("payment_option")

                if payment_option == "paystack":
                    return redirect("https://paystack.com/pay/owd")
                elif payment_option == "PayPal":
                    return redirect("https://paypal.me/oawisdomdigitalfirm?country.x=LS&locale.x=en_US")
                elif payment_option == "USD bank_transfer" or payment_option == "Naira bank_transfer":
                    user = request.user
                    profile = Profile.objects.get(user=user)
                    sender = User.objects.filter(is_superuser=True).first()

                    if sender is None:
                        return HttpResponse("No admin user found to send notifications.")

                    sender_profile_image = None
                    try:
                        sender_profile = Profile.objects.get(user=sender)
                        sender_profile_image = sender_profile.profile_image.url
                    except Profile.DoesNotExist:
                        sender_profile_image = "/path/to/default/image.jpg"  # Replace with default image path

                    # Naira bank details
                    naira_bank_details = {
                        "account_name": "Oti Alid Wisdom",
                        "bank": "MoniePoint Microfinance Bank",
                        "account_number": "7081668601",
                        "account_type": "Savings",
                    }

                    # USD bank details
                    usd_bank_details = {
                        "account_name": "ALID WISDOM OTI",
                        "bank": "WELLS FARGO BANK, N.A.",
                        "account_number": "1234567890",
                        "routing_number": "987654321",
                        "swift_code": "ABCDUS33",
                        "account_type": "Checking",
                        "address": "9450 Southwest Gemini Drive, Beaverton, OR, 97008, USA.",
                    }

                    # Combined notification message with Naira and USD details
                    notification_message = f"""
                    <h6>Make your transfer either in Naira or Dollar:</h6>
                    <h6><strong>Naira Bank Transfer:</strong></h6>
                    <p><strong>Account Name:</strong> {naira_bank_details['account_name']}</p>
                    <p><strong>Bank:</strong> {naira_bank_details['bank']}</p>
                    <p><strong>Account Number:</strong> {naira_bank_details['account_number']}</p>
                    <p><strong>Account Type:</strong> {naira_bank_details['account_type']}</p>
                    <hr>
                    <h6><strong>Dollar Bank Transfer:</strong></h6>
                    <p><strong>Account Name:</strong> {usd_bank_details['account_name']}</p>
                    <p><strong>Bank:</strong> {usd_bank_details['bank']}</p>
                    <p><strong>Account Number:</strong> {usd_bank_details['account_number']}</p>
                    <p><strong>Routing Number:</strong> {usd_bank_details['routing_number']}</p>
                    <p><strong>Swift Code:</strong> {usd_bank_details['swift_code']}</p>
                    <p><strong>Account Type:</strong> {usd_bank_details['account_type']}</p>
                    <p><strong>Address:</strong> {usd_bank_details['address']}</p>
                    """

                    Notification.objects.create(
                        user=user,
                        message=notification_message,
                        is_read=False,
                        sender=sender,
                        sender_profile_image=sender_profile_image,
                    )

                    # Email content
                    email_subject = "Payment Instructions for Your Domain Hosting Request"
                    email_content = f"""
                    Dear {user.username},

                    Please make your payment using one of the following options:

                    Naira Bank Transfer:
                    Account Name: {naira_bank_details['account_name']}
                    Bank: {naira_bank_details['bank']}
                    Account Number: {naira_bank_details['account_number']}
                    Account Type: {naira_bank_details['account_type']}

                    Dollar Bank Transfer:
                    Account Name: {usd_bank_details['account_name']}
                    Bank: {usd_bank_details['bank']}
                    Account Number: {usd_bank_details['account_number']}
                    Routing Number: {usd_bank_details['routing_number']}
                    Swift Code: {usd_bank_details['swift_code']}
                    Account Type: {usd_bank_details['account_type']}
                    Address: {usd_bank_details['address']}

                    Kindly ensure to include your username as the reference when making the payment.

                    Best regards,
                    OA Wisdom Digital Firm
                    """

                    # Render the email template
                    email_body = render_to_string('base_email.html', {
                        'email_subject': email_subject,
                        'email_content': email_content,
                        'current_year': timezone.now().year,
                    })

                    # Function to send email asynchronously
                    def send_email_async():
                        send_mail(
                            email_subject,
                            "",  # Empty text message
                            settings.DEFAULT_FROM_EMAIL,
                            [user.email],
                            html_message=email_body,  # HTML email content
                        )

                    threading.Thread(target=send_email_async).start()

                    return HttpResponse("Bank transfer details have been sent to your email. Please check your notifications and complete the payment to proceed.")
            except Exception as e:
                print("Error saving form:", e)
                return HttpResponse("An error occurred. Please try again.")
        else:
            return render(request, "home.html", {"form": form})
    else:
        form = DomainHostingRequirementForm()

    return render(request, "home.html", {"form": form})




def facebook_ads_requirement(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            form = FacebookAdRequirementForm(request.POST, request.FILES)
            payment_option = request.POST.get("payment_option")

            if form.is_valid():
                facebook_ads_request = form.save(commit=False)
                facebook_ads_request.user = (
                    request.user
                )  # Ensure the user is attached to the request
                facebook_ads_request.save()

                if payment_option == "paystack":
                    return redirect("https://paystack.com/pay/owd")
                elif payment_option == "PayPal":
                    return redirect("https://paypal.me/oawisdomdigitalfirm?country.x=LS&locale.x=en_US")
                elif payment_option == "USD bank_transfer" or payment_option == "Naira bank_transfer":
                    user = request.user
                    profile = Profile.objects.get(user=user)
                    sender = User.objects.filter(is_superuser=True).first()

                    if sender is None:
                        return HttpResponse("No admin user found to send notifications.")

                    sender_profile_image = None
                    try:
                        sender_profile = Profile.objects.get(user=sender)
                        sender_profile_image = sender_profile.profile_image.url
                    except Profile.DoesNotExist:
                        sender_profile_image = "/path/to/default/image.jpg"  # Replace with default image path

                    # Naira bank details
                    naira_bank_details = {
                        "account_name": "Oti Alid Wisdom",
                        "bank": "MoniePoint Microfinance Bank",
                        "account_number": "7081668601",
                        "account_type": "Savings",
                    }

                    # USD bank details
                    usd_bank_details = {
                        "account_name": "ALID WISDOM OTI",
                        "bank": "WELLS FARGO BANK, N.A.",
                        "account_number": "1234567890",
                        "routing_number": "987654321",
                        "swift_code": "ABCDUS33",
                        "account_type": "Checking",
                        "address": "9450 Southwest Gemini Drive, Beaverton, OR, 97008, USA.",
                    }

                    # Combined notification message with Naira and USD details
                    notification_message = f"""
                    <h6>Make your transfer either in Naira or Dollar:</h6>
                    <h6><strong>Naira Bank Transfer:</strong></h6>
                    <p><strong>Account Name:</strong> {naira_bank_details['account_name']}</p>
                    <p><strong>Bank:</strong> {naira_bank_details['bank']}</p>
                    <p><strong>Account Number:</strong> {naira_bank_details['account_number']}</p>
                    <p><strong>Account Type:</strong> {naira_bank_details['account_type']}</p>
                    <hr>
                    <h6><strong>Dollar Bank Transfer:</strong></h6>
                    <p><strong>Account Name:</strong> {usd_bank_details['account_name']}</p>
                    <p><strong>Bank:</strong> {usd_bank_details['bank']}</p>
                    <p><strong>Account Number:</strong> {usd_bank_details['account_number']}</p>
                    <p><strong>Routing Number:</strong> {usd_bank_details['routing_number']}</p>
                    <p><strong>Swift Code:</strong> {usd_bank_details['swift_code']}</p>
                    <p><strong>Account Type:</strong> {usd_bank_details['account_type']}</p>
                    <p><strong>Address:</strong> {usd_bank_details['address']}</p>
                    """

                    Notification.objects.create(
                        user=user,
                        message=notification_message,
                        is_read=False,
                        sender=sender,
                        sender_profile_image=sender_profile_image,
                    )

                    # Email content
                    email_subject = "Payment Instructions for Your Sponsored Ads Campaign"
                    email_content = f"""
                    Dear {user.username},

                    Please make your payment using one of the following options:

                    Naira Bank Transfer:
                    Account Name: {naira_bank_details['account_name']}
                    Bank: {naira_bank_details['bank']}
                    Account Number: {naira_bank_details['account_number']}
                    Account Type: {naira_bank_details['account_type']}

                    Dollar Bank Transfer:
                    Account Name: {usd_bank_details['account_name']}
                    Bank: {usd_bank_details['bank']}
                    Account Number: {usd_bank_details['account_number']}
                    Routing Number: {usd_bank_details['routing_number']}
                    Swift Code: {usd_bank_details['swift_code']}
                    Account Type: {usd_bank_details['account_type']}
                    Address: {usd_bank_details['address']}

                    Kindly ensure to include your username as the reference when making the payment.

                    Best regards,
                    OA Wisdom Digital Firm
                    """

                    # Render the email template
                    email_body = render_to_string('base_email.html', {
                        'email_subject': email_subject,
                        'email_content': email_content,
                        'current_year': timezone.now().year,
                    })

                    # Function to send email asynchronously
                    def send_email_async():
                        send_mail(
                            email_subject,
                            "",  # Empty text message
                            settings.DEFAULT_FROM_EMAIL,
                            [user.email],
                            html_message=email_body,  # HTML email content
                        )

                    threading.Thread(target=send_email_async).start()

                    return HttpResponse("Bank transfer details have been sent to your email. Please check your notifications and complete the payment to proceed.")
            else:
                # Handle form errors properly
                if request.is_ajax():
                    return JsonResponse({"error": form.errors}, status=400)
                else:
                    return render(request, "error_message.html", {"form": form})
        else:
            form = FacebookAdRequirementForm()

        return render(request, "facebook_ads_form.html", {"form": form})
    else:
        return redirect("register")


@csrf_exempt
def post_list(request):
    blog_posts = BlogPost.objects.all()
    blog_post_form = BlogPostForm()
    comment_form = CommentForm()

    if request.method == "POST":
        ai_form = AIIntegrationRequestForm(request.POST, request.FILES)
        if ai_form.is_valid():
            ai_request = ai_form.save()
            payment_option = ai_form.cleaned_data.get("payment_option")
            user = request.user

            if payment_option == "paystack":
                return redirect("https://paystack.com/pay/owd-ai-integration")

            elif payment_option == "PayPal":
                return redirect("https://paypal.me/oawisdomdigitalfirm?country.x=LS&locale.x=en_US")

            elif payment_option == "USD bank_transfer":
                sender = User.objects.filter(is_superuser=True).first()

                if not sender:
                    return JsonResponse({"error": "No admin user found to send notifications."}, status=500)

                sender_profile_image = Profile.objects.get(user=sender).profile_image.url

            # Naira bank details
                naira_bank_details = {
                    "account_name": "Oti Alid Wisdom",
                    "bank": "MoniePoint Microfinance Bank",
                    "account_number": "7081668601",
                    "account_type": "Savings",
                }

                # USD bank details
                usd_bank_details = {
                    "account_name": "ALID WISDOM OTI",
                    "bank": "WELLS FARGO BANK, N.A.",
                    "account_number": "1234567890",
                    "routing_number": "987654321",
                    "swift_code": "ABCDUS33",
                    "account_type": "Checking",
                    "address": "9450 Southwest Gemini Drive, Beaverton, OR, 97008, USA.",
                }

                # Combined notification message with Naira and USD details
                notification_message = f"""
                <h6>Make your transfer either in Naira or Dollar:</h6>
                <h6><strong>Naira Bank Transfer:</strong></h6>
                <p><strong>Account Name:</strong> {naira_bank_details['account_name']}</p>
                <p><strong>Bank:</strong> {naira_bank_details['bank']}</p>
                <p><strong>Account Number:</strong> {naira_bank_details['account_number']}</p>
                <p><strong>Account Type:</strong> {naira_bank_details['account_type']}</p>
                <hr>
                <h6><strong>Dollar Bank Transfer:</strong></h6>
                <p><strong>Account Name:</strong> {usd_bank_details['account_name']}</p>
                <p><strong>Bank:</strong> {usd_bank_details['bank']}</p>
                <p><strong>Account Number:</strong> {usd_bank_details['account_number']}</p>
                <p><strong>Routing Number:</strong> {usd_bank_details['routing_number']}</p>
                <p><strong>Swift Code:</strong> {usd_bank_details['swift_code']}</p>
                <p><strong>Account Type:</strong> {usd_bank_details['account_type']}</p>
                <p><strong>Address:</strong> {usd_bank_details['address']}</p>
                """

                Notification.objects.create(
                    user=user,
                    message=notification_message,
                    is_read=False,
                    sender=sender,
                    sender_profile_image=sender_profile_image,
                )

                # Email content
                email_subject = "Payment Instructions for Your AI Chatbot Integration"
                email_content = f"""
                Dear {user.username},

                Please make your payment using one of the following options:

                Naira Bank Transfer:
                Account Name: {naira_bank_details['account_name']}
                Bank: {naira_bank_details['bank']}
                Account Number: {naira_bank_details['account_number']}
                Account Type: {naira_bank_details['account_type']}

                Dollar Bank Transfer:
                Account Name: {usd_bank_details['account_name']}
                Bank: {usd_bank_details['bank']}
                Account Number: {usd_bank_details['account_number']}
                Routing Number: {usd_bank_details['routing_number']}
                Swift Code: {usd_bank_details['swift_code']}
                Account Type: {usd_bank_details['account_type']}
                Address: {usd_bank_details['address']}

                Kindly ensure to include your username as the reference when making the payment.

                Best regards,
                OA Wisdom Digital Firm
                """

                # Render the email template
                email_body = render_to_string('base_email.html', {
                    'email_subject': email_subject,
                    'email_content': email_content,
                    'current_year': timezone.now().year,
                })

                # Function to send email asynchronously
                def send_email_async():
                    send_mail(
                        email_subject,
                        "",  # Empty text message
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        html_message=email_body,  # HTML email content
                    )

                threading.Thread(target=send_email_async).start()

                return HttpResponse("Bank transfer details have been sent to your email. Please check your notifications and complete the payment to proceed.")

            else:
                return JsonResponse({"error": "Invalid payment option selected"}, status=400)

    else:
        ai_form = AIIntegrationRequestForm()

    return render(request, "home.html", {
        "blog_posts": blog_posts,
        "blog_post_form": blog_post_form,
        "comment_form": comment_form,
        "ai_form": ai_form,
    })


def register_business(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            form = BusinessRegistrationForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect("https://paystack.com/pay/oawisdomdigitalfirm")
        else:
            form = BusinessRegistrationForm()
        return render(request, "home.html", {"form": form})
    else:
        return redirect("register")


@csrf_exempt
def purchase_data(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            form = DataPurchaseForm(request.POST)
            if form.is_valid():
                data_purchase = form.save()  # Save the form instance

                # Assuming you have a URL from Paystack to redirect to
                paystack_base_url = "https://paystack.com/pay/owd-data_purchase"

                # Calculate amount based on data plan choice (you may have to adjust this logic based on your plans)
                data_plan_price_map = {
                    "500mb (N200) (30 Days)": 200,
                    "1gb (N400)": 400,
                    "2gb (N700) (30 Days)": 700,
                    "3gb (N1,000) (30 Days)": 1000,
                    "5gb (N1500) (30 Days)": 1500,
                    "10gb (N3,000) (30 Days)": 3000,
                    "300mb (N100) (30 Days)": 100,
                    "1gb (N300) (30 Days)": 300,
                    "5gb (N1,600) (30 Days)": 1600,
                    "2gb (N800) (30 Days)": 800,
                    "3gb (N1,200) (30 Days)": 1200,
                    "5gb (N1,800) (30 Days)": 1800,
                    "10gb (N3,500) (30 Days)": 3500,
                }
                data_plan_price = data_plan_price_map.get(data_purchase.dataPlan, 0)

                # Generate Paystack payment URL with query string parameters
                amount_in_kobo = int(
                    data_plan_price * 1
                )  # Convert Naira to kobo (1 kobo = 1 Naira)
                reference = (
                    data_purchase.id
                )  # Use the ID or any unique identifier as reference
                paystack_url = (
                    f"{paystack_base_url}?amount={amount_in_kobo}&reference={reference}"
                )

                # Return a JsonResponse with the URL to redirect to
                return JsonResponse({"redirect_url": paystack_url}, status=200)
            else:
                # Return form errors if validation fails
                return JsonResponse({"errors": form.errors}, status=400)
        else:
            # Handle invalid request method
            return JsonResponse({"message": "Invalid request method"}, status=405)
    else:
        return redirect("register")


def upload_success(request):
    return render(request, "upload_success.html")


def redirect_if_not_verified(user):
    # Your logic to check if the user is verified
    return not user.is_verified


def digital_marketing(request):
    if request.user.is_authenticated:
        profile_url = reverse("profile", kwargs={"username": request.user.username})
        profile = Profile.objects.get(user=request.user)
        courses = DigitalMarketing.objects.all()
        first, second, third = (
            courses[i] if i < len(courses) else None for i in range(3)
        )
        context = {
            "first": first,
            "second": second,
            "third": third,
            "profile": profile,
            "profile_url": profile_url,  # Pass profile_url to context
        }
        return render(request, "digital_marketing.html", context)
    else:
        return redirect("register")


def error_message(request):
    return render(request, "error_message.html", {"error_message": error_message})


def graphics(request):
    courses = Graphics.objects.all()
    first, second, third = (courses[i] if i < len(courses) else None for i in range(3))
    context = {
        "first": first,
        "second": second,
        "third": third,
    }
    return render(request, "graphics.html", context)


def data_analysis(request):
    courses = Data_analysis.objects.all()
    first, second, third = (courses[i] if i < len(courses) else None for i in range(3))
    context = {
        "first": first,
        "second": second,
        "third": third,
    }
    return render(request, "data_analysis.html", context)


def cyber_security(request):
    courses = CyberSecurity.objects.all()
    first, second, third = (courses[i] if i < len(courses) else None for i in range(3))
    context = {
        "first": first,
        "second": second,
        "third": third,
    }
    return render(request, "cyber_security.html", context)


def video_editing(request):
    courses = VideoEditing.objects.all()
    first, second, third = (courses[i] if i < len(courses) else None for i in range(3))
    context = {
        "first": first,
        "second": second,
        "third": third,
    }
    return render(request, "video_editing.html", context)


def coding(request):
    courses = Coding.objects.all()
    first, second, third = (courses[i] if i < len(courses) else None for i in range(3))
    context = {
        "first": first,
        "second": second,
        "third": third,
    }
    return render(request, "coding.html", context)


def digital_marketing(request):
    courses = DigitalMarketing.objects.all()
    first, second, third = (courses[i] if i < len(courses) else None for i in range(3))
    context = {
        "first": first,
        "second": second,
        "third": third,
    }
    return render(request, "digital_marketing.html", context)


def file_icon_class(file_name):
    if file_name.endswith(".pdf"):
        return "fas fa-file-pdf text-danger"
    elif file_name.endswith(".mp4") or file_name.endswith(".mov"):
        return "fas fa-file-video text-primary"
    elif file_name.endswith(".doc") or file_name.endswith(".docx"):
        return "fas fa-file-word text-primary"
    elif file_name.endswith(".xls") or file_name.endswith(".xlsx"):
        return "fas fa-file-excel text-success"
    elif file_name.endswith(".ppt") or file_name.endswith(".pptx"):
        return "fas fa-file-powerpoint text-danger"
    else:
        return "fas fa-file-alt text-secondary"


def digital_marketing_b(request):
    if request.user.is_authenticated:
        # Check the redirection setting in the admin
        site_setting = SiteSetting.objects.first()  # Assumes there's only one SiteSetting object
        if not request.user.user_profile.is_verified and site_setting.redirect_non_verified:
            return redirect("https://paystack.com/pay/owd-verification")
        courses = Digital_marketing_b.objects.all()
        for course in courses:
            course.icon_class = file_icon_class(course.file.name)
        return render(request, "digital_marketing_b.html", {"courses": courses})
    else:
        return redirect("register")


def digital_marketing_a(request):
    if request.user.is_authenticated:
        # Check if the user's profile is verified
        profile = request.user.user_profile  # Ensure profile is defined

        if profile.is_verified:  # Missing colon was added here
            courses = Digital_marketing_a.objects.all()

            # Add an icon class to each course based on the file name
            for course in courses:
                course.icon_class = file_icon_class(course.file.name)

            # Render the courses in the template
            return render(request, "digital_marketing_a.html", {"courses": courses})
        else:
            return redirect(
                "https://paystack.com/pay/owd-verification"
            )  # Redirect if profile is not verified
    else:
        return redirect("register")  # Redirect to register if not authenticated


def digital_marketing_p(request):
    if request.user.is_authenticated:
        # Check if the user's profile is verified
        profile = request.user.user_profile  # Ensure profile is defined

        if profile.is_verified:  # Check profile verification status
            courses = Digital_marketing_p.objects.all()

            # Add an icon class to each course based on the file name
            for course in courses:
                course.icon_class = file_icon_class(course.file.name)

            # Render the courses in the template
            return render(request, "digital_marketing_p.html", {"courses": courses})
        else:
            # Redirect to verification page if profile is not verified
            return redirect("https://paystack.com/pay/owd-verification")
    else:
        # Redirect to register page if not authenticated
        return redirect("register")


def coding_b(request):
    if request.user.is_authenticated:
        # Check the redirection setting in the admin
        site_setting = SiteSetting.objects.all()[1]  # This gets the second object (index 1)
        if not request.user.user_profile.is_verified and site_setting.redirect_non_verified:
            return redirect("https://paystack.com/pay/owd-verification")
        courses = Coding_b.objects.all()
        for course in courses:
            course.icon_class = file_icon_class(course.file.name)
        return render(request, "coding_b.html", {"courses": courses})
    else:
        return redirect("register")


def coding_a(request):
    if request.user.is_authenticated:
        # Check if the user's profile is verified
        profile = request.user.user_profile  # Ensure profile is defined

        if profile.is_verified:  # Check if profile is verified
            courses = Coding_a.objects.all()

            # Add an icon class to each course based on the file name
            for course in courses:
                course.icon_class = file_icon_class(course.file.name)

            # Render the courses in the template
            return render(request, "coding_a.html", {"courses": courses})
        else:
            return redirect(
                "https://paystack.com/pay/owd-verification"
            )  # Redirect if profile is not verified
    else:
        return redirect("register")  # Redirect to register if not authenticated


def coding_p(request):
    if request.user.is_authenticated:
        # Check if the user's profile is verified
        profile = request.user.user_profile  # Ensure profile is defined

        if profile.is_verified:  # Check if profile is verified
            courses = Coding_p.objects.all()

            # Add an icon class to each course based on the file name
            for course in courses:
                course.icon_class = file_icon_class(course.file.name)

            # Render the courses in the template
            return render(request, "coding_p.html", {"courses": courses})
        else:
            return redirect(
                "https://paystack.com/pay/owd-verification"
            )  # Redirect if profile is not verified
    else:
        return redirect("register")  # Redirect to register if not authenticated


def graphic_b(request):
    if request.user.is_authenticated:
        # Check the redirection setting in the admin
        site_setting = SiteSetting.objects.all()[2]
        if not request.user.user_profile.is_verified and site_setting.redirect_non_verified:
            return redirect("https://paystack.com/pay/owd-verification")
        courses = Graphic_b.objects.all()
        for course in courses:
            course.icon_class = file_icon_class(course.file.name)
        return render(request, "graphics_b.html", {"courses": courses})
    else:
        return redirect("register")


def graphic_a(request):
    if request.user.is_authenticated:
        # Check if the user's profile is verified
        profile = request.user.user_profile  # Ensure profile is defined

        if profile.is_verified:  # Check if profile is verified
            courses = Graphic_a.objects.all()

            # Add an icon class to each course based on the file name
            for course in courses:
                course.icon_class = file_icon_class(course.file.name)

            # Render the courses in the template
            return render(request, "graphics_a.html", {"courses": courses})
        else:
            return redirect(
                "https://paystack.com/pay/owd-verification"
            )  # Redirect if profile is not verified
    else:
        return redirect("register")  # Redirect to register if not authenticated


def graphic_p(request):
    if request.user.is_authenticated:
        # Check if the user's profile is verified
        profile = request.user.user_profile  # Ensure profile is defined

        if profile.is_verified:  # Check if profile is verified
            courses = Graphic_p.objects.all()

            # Add an icon class to each course based on the file name
            for course in courses:
                course.icon_class = file_icon_class(course.file.name)

            # Render the courses in the template
            return render(request, "graphics_p.html", {"courses": courses})
        else:
            return redirect(
                "https://paystack.com/pay/owd-verification"
            )  # Redirect if profile is not verified
    else:
        return redirect("register")  # Redirect to register if not authenticated


def cyber_security_b(request):
    if request.user.is_authenticated:
        # Check the redirection setting in the admin
        site_setting = SiteSetting.objects.all()[3]
        if not request.user.user_profile.is_verified and site_setting.redirect_non_verified:
            return redirect("https://paystack.com/pay/owd-verification")
        courses = CyberSecurity_b.objects.all()
        for course in courses:
            course.icon_class = file_icon_class(course.file.name)
        return render(request, "cyber_security_b.html", {"courses": courses})
    else:
        return redirect("register")


def cyber_security_a(request):
    if request.user.is_authenticated:
        # Check if the user's profile is verified
        profile = request.user.user_profile  # Ensure profile is defined

        if profile.is_verified:  # Check if profile is verified
            courses = CyberSecurity_a.objects.all()

            # Add an icon class to each course based on the file name
            for course in courses:
                course.icon_class = file_icon_class(course.file.name)

            # Render the courses in the template
            return render(request, "cyber_security_a.html", {"courses": courses})
        else:
            return redirect(
                "https://paystack.com/pay/owd-verification"
            )  # Redirect if profile is not verified
    else:
        return redirect("register")  # Redirect to register if not authenticated


def cyber_security_p(request):
    if request.user.is_authenticated:
        # Check if the user's profile is verified
        profile = request.user.user_profile  # Ensure profile is defined

        if profile.is_verified:  # Check if profile is verified
            courses = CyberSecurity_p.objects.all()

            # Add an icon class to each course based on the file name
            for course in courses:
                course.icon_class = file_icon_class(course.file.name)

            # Render the courses in the template
            return render(request, "cyber_security_p.html", {"courses": courses})
        else:
            return redirect(
                "https://paystack.com/pay/owd-verification"
            )  # Redirect if profile is not verified
    else:
        return redirect("register")  # Redirect to register if not authenticated


def video_editing_b(request):
    if request.user.is_authenticated:
        courses = Videoediting_b.objects.all()
        # Check the redirection setting in the admin
        site_setting = SiteSetting.objects.all()[4]
        if not request.user.user_profile.is_verified and site_setting.redirect_non_verified:
            return redirect("https://paystack.com/pay/owd-verification")
        courses = CyberSecurity_b.objects.all()
        for course in courses:
            course.icon_class = file_icon_class(course.file.name)
        return render(request, "video_editing_b.html", {"courses": courses})
    else:
        return redirect("register")


def video_editing_a(request):
    if request.user.is_authenticated:
        # Check if the user's profile is verified
        profile = request.user.user_profile  # Ensure profile is defined

        if profile.is_verified:  # Check if profile is verified
            courses = Videoediting_a.objects.all()

            # Add an icon class to each course based on the file name
            for course in courses:
                course.icon_class = file_icon_class(course.file.name)

            # Render the courses in the template
            return render(request, "video_editing_a.html", {"courses": courses})
        else:
            return redirect(
                "https://paystack.com/pay/owd-verification"
            )  # Redirect if profile is not verified
    else:
        return redirect("register")  # Redirect to register if not authenticated


def video_editing_p(request):
    if request.user.is_authenticated:
        # Check if the user's profile is verified
        profile = request.user.user_profile  # Ensure profile is defined

        if profile.is_verified:  # Check if profile is verified
            courses = Videoediting_p.objects.all()

            # Add an icon class to each course based on the file name
            for course in courses:
                course.icon_class = file_icon_class(course.file.name)

            # Render the courses in the template
            return render(request, "video_editing_p.html", {"courses": courses})
        else:
            return redirect(
                "https://paystack.com/pay/owd-verification"
            )  # Redirect if profile is not verified
    else:
        return redirect("register")  # Redirect to register if not authenticated


def data_analysis(request):
    courses = list(Data_analysis.objects.all())
    first, second, third = (courses[i] if i < len(courses) else None for i in range(3))
    context = {
        "first": first,
        "second": second,
        "third": third,
    }
    return render(request, "data_analysis.html", context)


def data_analysis_b(request):
    if request.user.is_authenticated:
        # Check the redirection setting in the admin
        site_setting = SiteSetting.objects.all()[5]
        if not request.user.user_profile.is_verified and site_setting.redirect_non_verified:
            return redirect("https://paystack.com/pay/owd-verification")

        courses = Data_analysis_b.objects.all()
        for course in courses:
            course.icon_class = file_icon_class(course.file.name)
        return render(request, "data_analysis_b.html", {"courses": courses})
    else:
        return redirect("register")


def data_analysis_a(request):
    if request.user.is_authenticated:
        # Check if the user's profile is verified
        profile = request.user.user_profile  # Ensure profile is defined

        if profile.is_verified:  # Check if profile is verified
            courses = Data_analysis_a.objects.all()

            # Add an icon class to each course based on the file name
            for course in courses:
                course.icon_class = file_icon_class(course.file.name)

            # Render the courses in the template
            return render(request, "data_analysis_a.html", {"courses": courses})
        else:
            return redirect(
                "https://paystack.com/pay/owd-verification"
            )  # Redirect if profile is not verified
    else:
        return redirect("register")  # Redirect to register if not authenticated


def data_analysis_p(request):
    if request.user.is_authenticated:
        # Check if the user's profile is verified
        profile = request.user.user_profile  # Ensure profile is defined

        if profile.is_verified:  # Check if profile is verified
            courses = Data_analysis_p.objects.all()

            # Add an icon class to each course based on the file name
            for course in courses:
                course.icon_class = file_icon_class(course.file.name)

            # Render the courses in the template
            return render(request, "data_analysis_p.html", {"courses": courses})
        else:
            return redirect(
                "https://paystack.com/pay/owd-verification"
            )  # Redirect if profile is not verified
    else:
        return redirect("register")  # Redirect to register if not authenticated


def andriod_apps(request):
    if request.user.is_authenticated:
        site_setting = SiteSetting.objects.all()[6]
        if not request.user.user_profile.is_verified and site_setting.redirect_non_verified:
            return redirect("https://paystack.com/pay/owd-verification")
        courses = Android_app.objects.all()

        # Add an icon class to each course based on the file name
        for course in courses:
            course.icon_class = file_icon_class(course.file.name)

        # Render the courses in the template
        return render(request, "android_apps.html", {"courses": courses})

    else:
        return redirect("register")  # Redirect to register if not authenticated


def desktop_apps(request):
    if request.user.is_authenticated:
        site_setting = SiteSetting.objects.all()[7]
        if not request.user.user_profile.is_verified and site_setting.redirect_non_verified:
            return redirect("https://paystack.com/pay/owd-verification")
        courses = Desktop_app.objects.all()

        # Add an icon class to each course based on the file name
        for course in courses:
            course.icon_class = file_icon_class(course.file.name)

        # Render the courses in the template
        return render(request, "desktop_apps.html", {"courses": courses})

    else:
        return redirect("register")  # Redirect to register if not authenticated


def useful_resources(request):
    if request.user.is_authenticated:
        site_setting = SiteSetting.objects.all()[6]
        if not request.user.user_profile.is_verified and site_setting.redirect_non_verified:
            return redirect("https://paystack.com/pay/owd-verification")

        courses = Useful_resource.objects.all()

        # Add an icon class to each course based on the file name
        for course in courses:
            course.icon_class = file_icon_class(course.file.name)

        return render(request, "useful_resources.html", {
        "courses": courses,
        "current_user": request.user  # Pass the current user to the template
    })

    else:
        return redirect("register")  # Redirect to register if not authenticated


def coding_exam_b(request):
    return render(request, "coding_exam_b.html", {"coding_exam_b": coding_exam_b})


def digital_marketing_exam_b(request):
    return render(
        request,
        "digital_marketing_exam_b.html",
        {"digital_marketing_exam_b": digital_marketing_exam_b},
    )


def graphic_exam_b(request):
    return render(request, "graphic_exam_b.html", {"graphic_exam_b": graphic_exam_b})


def cyber_security_exam_b(request):
    return render(
        request,
        "cyber_security_exam_b.html",
        {"cyber_security_exam_b": cyber_security_exam_b},
    )


def video_editing_exam_b(request):
    return render(
        request,
        "video_editing_exam_b.html",
        {"video_editing_exam_b": video_editing_exam_b},
    )


def data_analysis_exam_b(request):
    return render(
        request,
        "data_analysis_exam_b.html",
        {"data_analysis_exam_b": data_analysis_exam_b},
    )


@require_GET
def search_motivational_books(request):
    search_query = request.GET.get("search_query", "")
    if search_query:
        books = MotivationalBook.objects.filter(
            Q(title__icontains=search_query)
            | Q(author__icontains=search_query)
            | Q(description__icontains=search_query)
        )
        books_data = [
            {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "description": book.description,
                "price_naira": str(book.price),
                "price_dollars": f"{book.price_in_dollars():.2f}",  # Format to 2 decimal places
                "image_url": book.image_url if book.image_url else None,  # Send image URL if available
            }
            for book in books
        ]
        return JsonResponse({"books": books_data})
    return JsonResponse({"books": []})


@csrf_exempt
@require_POST
def submit_material_request(request):
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        try:
            data = json.loads(request.body)
            search_query = data.get("search_query", "").strip()
            if not search_query:
                return JsonResponse({"error": ""}, status=400)

            new_material = Material(
                title=search_query, description="", price=0.0, is_available=True
            )
            new_material.save()
            logger.info(f"Material saved: {search_query}")

            return JsonResponse({"message": "", "material_id": new_material.id})
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON data: {e}")
            return JsonResponse({"error": ""}, status=400)
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return JsonResponse({"error": ""}, status=500)
    else:
        return JsonResponse({"error": ""}, status=400)




@csrf_exempt
def purchase_material(request):
    if (
        request.method == "POST"
        and request.headers.get("X-Requested-With") == "XMLHttpRequest"
    ):
        try:
            data = json.loads(request.body)
            material_id = data.get("material_id")
            payment_option = data.get(
                "payment_option"
            )  # Get payment option from the request

            logger.debug(f"Received material_id: {material_id}")

            if not material_id:
                return JsonResponse({"error": "Material ID not provided"}, status=400)

            try:
                material = Material.objects.get(id=material_id)
                amount = int(material.price * 100)  # Convert amount to Kobo
            except Material.DoesNotExist:
                logger.debug(f"Material with id {material_id} not found.")
                try:
                    motivational_book = MotivationalBook.objects.get(id=material_id)
                    amount = int(
                        motivational_book.price * 1
                    )  # Convert amount to Kobo
                except MotivationalBook.DoesNotExist:
                    logger.debug(f"MotivationalBook with id {material_id} not found.")
                    return JsonResponse({"error": "Material not found"}, status=404)

            user = request.user  # Assume the user is logged in
            if payment_option == "paystack":
                # Paystack payment URL
                paystack_url = f"https://paystack.com/pay/owd-digital-materials?amount={amount}&reference={material_id}"
                return JsonResponse({"redirect_url": paystack_url})

            elif payment_option == "PayPal":
                # PayPal payment URL
                paypal_url = (
                    "https://paypal.me/oawisdomdigitalfirm?country.x=LS&locale.x=en_US"
                )
                return JsonResponse({"redirect_url": paypal_url})

            elif payment_option == "USD_bank_transfer":
                sender = User.objects.filter(is_superuser=True).first()

                if not sender:
                    return JsonResponse({"error": "No admin user found to send notifications."}, status=500)

                sender_profile_image = Profile.objects.get(user=sender).profile_image.url

                # Naira bank details
                naira_bank_details = {
                    "account_name": "Oti Alid Wisdom",
                    "bank": "MoniePoint Microfinance Bank",
                    "account_number": "7081668601",
                    "account_type": "Savings",
                }

                # USD bank details
                usd_bank_details = {
                    "account_name": "ALID WISDOM OTI",
                    "bank": "WELLS FARGO BANK, N.A.",
                    "account_number": "1234567890",
                    "routing_number": "987654321",
                    "swift_code": "ABCDUS33",
                    "account_type": "Checking",
                    "address": "9450 Southwest Gemini Drive, Beaverton, OR, 97008, USA.",
                }

                # Combined notification message with Naira and USD details
                notification_message = f"""
                <h6>Make your transfer either in Naira or Dollar:</h6>
                <h6><strong>Naira Bank Transfer:</strong></h6>
                <p><strong>Account Name:</strong> {naira_bank_details['account_name']}</p>
                <p><strong>Bank:</strong> {naira_bank_details['bank']}</p>
                <p><strong>Account Number:</strong> {naira_bank_details['account_number']}</p>
                <p><strong>Account Type:</strong> {naira_bank_details['account_type']}</p>
                <hr>
                <h6><strong>Dollar Bank Transfer:</strong></h6>
                <p><strong>Account Name:</strong> {usd_bank_details['account_name']}</p>
                <p><strong>Bank:</strong> {usd_bank_details['bank']}</p>
                <p><strong>Account Number:</strong> {usd_bank_details['account_number']}</p>
                <p><strong>Routing Number:</strong> {usd_bank_details['routing_number']}</p>
                <p><strong>Swift Code:</strong> {usd_bank_details['swift_code']}</p>
                <p><strong>Account Type:</strong> {usd_bank_details['account_type']}</p>
                <p><strong>Address:</strong> {usd_bank_details['address']}</p>
                """

                Notification.objects.create(
                    user=user,
                    message=notification_message,
                    is_read=False,
                    sender=sender,
                    sender_profile_image=sender_profile_image,
                )

                # Email content
                email_subject = "Payment Instructions for Your Material to Purchase"
                email_content = f"""
                Dear {user.username},

                Please make your payment using one of the following options:

                Naira Bank Transfer:
                Account Name: {naira_bank_details['account_name']}
                Bank: {naira_bank_details['bank']}
                Account Number: {naira_bank_details['account_number']}
                Account Type: {naira_bank_details['account_type']}

                Dollar Bank Transfer:
                Account Name: {usd_bank_details['account_name']}
                Bank: {usd_bank_details['bank']}
                Account Number: {usd_bank_details['account_number']}
                Routing Number: {usd_bank_details['routing_number']}
                Swift Code: {usd_bank_details['swift_code']}
                Account Type: {usd_bank_details['account_type']}
                Address: {usd_bank_details['address']}

                Kindly ensure to include your username as the reference when making the payment.

                Best regards,
                OA Wisdom Digital Firm
                """

                # Render the email template
                email_body = render_to_string('base_email.html', {
                    'email_subject': email_subject,
                    'email_content': email_content,
                    'current_year': timezone.now().year,
                })

                # Function to send email asynchronously
                def send_email_async():
                    send_mail(
                        email_subject,
                        "",  # Empty text message
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        html_message=email_body,  # HTML email content
                    )

                threading.Thread(target=send_email_async).start()

                return HttpResponse("Bank transfer details have been sent to your email. Please check your notifications and complete the payment to proceed.")

            else:
                # If no specific payment option is selected, return an error
                return JsonResponse({"error": "Invalid payment option selected"}, status=400)

        except json.JSONDecodeError:
            logger.error("Invalid JSON")
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"Error processing purchase: {e}")
            return JsonResponse({"error": "Internal Server Error"}, status=500)
    else:
        return JsonResponse({"error": "Invalid request"}, status=400)


def about(request):
    return render(request, "about.html", {"about": about})


def terms(request):
    return render(request, "terms.html", {"terms": terms})


def privacy_policy(request):
    return render(request, "privacy_policy.html", {"privacy_policy": privacy_policy})


def send_email_async(subject, message, from_email, recipient_list):
    # Render the email using base_email.html
    email_body = render_to_string('base_email.html', {
        'email_subject': subject,
        'email_content': message,
        'current_year': timezone.now().year,
    })

    # Send email asynchronously
    def send():
        for recipient in recipient_list:
            try:
                send_mail(
                    subject,
                    "",  # Empty plain text message
                    from_email,
                    [recipient],
                    html_message=email_body  # Send as HTML
                )
            except Exception as e:
                logger.error(f"Failed to send email to {recipient}: {e}")

    # Start email sending in a separate thread
    threading.Thread(target=send).start()


@login_required(login_url='/users/register/')
def like_post(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    liked = False

    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True

        # Create a notification for the post owner
        Notification.objects.create(
            user=post.author,
            message=f"{request.user.username} liked your post: {post.title}.",
            is_read=False,
            sender=request.user,
            sender_profile_image=(
                request.user.user_profile.profile_image.url
                if request.user.user_profile.profile_image
                else None
            ),
            chat=None,  # Optional, if you have chat functionality
        )

        # Send an email to the post owner after the transaction is committed
        transaction.on_commit(lambda: threading.Thread(
            target=send_email_async,
            args=(
                "New Like on Your Post",
                f"Your post '{post.title}' has received a new like from {request.user.username}.",
                settings.DEFAULT_FROM_EMAIL,
                [post.author.email],
            )
        ).start())

    # Return the response immediately after like operation
    return JsonResponse({"liked": liked, "total_likes": post.total_likes()})

@login_required(login_url='/users/register/')
def add_comment(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    success = False

    if request.method == "POST":
        content = request.POST.get("content")
        if content:
            comment = Comment.objects.create(
                post=post, author=request.user, content=content
            )
            success = True

            # Create a notification for the post owner
            Notification.objects.create(
                user=post.author,
                message=f"{request.user.username} commented on your post: {post.title}.",
                is_read=False,
                sender=request.user,
                sender_profile_image=(
                    request.user.user_profile.profile_image.url
                    if request.user.user_profile.profile_image
                    else None
                ),
                chat=None,  # Optional, if you have chat functionality
            )

            # Send an email to the post owner in a separate thread
            threading.Thread(
                target=send_email_async,
                args=(
                    "New Comment on Your Post",
                    f"Your post '{post.title}' has received a new comment from {request.user.username}: {content}",
                    settings.DEFAULT_FROM_EMAIL,
                    [post.author.email],
                )
            ).start()

    return JsonResponse({"success": success})

@login_required(login_url='/users/register/')
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author or comment.post.author == request.user:
        comment.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})

@login_required(login_url='/users/register/')
def share_post(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    shared_link = request.build_absolute_uri(post.get_absolute_url())

    # Create a notification for the post owner
    Notification.objects.create(
        user=post.author,
        message=f"Your post '{post.title}' has been shared.",
        is_read=False,
        sender=request.user,
        sender_profile_image=(
            request.user.user_profile.profile_image.url
            if request.user.user_profile.profile_image
            else None
        ),
        chat=None  # Optional, if you have chat functionality
    )

    # Send an email to the post owner in a separate thread
    threading.Thread(
        target=send_email_async,
        args=(
            "Your Post Has Been Shared",
            f"Your post '{post.title}' has been shared. View it here: {shared_link}",
            settings.DEFAULT_FROM_EMAIL,
            [post.author.email],
        )
    ).start()

    # Implement additional sharing functionality here, e.g., copying the link to clipboard
    return JsonResponse({"shared_link": shared_link, "success": True})


@login_required(login_url='/users/register/')
def edit_post(request, post_id):
    # Ensure the user can only edit their own posts
    post = get_object_or_404(BlogPost, id=post_id, author=request.user)

    if request.method == "POST":
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            # Redirect to profile or post detail page after successful edit
            return redirect("profile", username=request.user.username)
        else:
            # Return form errors if the form is invalid
            return JsonResponse({"success": False, "error": form.errors}, status=400)

    else:
        form = BlogPostForm(instance=post)

    return render(request, "edit_post.html", {"form": form, "post": post})


@login_required(login_url='/users/register/')
def delete_post(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(BlogPost, id=post_id, author=request.user)
        post.delete()
        return JsonResponse({"success": True})
    else:
        return HttpResponseBadRequest("Invalid request")


def post_detail(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    profile = None
    subscriptions = []

    if request.user.is_authenticated:
        profile = Profile.objects.filter(user=request.user).first()
        subscriptions = [
            post.author.id
            for post in BlogPost.objects.all()
            if Profile.objects.filter(
                user=post.author, subscribers=request.user
            ).exists()
        ]

    # Get tags from the post
    tags = [tag.strip().lower() for tag in post.tags.split(",")] if post.tags else []

    # Build Q objects for each tag
    query = Q()
    for tag in tags:
        query |= Q(title__icontains=tag) | Q(content__icontains=tag)

    # Fetch related posts based on tags
    related_posts = BlogPost.objects.filter(query).exclude(id=post_id).distinct()

    context = {
        "post": post,
        "user": request.user,
        "profile": profile,
        "subscriptions": subscriptions,
        "related_posts": related_posts,
    }
    return render(request, "post_detail.html", context)
