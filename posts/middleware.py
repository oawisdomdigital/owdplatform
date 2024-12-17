# myapp/middleware.py

from django.contrib.sites.models import Site
from django.utils.deprecation import MiddlewareMixin

class DynamicSiteIDMiddleware(MiddlewareMixin):
    def process_request(self, request):
        try:
            site = Site.objects.get(domain=request.get_host())
            request.site = site  # Attach the Site object to the request
            request.session['SITE_ID'] = site.id  # Optional: Store SITE_ID in session
        except Site.DoesNotExist:
            request.site = None
            request.session['SITE_ID'] = None  # Handle as needed
