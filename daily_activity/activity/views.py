import base64
from datetime import datetime
from io import BytesIO
import logging
import os
from rest_framework import viewsets
import json

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, parser_classes
from pydub import AudioSegment
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from django.conf import settings

from .models import DailyActivity
from .serializers import ActivitySerializer
from .models import Profile
from .serializers import ProfileSerializer
from .utility.utils import transcribe_audio, summarize_text

class ActivityViewSet(viewsets.ModelViewSet):
    queryset = DailyActivity.objects.all()
    serializer_class = ActivitySerializer

class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]  # Restrict access to authenticated users only

    def get(self, request):
        return Response({"message": "This is a protected view only for authenticated users."})

logger = logging.getLogger('activity_logger')

@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@login_required
def record_activity_api(request):
    if request.method == 'POST':
        # Log the start of the request
        logger.info("Started processing record_activity request with streaming")

        # Handle streaming uploads with TemporaryFileUploadHandler
        request.upload_handlers.insert(0, TemporaryFileUploadHandler())

        # Get the selected date from the request
        selected_date = request.POST.get('date')
        if not selected_date:
            logger.error("No date provided by the user")
            return JsonResponse({'error': 'No date provided'}, status=400)

        logger.info(f"User selected date: {selected_date}")

        # Format the selected date
        formatted_date = datetime.strptime(selected_date, '%Y-%m-%d').strftime('%Y-%m-%d')

        # Create a directory based on the selected date
        date_folder_path = os.path.join(settings.MEDIA_ROOT, 'audio', formatted_date)
        if not os.path.exists(date_folder_path):
            os.makedirs(date_folder_path)  # Create the folder if it doesn't exist
            logger.info(f"Created directory for date: {formatted_date} at {date_folder_path}")
        else:
            logger.info(f"Directory for date: {formatted_date} already exists")

        # Handle file upload from React (streaming mode)
        if 'audio_file' in request.FILES:
            uploaded_audio = request.FILES['audio_file']

            try:
                # Convert uploaded file to WAV format
                logger.info("Processing uploaded audio file in streaming mode")

                # If the uploaded file is already in WAV, this will handle it correctly; otherwise, convert to WAV
                audio_segment = AudioSegment.from_file(uploaded_audio)
                audio_temp = BytesIO()
                audio_segment.export(audio_temp, format="wav")  # Convert to WAV

                # Create a unique file name using the current time to avoid file name collisions
                audio_file_name = f'audio_{formatted_date}_{datetime.now().strftime("%H-%M-%S")}.wav'

                # Save the uploaded file in the date-based folder in .wav format
                file_path = os.path.join(date_folder_path, audio_file_name)
                with open(file_path, 'wb') as f:
                    f.write(audio_temp.getvalue())  # Save the converted audio file as a .wav file

                logger.info(f"Uploaded and converted audio file successfully saved at {file_path}")

            except Exception as e:
                # Log error and return JSON response
                logger.error(f"Error processing uploaded audio file: {str(e)}", exc_info=True)
                return JsonResponse({'error': f"Error converting audio: {str(e)}"}, status=400)

        logger.info("Successfully processed record_activity request")
        return JsonResponse({'message': 'Activity saved and converted to .wav successfully'})

    # If GET method is used, return a simple response (adjust as per your requirement)
    return JsonResponse({'message': 'GET method not supported for this endpoint'}, status=405)


@api_view(['POST'])
def signup(request):
    try:
        data = request.data
        user = User.objects.create(
            username=data['username'],
            password=make_password(data['password']),
            email=data['email']
        )
        return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    
@api_view(['GET', 'POST'])
def user_profile(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'User not authenticated'}, status=401)
    
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        profile = Profile.objects.get(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        profile = Profile.objects.get(user=request.user)
        profile.profile_photo = request.FILES.get('profile_photo')
        profile.save()
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
    

#@login_required
@permission_classes([IsAuthenticated])
@csrf_exempt
@api_view(['POST'])
def get_audio_files_for_date(request, date):
    """
    Fetch the list of audio files for the given date.
    """
    # if not request.user.is_authenticated:
    #     return JsonResponse({'error': 'User not authenticated'}, status=401)
    # Format the date and construct the folder path
    logger.info(f"Received request for audio files for date: {date}")
    formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
    date_folder_path = os.path.join(settings.MEDIA_ROOT, 'audio', formatted_date)

    if not os.path.exists(date_folder_path):
        return JsonResponse({'files': [], 'message': 'No files found for the selected date.'})

    # List all .wav files in the folder
    files = [f for f in os.listdir(date_folder_path) if f.endswith('.wav')]
    return JsonResponse({'files': files, 'count': len(files)})

#@login_required
@permission_classes([IsAuthenticated])
@require_POST
@csrf_exempt
@api_view(['POST'])
def delete_audio_file(request):
    """
    Delete a specific audio file.
    """
    # if not request.user.is_authenticated:
    #     return JsonResponse({'error': 'User not authenticated'}, status=401)
    
    logger.info("Received request to delete audio file")
    try:
        data = json.loads(request.body)  # Parse the JSON request body
        file_name = data.get('file_name')
        date = data.get('date')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    logger.info(f"Received request to delete file: {file_name} for date: {date}")
    
    if not file_name or not date:
        return JsonResponse({'error': 'File name or date not provided'}, status=400)

    # Format the date and construct the file path
    formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
    file_path = os.path.join(settings.MEDIA_ROOT, 'audio', formatted_date, file_name)

    logger.info(f"Attempting to delete file: {file_path}")
    
    if os.path.exists(file_path):
        os.remove(file_path)
        return JsonResponse({'message': f'{file_name} deleted successfully'})
    else:
        return JsonResponse({'error': 'File not found'}, status=404)