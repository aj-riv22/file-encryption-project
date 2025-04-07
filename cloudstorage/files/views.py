from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse
from .models import File
from .serializers import FileSerializer
from .services.file_handler import FileHandler

class FileViewSet(viewsets.ModelViewSet):
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return File.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        file_obj = self.request.FILES.get('file')
        path = self.request.data.get('path')
        encrypt = self.request.data.get('encrypt', False)

        if not file_obj or not path:
            raise serializers.ValidationError(
                "Both 'file' and 'path' are required"
            )

        handler = FileHandler(self.request.user)
        file_record = handler.save_file(file_obj, path, encrypt)
        serializer.instance = file_record

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        file_obj = self.get_object()
        handler = FileHandler(request.user)
        file_content = handler.get_file_content(file_obj)
        
        response = FileResponse(file_content)
        response['Content-Disposition'] = f'attachment; filename="{file_obj.name}"'
        response['Content-Type'] = file_obj.content_type
        return response
