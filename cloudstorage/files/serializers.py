from rest_framework import serializers
from .models import File, FileVersion

class FileVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileVersion
        fields = ['version_number', 'size', 'created_at']

class FileSerializer(serializers.ModelSerializer):
    versions = FileVersionSerializer(many=True, read_only=True)

    class Meta:
        model = File
        fields = ['id', 'name', 'path', 'size', 'content_type', 
                 'is_encrypted', 'version', 'created_at', 
                 'updated_at', 'versions']
        read_only_fields = ['id', 'created_at', 'updated_at']
