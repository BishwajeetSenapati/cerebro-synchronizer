import os
import uuid
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import cloudinary
import cloudinary.uploader


def index(request):
    return render(request, 'index.html')


@csrf_exempt
def upload_video(request):
    if request.method == 'POST':
        video_file = request.FILES.get('video')
        if not video_file:
            return JsonResponse({'error': 'No file provided'}, status=400)

        # Validate file type
        allowed_types = [
            'video/mp4', 'video/webm', 'video/ogg',
            'video/avi', 'video/mov', 'video/quicktime',
            'video/x-msvideo', 'video/x-matroska',
        ]
        if video_file.content_type not in allowed_types:
            return JsonResponse(
                {'error': f'Invalid file type: {video_file.content_type}'},
                status=400
            )

        try:
            # Upload directly to Cloudinary
            upload_result = cloudinary.uploader.upload(
                video_file,
                resource_type = 'video',
                folder        = 'cerebro_videos',
                public_id     = f"video_{uuid.uuid4().hex}",
            )

            # Get the secure URL from Cloudinary
            video_url = upload_result.get('secure_url')

            return JsonResponse({'url': video_url})

        except Exception as e:
            return JsonResponse(
                {'error': f'Upload failed: {str(e)}'},
                status=500
            )

    return JsonResponse({'error': 'Method not allowed'}, status=405)


def serve_video(request, filename):
    """Serve video with HTTP Range support for seeking."""
    filepath = os.path.join(settings.MEDIA_ROOT, filename)
    if not os.path.exists(filepath):
        return HttpResponse(status=404)

    file_size = os.path.getsize(filepath)
    range_header = request.META.get('HTTP_RANGE', '').strip()

    if range_header:
        range_match = range_header.replace('bytes=', '').split('-')
        first_byte = int(range_match[0])
        last_byte = int(range_match[1]) if range_match[1] else file_size - 1
        last_byte = min(last_byte, file_size - 1)
        length = last_byte - first_byte + 1

        def file_iterator(path, offset, length, chunk_size=8192):
            with open(path, 'rb') as f:
                f.seek(offset)
                remaining = length
                while remaining > 0:
                    chunk = f.read(min(chunk_size, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        response = StreamingHttpResponse(
            file_iterator(filepath, first_byte, length),
            status=206,
            content_type='video/mp4',
        )
        response['Content-Range']  = f'bytes {first_byte}-{last_byte}/{file_size}'
        response['Accept-Ranges']  = 'bytes'
        response['Content-Length'] = str(length)
        return response

    else:
        def full_file_iterator(path, chunk_size=8192):
            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

        response = StreamingHttpResponse(
            full_file_iterator(filepath),
            status=200,
            content_type='video/mp4',
        )
        response['Accept-Ranges']  = 'bytes'
        response['Content-Length'] = str(file_size)
        return response