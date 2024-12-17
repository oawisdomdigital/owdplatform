import requests
from django.conf import settings

def send_push_notification(token, message_body):
    api_url = "https://fcm.googleapis.com/fcm/send"
    headers = {
        "Authorization": f"key={settings.FCM_SERVER_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": token,
        "notification": {
            "title": "OTP Notification",
            "body": message_body
        }
    }
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code != 200:
        print(f"Failed to send push notification: {response.content}")
