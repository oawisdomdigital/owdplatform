from django.apps import AppConfig

class PostsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'posts'

    def ready(self):
        # Import the signal handlers
        from . import signals
        
        # Import and start the scheduler
        from .scheduler import start_scheduler
        start_scheduler()
