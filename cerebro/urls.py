from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from sync.views import index, upload_video, serve_video

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('upload/', upload_video, name='upload_video'),
    path('video/<str:filename>/', serve_video, name='serve_video'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)