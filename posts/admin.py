from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.html import format_html
import logging
from django.contrib.auth.admin import UserAdmin
from .models import (
    VideoEditing,
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
    Message,
    FileUpload,
    MarketplaceEntry,
    MarketplaceItem,
    MarketplaceItemImage,
    Wishlist,
    Cart,
    CartItem,
    SiteSetting,
    YoutubeComment,
)
from .forms import FacebookAdRequirementForm

from .models import YouTubePost, YouTubeChannel
from django.core.management import call_command
from django.contrib import messages
from .scheduler import start_scheduler, stop_scheduler
from .models import SchedulerControl

@admin.register(YoutubeComment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('youtube_post', 'user', 'created_at', 'text')
    search_fields = ('youtube_post__title', 'user__username', 'text')

@admin.register(YouTubeChannel)
class YouTubeChannelAdmin(admin.ModelAdmin):
    list_display = ('channel_id', 'name')
    search_fields = ('channel_id', 'name')
    actions = ['fetch_youtube_videos']

    def fetch_youtube_videos(self, request, queryset):
        # Call the management command to fetch YouTube videos
        call_command('fetch_youtube_videos')
        messages.success(request, "YouTube videos have been fetched successfully.")

    fetch_youtube_videos.short_description = "Fetch YouTube videos"

@admin.register(SchedulerControl)
class SchedulerControlAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    actions = ['start_scheduler_action', 'stop_scheduler_action']

    def start_scheduler_action(self, request, queryset):
        """
        Admin action to manually start the scheduler.
        """
        try:
            start_scheduler()
            queryset.update(is_active=True)
            self.message_user(request, "Scheduler started successfully.", level=messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Error starting scheduler: {str(e)}", level=messages.ERROR)

    def stop_scheduler_action(self, request, queryset):
        """
        Admin action to manually stop the scheduler.
        """
        try:
            stop_scheduler()
            queryset.update(is_active=False)
            self.message_user(request, "Scheduler stopped successfully.", level=messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Error stopping scheduler: {str(e)}", level=messages.ERROR)

    def save_model(self, request, obj, form, change):
        """
        Override save_model to ensure the scheduler is started or stopped based on is_active field.
        """
        if obj.is_active:
            start_scheduler()
        else:
            stop_scheduler()
        super().save_model(request, obj, form, change)

    start_scheduler_action.short_description = "Start Scheduler"
    stop_scheduler_action.short_description = "Stop Scheduler"

@admin.register(YouTubePost)
class YouTubePostAdmin(admin.ModelAdmin):
    list_display = ('title', 'video_url', 'published_at', 'thumbnail_url')
    list_filter = ('published_at',)
    search_fields = ('title', 'description', 'video_id')
    fields = ('title', 'description', 'video_id', 'published_at', 'thumbnail_url')

class MarketplaceEntryAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "occupation",
        "sell_or_service",
        "product_or_service",
        "office_address",
        "years_experience",
        "specialty",
        "portfolio_link",
    )
    search_fields = (
        "user__username",
        "occupation",
        "product_or_service",
        "office_address",
        "portfolio_link",
    )
    list_filter = ("sell_or_service", "specialty")


class VideoEditingAdmin(admin.ModelAdmin):
    list_display = ('name', 'header', 'description1')
    search_fields = ('name', 'header', 'description1', 'description2', 'description3', 'description4', 'description5', 'description6')
    list_filter = ('header',)
    ordering = ('name',)

class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following')

class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'date_uploaded')
    search_fields = ('title',)

class FriendAdmin(admin.ModelAdmin):
    list_display = ('user',)

class AdspostsAdmin(admin.ModelAdmin):
    list_display = ('name', 'header')

class MessageAdmin(admin.ModelAdmin):
    list_display = ('name',)

class DigitalMarketingAdmin(admin.ModelAdmin):
    list_display = ('name', 'header')

class CodingAdmin(admin.ModelAdmin):
    list_display = ('name', 'header')

class GraphicsAdmin(admin.ModelAdmin):
    list_display = ('name', 'header')

class CyberSecurityAdmin(admin.ModelAdmin):
    list_display = ('name', 'header')

class DigitalMarketingBAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class DigitalMarketingAAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class DigitalMarketingPAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class CodingBAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class CodingAAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class CodingPAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class GraphicBAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class GraphicAAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class GraphicPAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class CyberSecurityBAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class CyberSecurityAAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class CyberSecurityPAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class VideoeditingBAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class VideoeditingAAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class VideoeditingPAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class BusinessRegistrationAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'business_type')

class WebsiteRequirementAdmin(admin.ModelAdmin):
    list_display = ('website_type', 'business_type', 'contact_email', 'contact_phone', 'budget_naira', 'budget_usd', 'created_at_display')
    search_fields = ('business_type', 'contact_email', 'website_type')
    list_filter = ('website_type', 'created_at')
    ordering = ('-id',)  # Assuming 'id' is the primary key or another suitable field for ordering

    def created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S') if obj.created_at else None
    created_at_display.admin_order_field = 'created_at'
    created_at_display.short_description = 'Created At'

class FacebookAdRequirementAdmin(admin.ModelAdmin):
    list_display = ['ad_objective', 'budget_naira', 'budget_dollar', 'estimated_reach', 'created_at']
    search_fields = ['ad_objective', 'title']
    list_filter = ['ad_objective', 'created_at']
    readonly_fields = ['budget_dollar', 'estimated_reach', 'created_at']

class DomainHostingRequirementAdmin(admin.ModelAdmin):
    list_display = ('domainName', 'domainType', 'hostingPlan', 'created_at')
    search_fields = ('domainName', 'domainType', 'hostingPlan')
    list_filter = ('domainType', 'hostingPlan')
    date_hierarchy = 'created_at'

class DataAnalysisAdmin(admin.ModelAdmin):
    list_display = ('name', 'header')

class DataAnalysisBAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class DataAnalysisAAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class DataAnalysisPAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class AndroidAppAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class DesktopAppAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class UsefulResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "created_at", "total_likes")
    list_filter = ("created_at", "author")
    search_fields = ("title", "content", "tags")  # Include tags in search fields
    fields = ("title", "content", "image", "tags")  # Ensure tags are in the form
    filter_horizontal = ()  # Optionally, use this for many-to-many fields if needed


class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'content', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('content', 'user__username', 'post__title')

class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')

class ScheduledMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'scheduled_time', 'sent')

class DataPurchaseAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'network', 'dataPlan', 'created_at')

class MaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'is_available', 'created_at')

class MotivationalBookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'price', 'created_at')

class AIIntegrationRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'website_or_app', 'description', 'media_file', 'created_at')
    search_fields = ('title', 'website_or_app')


class FileUploadInline(admin.TabularInline):
    model = FileUpload
    extra = 1  # Number of empty forms displayed by default


class MessageAdmin(admin.ModelAdmin):
    list_display = ("name", "get_files_count", "text_preview")
    search_fields = ("name", "text")
    inlines = [FileUploadInline]

    def get_files_count(self, obj):
        return obj.files.count()

    get_files_count.short_description = "Files Count"

    def text_preview(self, obj):
        return (obj.text[:50] + "...") if len(obj.text) > 50 else obj.text

    text_preview.short_description = "Text Preview"


class FileUploadAdmin(admin.ModelAdmin):
    list_display = ("message", "file_name", "file_size", "uploaded_at")
    search_fields = ("message__name", "file")
    list_filter = ("message",)

    def file_name(self, obj):
        return obj.file.name

    file_name.short_description = "File Name"

    def file_size(self, obj):
        size_kb = obj.file.size / 1024
        return f"{size_kb:.2f} KB"

    file_size.short_description = "File Size"

    def uploaded_at(self, obj):
        return obj.file.field.upload_to

    uploaded_at.short_description = "Uploaded Path"


class MarketplaceItemImageInline(admin.TabularInline):
    model = MarketplaceItemImage
    extra = 1  # Show 1 empty form for additional image upload


class MarketplaceItemAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "price", "user", "created_at")
    search_fields = ("name", "description", "user__username")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
    inlines = [MarketplaceItemImageInline]  # Display images inline


# Define the admin class for Wishlist
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "item_count")
    search_fields = ("user__username",)
    filter_horizontal = ("items",)

    def item_count(self, obj):
        return obj.items.count()

    item_count.short_description = "Number of Items"


# Define the admin class for Cart
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "total_items")
    search_fields = ("user__username",)
    readonly_fields = ("created_at",)

    def total_items(self, obj):
        return obj.cart_items.count()

    total_items.short_description = "Number of Items"


# Define the admin class for CartItem
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "item", "quantity", "added_at", "total_price")
    search_fields = ("cart__user__username", "item__name")
    readonly_fields = ("added_at",)

    def total_price(self, obj):
        return obj.item.price * obj.quantity

    total_price.short_description = "Total Price"


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'redirect_non_verified', 'created_at')
    readonly_fields = ('created_at',)

    
# Register the admin classes with the corresponding models
admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(MarketplaceItem, MarketplaceItemAdmin)
admin.site.register(MarketplaceItemImage)
admin.site.register(MarketplaceEntry, MarketplaceEntryAdmin)
admin.site.register(FileUpload, FileUploadAdmin)
admin.site.register(VideoEditing, VideoEditingAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Adsposts, AdspostsAdmin)
admin.site.register(DigitalMarketing, DigitalMarketingAdmin)
admin.site.register(Coding, CodingAdmin)
admin.site.register(Graphics, GraphicsAdmin)
admin.site.register(CyberSecurity, CyberSecurityAdmin)
admin.site.register(Digital_marketing_b, DigitalMarketingBAdmin)
admin.site.register(Digital_marketing_a, DigitalMarketingAAdmin)
admin.site.register(Digital_marketing_p, DigitalMarketingPAdmin)
admin.site.register(Coding_b, CodingBAdmin)
admin.site.register(Coding_a, CodingAAdmin)
admin.site.register(Coding_p, CodingPAdmin)
admin.site.register(Graphic_b, GraphicBAdmin)
admin.site.register(Graphic_a, GraphicAAdmin)
admin.site.register(Graphic_p, GraphicPAdmin)
admin.site.register(CyberSecurity_b, CyberSecurityBAdmin)
admin.site.register(CyberSecurity_a, CyberSecurityAAdmin)
admin.site.register(CyberSecurity_p, CyberSecurityPAdmin)
admin.site.register(Videoediting_b, VideoeditingBAdmin)
admin.site.register(Videoediting_a, VideoeditingAAdmin)
admin.site.register(Videoediting_p, VideoeditingPAdmin)
admin.site.register(BusinessRegistration, BusinessRegistrationAdmin)
admin.site.register(WebsiteRequirement, WebsiteRequirementAdmin)
admin.site.register(FacebookAdRequirement, FacebookAdRequirementAdmin)
admin.site.register(DomainHostingRequirement, DomainHostingRequirementAdmin)
admin.site.register(Data_analysis, DataAnalysisAdmin)
admin.site.register(Data_analysis_b, DataAnalysisBAdmin)
admin.site.register(Data_analysis_a, DataAnalysisAAdmin)
admin.site.register(Data_analysis_p, DataAnalysisPAdmin)
admin.site.register(Android_app, AndroidAppAdmin)
admin.site.register(Desktop_app, DesktopAppAdmin)
admin.site.register(Useful_resource, UsefulResourceAdmin)
admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(DataPurchase, DataPurchaseAdmin)
admin.site.register(Material, MaterialAdmin)
admin.site.register(MotivationalBook, MotivationalBookAdmin)
admin.site.register(AIIntegrationRequest, AIIntegrationRequestAdmin)
