from uuid import uuid4

import requests
from django.core.files.base import ContentFile
from django.http import HttpResponseServerError
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from datetime import datetime
import os


class FileUploadSerializer(serializers.Serializer):
    files = serializers.ListField(child=serializers.FileField(max_length=100000, allow_empty_file=False, use_url=False))


def save_uploaded_files(uploaded_files, path='uploads/'):
    result_data = []

    for uploaded_file in uploaded_files:
        original_name = None
        extension = None
        url = None

        if isinstance(uploaded_file, str):
            response = requests.get(uploaded_file)
            if response.status_code == 200:
                content_type = response.headers.get('content-type')
                extension = content_type.split('/')[-1] if content_type else ''
                new_name = f"{uuid4().hex}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{extension}"

                try:
                    path = default_storage.save(os.path.join(path, new_name), ContentFile(response.content))
                    url = default_storage.url(path)
                except Exception as e:
                    return HttpResponseServerError("Внутренняя ошибка сервера")
        else:
            original_name = uploaded_file.name
            extension = os.path.splitext(original_name)[-1].lower()
            new_name = f"{uuid4().hex}_{datetime.now().strftime('%Y%m%d%H%M%S')}{extension}"

            try:
                path = default_storage.save(os.path.join(path, new_name), uploaded_file)
                url = default_storage.url(path)
            except Exception as e:
                return HttpResponseServerError("Внутренняя ошибка сервера")

        url = url.replace("media/", "")
        file_data = {
            'file': url,
            'original_name': original_name,
            'extension': extension,
        }

        result_data.append(file_data)

    return result_data


class FileUploadView(APIView):
    serializer_class = FileUploadSerializer

    def post(self, request, *args, **kwargs):
        uploaded_files = request.FILES.getlist('files')
        path = request.GET.get('path', 'uploads/')

        result_data = save_uploaded_files(uploaded_files, path)

        return Response(result_data, status=status.HTTP_201_CREATED)