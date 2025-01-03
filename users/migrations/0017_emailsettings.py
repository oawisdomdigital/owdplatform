# Generated by Django 5.0.7 on 2024-08-25 18:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_alter_profile_whatsapp_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_host', models.CharField(default='smtp.gmail.com', max_length=255)),
                ('email_port', models.IntegerField(default=587)),
                ('email_use_tls', models.BooleanField(default=True)),
                ('email_host_user', models.EmailField(max_length=254)),
                ('email_host_password', models.CharField(max_length=255)),
                ('default_from_email', models.EmailField(max_length=254)),
            ],
        ),
    ]
