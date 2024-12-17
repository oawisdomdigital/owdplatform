from django.apps import AppConfig


class ChatConfig(AppConfig):
    name = "chat"

    def ready(self):
        import chat.signals  # Import the signals to ensure they are registered
