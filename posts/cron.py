from django_cron import CronJobBase, Schedule
import requests
from .models import YouTubePost, YouTubeChannel
import logging
import threading
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.utils import timezone

# Initialize environment variables
env = environ.Env()
environ.Env.read_env()

YOUTUBE_API_KEY = env('YOUTUBE_API_KEY')

logger = logging.getLogger(__name__)

class FetchYouTubeVideosCronJob(CronJobBase):
    # Run every 24 hours (1440 minutes in a day)
    RUN_EVERY_MINS = 1440
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'posts.fetch_youtube_videos'

    def do(self):
        youtube_channels = YouTubeChannel.objects.all()
        for channel in youtube_channels:
            api_url = (
                f'https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}'
                f'&channelId={channel.channel_id}&part=snippet,id&order=date&maxResults=5'
            )
            logger.info(f"Fetching URL: {api_url}")
            response = requests.get(api_url)

            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response content: {response.content}")

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response Data: {data}")
                for item in data.get('items', []):
                    video_id = item['id'].get('videoId')
                    if video_id:
                        title = item['snippet']['title']
                        description = item['snippet']['description']
                        published_at = item['snippet']['publishedAt']
                        thumbnail_url = item['snippet']['thumbnails']['high']['url']

                        # Check if the video is already in the database
                        if not YouTubePost.objects.filter(video_id=video_id).exists():
                            # Create the YouTube post
                            new_post = YouTubePost.objects.create(
                                title=title,
                                description=description,
                                video_id=video_id,
                                published_at=published_at,
                                thumbnail_url=thumbnail_url
                            )

                            # Fetch users who liked related posts
                            users_who_liked = User.objects.filter(
                                youtube_likes__in=YouTubePost.objects.filter(video_id=video_id)
                            ).distinct()

                            # Collect emails of users who have liked posts
                            recipient_list = [user.email for user in users_who_liked if user.email]

                            # Function to send the email asynchronously using base_email.html
                            def send_email_async(subject, email_content, from_email, recipient_list):
                                try:
                                    # Render the email using base_email.html
                                    email_body = render_to_string('base_email.html', {
                                        'email_subject': subject,
                                        'email_content': email_content,
                                        'current_year': timezone.now().year,
                                    })

                                    # Send email
                                    send_mail(
                                        subject=subject,
                                        message="",  # Empty text message
                                        from_email=from_email,
                                        recipient_list=recipient_list,
                                        html_message=email_body,  # HTML email content
                                    )
                                except Exception as e:
                                    logger.error(f"Failed to send YouTube post email: {e}")

                            # Construct the full URL manually (since request is not available)
                            current_site = Site.objects.all()
                            domain = current_site.domain
                            shared_link = f"http://{domain}{reverse('youtube_post_detail', args=[video_id])}"

                            subject = f"New Current Happening Video: {title}"
                            email_content = f"""
                            Hello,

                            A new video titled '{title}' has been posted on OWD.

                            {description}

                            Watch it here: <a href="{shared_link}">{shared_link}</a>

                            Thank you!
                            """

                            # Send the email in a separate thread to avoid blocking the main process
                            threading.Thread(
                                target=send_email_async,
                                args=(subject, email_content, settings.DEFAULT_FROM_EMAIL, recipient_list)
                            ).start()

            else:
                logger.error(f"Failed to fetch videos for channel {channel.channel_id}: {response.status_code}")
                logger.error(f"Response content: {response.content}")
