# utils/signals.py

from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage
from .file_utils import delete_file_from_storage

@receiver(post_delete)
def delete_files(sender, instance, **kwargs):
    """Deletes files from storage when a model instance is deleted."""
    # Iterate through all fields in the model
    for field in instance._meta.fields:
        # Check if the field is a FileField or ImageField
        if hasattr(field, 'upload_to'):
            file_field = getattr(instance, field.name)
            if file_field and file_field.name:
                delete_file_from_storage(file_field.name)
