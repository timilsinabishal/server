from rest_framework import serializers
from rest_framework.exceptions import APIException

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

from user_resource.serializers import UserResourceSerializer
from utils.external_storages.google_drive import download as g_download
from utils.external_storages.dropbox import download as d_download
from .models import File


class FileSerializer(UserResourceSerializer):
    class Meta:
        model = File
        fields = ('__all__')

    def create(self, validated_data):
        file = super(FileSerializer, self).create(validated_data)
        file.permitted_users.add(self.context['request'].user)
        return file


class GoogleDriveFileSerializer(UserResourceSerializer):
    access_token = serializers.CharField(write_only=True)
    file_id = serializers.CharField(write_only=True)
    mime_type = serializers.CharField(write_only=True)

    class Meta:
        model = File
        fields = ('__all__')

    def create(self, validated_data):
        title = validated_data.get('title')
        access_token = validated_data.pop('access_token')
        file_id = validated_data.pop('file_id')
        mime_type = validated_data.pop('mime_type', '')

        file = g_download(
            file_id,
            mime_type,
            access_token,
            settings.DEEP_SUPPORTED_MIME_TYPES,
            APIException,
        )

        # TODO: is this good?
        validated_data['file'] = InMemoryUploadedFile(
            file, None, title, mime_type, None, None
        )

        file = super(GoogleDriveFileSerializer, self).create(validated_data)
        file.permitted_users.add(self.context['request'].user)
        return file


class DropboxFileSerializer(UserResourceSerializer):
    file_url = serializers.CharField(write_only=True)

    class Meta:
        model = File
        fields = ('__all__')

    def create(self, validated_data):
        title = validated_data.get('title')
        file_url = validated_data.pop('file_url')

        file, mime_type = d_download(
            file_url,
            settings.DEEP_SUPPORTED_MIME_TYPES,
            APIException,
        )

        # TODO: is this good?
        validated_data['file'] = InMemoryUploadedFile(
            file, None, title, mime_type, None, None
        )

        file = super(DropboxFileSerializer, self).create(validated_data)
        file.permitted_users.add(self.context['request'].user)
        return file
