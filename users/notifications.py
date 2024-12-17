from pyfcm import FCMNotification
from django.conf import settings

def send_push_notification(registration_ids, message_title, message_body):
    push_service = FCMNotification(api_key=settings.FIREBASE_SERVER_KEY)
    result = push_service.notify_multiple_devices(
        registration_ids=registration_ids,
        message_title=message_title,
        message_body=message_body
    )
    return result
