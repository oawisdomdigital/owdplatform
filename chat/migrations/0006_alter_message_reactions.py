# Generated by Django 4.2.13 on 2024-10-27 16:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_message_reactions_delete_reaction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='reactions',
            field=models.CharField(blank=True, default='{}', max_length=1024),
        ),
    ]