# Generated by Django 5.0.7 on 2024-08-25 16:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_remove_profile_fcm_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='whatsapp_number',
            field=models.CharField(blank=True, max_length=15),
        ),
    ]
