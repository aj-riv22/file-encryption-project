import os
from django.conf import settings
from ..models import File, FileVersion
from .encryption import EncryptionService

class FileHandler:
    def __init__(self, user):
        self.user = user
        self.encryption_service = EncryptionService()

    def save_file(self, file_obj, path: str, encrypt: bool = False):
        # Read file content
        file_content = file_obj.read()
        
        # Encrypt if requested
        if encrypt:
            key = self.encryption_service.generate_key()
            file_content = self.encryption_service.encrypt_file(file_content, key)
            encryption_key = key.decode()
        else:
            encryption_key = None

        # Create or update file record
        file_record, created = File.objects.get_or_create(
            owner=self.user,
            path=path,
            defaults={
                'name': os.path.basename(path),
                'size': len(file_content),
                'content_type': file_obj.content_type,
                'is_encrypted': encrypt,
                'encryption_key': encryption_key
            }
        )

        if not created:
            # Create new version
            FileVersion.objects.create(
                file=file_record,
                version_number=file_record.version,
                size=file_record.size
            )
            # Update file record
            file_record.version += 1
            file_record.size = len(file_content)
            file_record.save()

        # Save file content
        file_path = os.path.join(settings.MEDIA_ROOT, str(file_record.id))
        with open(file_path, 'wb') as f:
            f.write(file_content)

        return file_record