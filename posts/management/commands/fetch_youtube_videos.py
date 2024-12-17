from django.core.management.base import BaseCommand
from posts.cron import FetchYouTubeVideosCronJob

class Command(BaseCommand):
    help = 'Fetch YouTube videos from all channels'

    def handle(self, *args, **kwargs):
        job = FetchYouTubeVideosCronJob()
        job.do()
        self.stdout.write(self.style.SUCCESS('Successfully fetched YouTube videos'))