# Generated by Django 4.2.13 on 2024-11-04 12:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0024_emailallusers'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailallusers',
            name='broadcast',
            field=models.BooleanField(default=False),
        ),
    ]
