# Generated by Django 5.0.7 on 2024-08-25 16:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_alter_profile_whatsapp_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='whatsapp_number',
            field=models.CharField(default=1, max_length=15),
            preserve_default=False,
        ),
    ]