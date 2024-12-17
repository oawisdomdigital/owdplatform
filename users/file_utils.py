# utils/file_utils.py

import os
from django.conf import settings

def delete_file_from_storage(file_path):
    """Deletes a file from the filesystem."""
    if file_path and os.path.isfile(os.path.join(settings.MEDIA_ROOT, file_path)):
        os.remove(os.path.join(settings.MEDIA_ROOT, file_path))
