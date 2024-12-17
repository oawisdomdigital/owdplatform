# create_profile.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import Profile

class Command(BaseCommand):
    help = 'Create profiles for users without one'

    def handle(self, *args, **kwargs):
        users_without_profiles = User.objects.filter(user_profile__isnull=True)
        for user in users_without_profiles:
            Profile.objects.create(user=user)
            self.stdout.write(self.style.SUCCESS(f'Created profile for user {user.username}'))
        self.stdout.write(self.style.SUCCESS('Profiles created for all users without one'))
