from django.db import models
from django.conf import settings

class File(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=1024)
    size = models.BigIntegerField()
    content_type = models.CharField(max_length=100)
    is_encrypted = models.BooleanField(default=False)
    encryption_key = models.CharField(max_length=255, null=True, blank=True)
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['owner', 'path']

class FileVersion(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    size = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)