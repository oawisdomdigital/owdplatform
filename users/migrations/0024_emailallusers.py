# Generated by Django 4.2.13 on 2024-11-04 12:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0023_rename_device_token_profile_fcm_token'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailAllUsers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
