from django.contrib.auth.models import User
from django.db import models
from django.db import models
from datetime import datetime
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone
import uuid
from django.conf import settings

class TelegramChannel(models.Model):
    channel_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

class TelegramPost(models.Model):
    message_id = models.CharField(max_length=255, unique=True)
    text = models.TextField()
    date = models.DateTimeField()
    channel = models.ForeignKey(TelegramChannel, on_delete=models.CASCADE)

class SchedulerControl(models.Model):
    """
    Dummy model to control the scheduler from the admin panel.
    """
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=False, help_text="Indicates if the scheduler should be running.")

    def __str__(self):
        return self.name

class YouTubeChannel(models.Model):
    channel_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, blank=True, help_text="Optional: Name of the channel")

    def __str__(self):
        return self.name or self.channel_id

class YouTubePost(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    video_id = models.CharField(max_length=255)  # Store only the video ID
    published_at = models.DateTimeField()
    thumbnail_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='youtube_likes', blank=True)

    @property
    def total_likes(self):
        return self.likes.count()

    @property
    def video_url(self):
        return f'https://www.youtube.com/watch?v={self.video_id}'

    def __str__(self):
        return self.title
    

class YoutubeComment(models.Model):
    youtube_post = models.ForeignKey(YouTubePost, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.youtube_post.title}'


class SiteSetting(models.Model):
    name = models.CharField(max_length=255)
    redirect_non_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Site Settings"

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

class MarketplaceEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    occupation = models.CharField(max_length=255)
    sell_or_service = models.CharField(max_length=255)
    product_or_service = models.CharField(max_length=255)
    office_address = models.CharField(max_length=255)
    years_experience = models.IntegerField()
    specialty = models.CharField(
        max_length=50,
        choices=[
            ("beginner", "Beginner"),
            ("amateur", "Amateur"),
            ("professional", "Professional"),
        ],
    )
    certification = models.FileField(upload_to="certifications/", blank=True, null=True)
    phone_number1 = models.CharField(max_length=15)
    phone_number2 = models.CharField(max_length=15, blank=True, null=True)
    portfolio_link = models.URLField(blank=True, null=True)


class MarketplaceItem(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="marketplace_items"
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    view_count = models.PositiveIntegerField(default=0)  # Add view_count field

    def __str__(self):
        return self.name

    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=["view_count"])

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse(
            "marketplace_item_detail", kwargs={"pk": self.pk}
        )  # Ensure you have a detail view set up


class MarketplaceItemImage(models.Model):
    item = models.ForeignKey(
        MarketplaceItem, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="marketplace/images/")

    def __str__(self):
        return f"Image for {self.item.name}"


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
    items = models.ManyToManyField(MarketplaceItem, related_name="wishlists")

    def __str__(self):
        return f"Wishlist for {self.user.username}"


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    def total_items(self):
        return self.cart_items.count()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    item = models.ForeignKey(MarketplaceItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item.name} (x{self.quantity})"

    def total_price(self):
        return self.item.price * self.quantity


class Adsposts(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='photos/')
    header = models.CharField(max_length=100)
    subheader = models.CharField(max_length=100)
    description1 = models.CharField(max_length=1000, blank=True, null=True)
    description2 = models.CharField(max_length=1000, blank=True, null=True)
    description3 = models.CharField(max_length=1000, blank=True, null=True)
    description4 = models.CharField(max_length=1000, blank=True, null=True)
    description5 = models.CharField(max_length=1000, blank=True, null=True)
    description6 = models.CharField(max_length=1000, blank=True, null=True)
    description7 = models.CharField(max_length=1000, blank=True, null=True)
    description8 = models.CharField(max_length=1000, blank=True, null=True)
    conclusion = models.CharField(max_length=1000, blank=True, null=True)
    button = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

class DigitalMarketing(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='photos/')
    header = models.CharField(max_length=100)
    description1 = models.CharField(max_length=1000)
    description2 = models.CharField(max_length=1000)
    description3 = models.CharField(max_length=1000)
    description4 = models.CharField(max_length=1000)
    description5 = models.CharField(max_length=1000)
    description6 = models.CharField(max_length=1000)
    button = models.CharField(max_length=1000)

    def __str__(self):
        return f"{self.header} - {self.description1}"

class Coding(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='photos/')
    header = models.CharField(max_length=100)
    description1 = models.CharField(max_length=1000)
    description2 = models.CharField(max_length=1000)
    description3 = models.CharField(max_length=1000)
    description4 = models.CharField(max_length=1000)
    description5 = models.CharField(max_length=1000)
    description6 = models.CharField(max_length=1000)
    button = models.CharField(max_length=1000)

    def __str__(self):
        return f"{self.header} - {self.description1}"

class Graphics(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='photos/')
    header = models.CharField(max_length=100)
    description1 = models.CharField(max_length=1000)
    description2 = models.CharField(max_length=1000)
    description3 = models.CharField(max_length=1000)
    description4 = models.CharField(max_length=1000)
    description5 = models.CharField(max_length=1000)
    description6 = models.CharField(max_length=1000)
    button = models.CharField(max_length=1000)

    def __str__(self):
        return f"{self.header} - {self.description1}"

class VideoEditing(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='photos/')
    header = models.CharField(max_length=100)
    description1 = models.CharField(max_length=1000)
    description2 = models.CharField(max_length=1000)
    description3 = models.CharField(max_length=1000)
    description4 = models.CharField(max_length=1000)
    description5 = models.CharField(max_length=1000)
    description6 = models.CharField(max_length=1000)
    button = models.CharField(max_length=1000)

    def __str__(self):
        return f"{self.header} - {self.description1}"

class CyberSecurity(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='photos/')
    header = models.CharField(max_length=100)
    description1 = models.CharField(max_length=1000)
    description2 = models.CharField(max_length=1000)
    description3 = models.CharField(max_length=1000)
    description4 = models.CharField(max_length=1000)
    description5 = models.CharField(max_length=1000)
    description6 = models.CharField(max_length=1000)
    button = models.CharField(max_length=1000)

    def __str__(self):
        return f"{self.header} - {self.description1}"

class Digital_marketing_b(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/')
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class Digital_marketing_a(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class Digital_marketing_p(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class Coding_b(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class Coding_a(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class Coding_p(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class Graphic_b(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class Graphic_a(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class Graphic_p(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class CyberSecurity_b(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class CyberSecurity_a(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class CyberSecurity_p(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class Videoediting_b(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class Videoediting_a(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class Videoediting_p(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class BusinessRegistration(models.Model):
    BUSINESS_TYPES = [
        ('soleProprietorship', 'Sole Proprietorship'),
        ('partnership', 'Partnership'),
        ('llc', 'Limited Liability Company (LLC)'),
        ('plc', 'Public Limited Company (PLC)'),
        ('ngo', 'Non-Governmental Organization (NGO)'),
        ('incorporatedTrustee', 'Incorporated Trustee'),
        ('cooperativeSociety', 'Cooperative Society'),
    ]

    business_type = models.CharField(max_length=50, choices=BUSINESS_TYPES)
    business_name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return f"{self.business_type} - {self.business_name}"

class WebsiteRequirement(models.Model):
    website_type = models.CharField(max_length=100)
    business_type = models.CharField(max_length=100)
    features = models.TextField()
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    budget_naira = models.DecimalField(max_digits=10, decimal_places=2)
    budget_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Add this field

    def save(self, *args, **kwargs):
        if self.budget_naira and not self.budget_usd:
            exchange_rate = 1500 
            self.budget_usd = float(self.budget_naira) / exchange_rate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.website_type} - {self.business_type}"

class FacebookAdRequirement(models.Model):
    AD_OBJECTIVES = [
        ('automatic', 'Automatic'),
        ('more_messages_whatsapp', 'Get more messages on WhatsApp'),
        ('more_website_visitors', 'Get more website visitors'),
        ('more_calls', 'Get more calls'),
        ('more_followers', 'Get more followers'),
        ('grow_customer_base', 'Grow customer base'),
    ]

    ad_objective = models.CharField(max_length=50, choices=AD_OBJECTIVES)
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True)
    message_template = models.TextField(blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)
    call_to_action = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    call_schedule = models.TextField(blank=True, null=True)
    social_media_platform = models.CharField(max_length=50, blank=True, null=True)
    target_audience = models.TextField(blank=True, null=True)
    customer_base_goal = models.CharField(max_length=255, blank=True, null=True)
    growth_strategy = models.TextField(blank=True, null=True)
    target_age_range = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    ads_display_location = models.CharField(max_length=255, blank=True, null=True)
    budget_naira = models.PositiveIntegerField()  # Renamed to differentiate from budget
    budget_dollar = models.FloatField(blank=True, null=True)  # Calculated field for dollar equivalent
    estimated_reach = models.PositiveIntegerField(blank=True, null=True)  # Estimated reach based on budget and ad type
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    media_file = models.FileField(upload_to='uploads/', blank=True, null=True)
    days_duration = models.PositiveIntegerField(default=1)  # New field for duration in days
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ad_objective

    def save(self, *args, **kwargs):
        if self.budget_naira:
            self.budget_dollar = self.budget_naira / 1  # Assuming an exchange rate of 410 Naira to Dollar
        super().save(*args, **kwargs)

class DomainHostingRequirement(models.Model):
    DOMAIN_TYPES = [
        ('com', '.com'),
        ('net', '.net'),
        ('org', '.org'),
        ('ng', '.ng'),
        ('info', '.info'),
        ('io', '.io'),
        ('tech', '.tech'),
        # Add more domain types as needed
    ]

    HOSTING_PACKAGES = [
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('business', 'Business'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]

    domainName = models.CharField(max_length=255)
    domainType = models.CharField(max_length=10, choices=DOMAIN_TYPES)
    hostingPlan = models.CharField(max_length=50, choices=HOSTING_PACKAGES)
    additionalServices = models.TextField(blank=True, null=True)
    websiteFiles = models.FileField(upload_to='uploads/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.domainName} - {self.hostingPlan}"

class Data_analysis(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='photos/')
    header = models.CharField(max_length=100)
    description1 = models.CharField(max_length=1000)
    description2 = models.CharField(max_length=1000)
    description3 = models.CharField(max_length=1000)
    description4 = models.CharField(max_length=1000)
    description5 = models.CharField(max_length=1000)
    description6 = models.CharField(max_length=1000)
    button = models.CharField(max_length=1000)

    def __str__(self):
        return f"{self.header} - {self.description1}"

class Data_analysis_b(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class Data_analysis_a(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class Data_analysis_p(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class Android_app(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class Desktop_app(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class Useful_resource(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    button = models.CharField(max_length=1000)
    author = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to="blog_images/")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name="liked_posts", blank=True)
    tags = models.CharField(
        max_length=255, blank=True, help_text="Comma-separated list of tags"
    )
    is_approved = models.BooleanField(default=False)

    def total_likes(self):
        return self.likes.count()

    def get_absolute_url(self):
        return f"/post/{self.id}/"


class DataPurchase(models.Model):
    phone_number = models.CharField(max_length=15)
    network_choices = [
        ('MTN', 'MTN'),
        ('GLO', 'GLO'),
        ('AIRTEL', 'AIRTEL'),
        ('9MOBILE', '9MOBILE'),
    ]
    network = models.CharField(max_length=10, choices=network_choices)
    
    data_plan_choices = [
        ('500mb (N200) (30 Days)', '500mb (N200) (30 Days)'),
        ('1gb (N400)', '1gb (N400)'),
        ('2gb (N700) (30 Days)', '2gb (N700) (30 Days)'),
        ('3gb (N1,000) (30 Days)', '3gb (N1,000) (30 Days)'),
        ('5gb (N1500) (30 Days)', '5gb (N1500) (30 Days)'),
        ('10gb (N3,000) (30 Days)', '10gb (N3,000) (30 Days)'),
        ('300mb (N100) (30 Days)', '300mb (N100) (30 Days)'),
        ('1gb (N300) (30 Days)', '1gb (N300) (30 Days)'),
        ('5gb (N1,600) (30 Days)', '5gb (N1,600) (30 Days)'),
        ('2gb (N800) (30 Days)', '2gb (N800) (30 Days)'),
        ('3gb (N1,200) (30 Days)', '3gb (N1,200) (30 Days)'),
        ('5gb (N1,800) (30 Days)', '5gb (N1,800) (30 Days)'),
        ('10gb (N3,500) (30 Days)', '10gb (N3,500) (30 Days)'),
        ('500mb (N200) (30 Days)', '500mb (N200) (30 Days)'),
        ('2gb (N800) (30 Days)', '2gb (N800) (30 Days)'),
        ('3gb (N1,100) (30 Days)', '3gb (N1,100) (30 Days)'),
        ('5gb (N1,500) (30 Days)', '5gb (N1,500) (30 Days)'),
        ('10gb (N3,000) (30 Days)', '10gb (N3,000) (30 Days)'),
    ]
    dataPlan = models.CharField(max_length=50, choices=data_plan_choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone_number} - {self.network} - {self.dataPlan}"

class Material(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class MotivationalBook(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=0)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    image_url = models.URLField(max_length=12000, blank=True)  # Field to store external image URL

    def __str__(self):
        return self.title

    def price_in_dollars(self):
        exchange_rate = 1500  # Update with actual exchange rate
        return self.price / exchange_rate


class AIIntegrationRequest(models.Model):
    title = models.CharField(max_length=255)
    website_or_app = models.CharField(max_length=255)
    description = models.TextField()
    media_file = models.FileField(upload_to='uploads/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# Here is for the form submission of the upload request
class Message(models.Model):
    name = models.CharField(max_length=1000)
    text = models.TextField()

    def __str__(self):
        return self.name


class FileUpload(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="uploads/")  # Change from 'photos/' to 'uploads/'

    def __str__(self):
        return f"{self.file.name} ({self.message.name})"


class Comment(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        User, related_name="subscriptions", on_delete=models.CASCADE
    )
    subscribed_to = models.ForeignKey(
        User, related_name="subscribers", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("subscriber", "subscribed_to")

