
import os
import uuid
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


def index(request):
    return render(request, 'index.html')


def serve_video(request, filename):
    """Serve video with HTTP Range support for seeking."""
    filepath = os.path.join(settings.MEDIA_ROOT, filename)
    if not os.path.exists(filepath):
        return HttpResponse(status=404)

    file_size = os.path.getsize(filepath)
    range_header = request.META.get('HTTP_RANGE', '').strip()

    if range_header:
        # Parse range header e.g. bytes=0-1023
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
        response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{file_size}'
        response['Accept-Ranges'] = 'bytes'
        response['Content-Length'] = str(length)
        return response
    else:
        # Full file response
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
        response['Accept-Ranges'] = 'bytes'
        response['Content-Length'] = str(file_size)
        return response


@csrf_exempt
def upload_video(request):
    if request.method == 'POST':
        video_file = request.FILES.get('video')
        if not video_file:
            return JsonResponse({'error': 'No file provided'}, status=400)
        allowed_types = [
            'video/mp4', 'video/webm', 'video/ogg',
            'video/avi', 'video/mov', 'video/quicktime',
            'video/x-msvideo', 'video/x-matroska',
        ]
        if video_file.content_type not in allowed_types:
            return JsonResponse({'error': f'Invalid file type: {video_file.content_type}'}, status=400)
        ext = os.path.splitext(video_file.name)[1]
        unique_name = f"{uuid.uuid4().hex}{ext}"
        save_path = os.path.join(settings.MEDIA_ROOT, unique_name)
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        with open(save_path, 'wb+') as f:
            for chunk in video_file.chunks():
                f.write(chunk)
        # Return the custom serve URL instead of direct media URL
        video_url = request.build_absolute_uri(f'/video/{unique_name}/')
        return JsonResponse({'url': video_url})
    return JsonResponse({'error': 'Method not allowed'}, status=405)