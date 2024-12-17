from django import forms
from .widgets import CustomFileInput
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
    Message,
    MarketplaceEntry,
    MarketplaceItemImage,
    Useful_resource,
    YoutubeComment,
)
from .widgets import MultipleFileInput
from django.forms import modelformset_factory

class YoutubeCommentForm(forms.ModelForm):
    class Meta:
        model = YoutubeComment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add a comment...'}),
        }

class UsefulResourceForm(forms.ModelForm):
    class Meta:
        model = Useful_resource
        fields = ['name', 'description', 'file', 'button']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'button': forms.Textarea(attrs={'rows': 2}),
        }

class MarketplaceItemForm(forms.ModelForm):
    class Meta:
        model = MarketplaceItem
        fields = ["name", "description", "price"]


class MarketplaceItemImageForm(forms.ModelForm):
    class Meta:
        model = MarketplaceItemImage
        fields = ["image"]


class MarketplaceForm(forms.ModelForm):
    class Meta:
        model = MarketplaceEntry
        fields = [
            "occupation",
            "sell_or_service",
            "product_or_service",
            "office_address",
            "years_experience",
            "specialty",
            "certification",
            "phone_number1",
            "phone_number2",
            "portfolio_link",
        ]
        widgets = {
            "specialty": forms.Select(
                choices=[
                    ("beginner", "Beginner"),
                    ("amateur", "Amateur"),
                    ("professional", "Professional"),
                ]
            ),
            "certification": forms.FileInput(),
        }


class ServiceForm(forms.Form):
    service_name = forms.CharField(max_length=255)
    description = forms.CharField(widget=forms.Textarea)
    file = forms.FileField(required=False)

class FacebookAdRequirementForm(forms.ModelForm):
    class Meta:
        model = FacebookAdRequirement
        fields = '__all__'


class MaterialSearchForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['title', 'description', 'price', 'is_available']

class WebsiteRequirementForm(forms.ModelForm):
    class Meta:
        model = WebsiteRequirement
        fields = ['website_type', 'business_type', 'features', 'contact_email', 'contact_phone', 'budget_naira']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['budget_naira'].widget.attrs.update({'placeholder': 'Enter budget in Naira'})


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["name", "text"]  # Removed 'image' field

class AdspostsForm(forms.ModelForm):
    class Meta:
        model = Adsposts
        fields = '__all__'

class DigitalMarketingForm(forms.ModelForm):
    class Meta:
        model = DigitalMarketing
        fields = '__all__'

class CodingForm(forms.ModelForm):
    class Meta:
        model = Coding
        fields = '__all__'

class GraphicsForm(forms.ModelForm):
    class Meta:
        model = Graphics
        fields = '__all__'

class CyberSecurityForm(forms.ModelForm):
    class Meta:
        model = CyberSecurity
        fields = '__all__'

class DigitalMarketingBForm(forms.ModelForm):
    class Meta:
        model = Digital_marketing_b
        fields = '__all__'

class DigitalMarketingAForm(forms.ModelForm):
    class Meta:
        model = Digital_marketing_a
        fields = '__all__'

class DigitalMarketingPForm(forms.ModelForm):
    class Meta:
        model = Digital_marketing_p
        fields = '__all__'

class CodingBForm(forms.ModelForm):
    class Meta:
        model = Coding_b
        fields = '__all__'

class CodingAForm(forms.ModelForm):
    class Meta:
        model = Coding_a
        fields = '__all__'

class CodingPForm(forms.ModelForm):
    class Meta:
        model = Coding_p
        fields = '__all__'

class GraphicBForm(forms.ModelForm):
    class Meta:
        model = Graphic_b
        fields = '__all__'

class GraphicAForm(forms.ModelForm):
    class Meta:
        model = Graphic_a
        fields = '__all__'

class GraphicPForm(forms.ModelForm):
    class Meta:
        model = Graphic_p
        fields = '__all__'

class CyberSecurityBForm(forms.ModelForm):
    class Meta:
        model = CyberSecurity_b
        fields = '__all__'

class CyberSecurityAForm(forms.ModelForm):
    class Meta:
        model = CyberSecurity_a
        fields = '__all__'

class CyberSecurityPForm(forms.ModelForm):
    class Meta:
        model = CyberSecurity_p
        fields = '__all__'

class VideoeditingBForm(forms.ModelForm):
    class Meta:
        model = Videoediting_b
        fields = '__all__'

class VideoeditingAForm(forms.ModelForm):
    class Meta:
        model = Videoediting_a
        fields = '__all__'

class VideoeditingPForm(forms.ModelForm):
    class Meta:
        model = Videoediting_p
        fields = '__all__'

class BusinessRegistrationForm(forms.ModelForm):
    class Meta:
        model = BusinessRegistration
        fields = '__all__'

class WebsiteRequirementForm(forms.ModelForm):
    budget_naira = forms.DecimalField(max_digits=10, decimal_places=2, required=True, label='Budget (Naira)')
    
    class Meta:
        model = WebsiteRequirement
        fields = ['website_type', 'business_type', 'features', 'contact_email', 'contact_phone', 'budget_naira']

class DomainHostingRequirementForm(forms.ModelForm):
    websiteFiles = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}))

    class Meta:
        model = DomainHostingRequirement
        fields = ['domainName', 'domainType', 'hostingPlan', 'additionalServices', 'websiteFiles']
        widgets = {
            'domainName': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your desired domain name'}),
            'domainType': forms.Select(attrs={'class': 'form-control'}),
            'hostingPlan': forms.Select(attrs={'class': 'form-control'}),
            'additionalServices': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter additional services (optional)'}),
        }

class DataAnalysisForm(forms.ModelForm):
    class Meta:
        model = Data_analysis
        fields = '__all__'

class DataAnalysisBForm(forms.ModelForm):
    class Meta:
        model = Data_analysis_b
        fields = '__all__'

class DataAnalysisAForm(forms.ModelForm):
    class Meta:
        model = Data_analysis_a
        fields = '__all__'

class DataAnalysisPForm(forms.ModelForm):
    class Meta:
        model = Data_analysis_p
        fields = '__all__'

class AndroidAppForm(forms.ModelForm):
    class Meta:
        model = Android_app
        fields = '__all__'

class DesktopAppForm(forms.ModelForm):
    class Meta:
        model = Desktop_app
        fields = '__all__'

class UsefulResourceForm(forms.ModelForm):
    class Meta:
        model = Useful_resource
        fields = '__all__'


class BlogPostForm(forms.ModelForm):
    tags = forms.CharField(
        max_length=200,
        required=False,
        help_text="Enter tags separated by commas. e.g., subsidy, finance",
    )

    class Meta:
        model = BlogPost
        fields = ["title", "content", "image", "tags"]  # Include tags in the fields


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['post', 'content']

class DataPurchaseForm(forms.ModelForm):
    class Meta:
        model = DataPurchase
        fields = ['phone_number', 'network', 'dataPlan']

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['title', 'price', 'is_available']

class MotivationalBookForm(forms.ModelForm):
    class Meta:
        model = MotivationalBook
        fields = ['title', 'author', 'price']


class AIIntegrationRequestForm(forms.ModelForm):
    payment_option = forms.ChoiceField(
        choices=[
            ("paystack", "Paystack"),
            ("PayPal", "PayPal"),
            ("USD bank_transfer", "USD Bank Transfer"),
        ],
        required=True,
    )

    class Meta:
        model = AIIntegrationRequest
        fields = [
            "title",
            "website_or_app",
            "description",
            "media_file",
            "payment_option",
        ]
