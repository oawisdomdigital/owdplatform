# Generated by Django 4.2.13 on 2024-10-31 15:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_motivationalbook_image_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='motivationalbook',
            name='image_url',
            field=models.URLField(blank=True, max_length=3000),
        ),
    ]
