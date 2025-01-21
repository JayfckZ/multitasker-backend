from django.urls import path
from .views import ConvertImageView, DownloadVideoView

urlpatterns = [
    path('convert-image/', ConvertImageView.as_view(), name='convert-image'),
    path('download-video/', DownloadVideoView.as_view(), name='download-video'),
]
