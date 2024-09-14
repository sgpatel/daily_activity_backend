import base64
from datetime import datetime
from io import BytesIO
import logging
import os
from rest_framework import viewsets
from django.core.files.base import ContentFile

from rest_framework import status
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

from django.conf import settings

from .models import DailyActivity
from .serializers import ActivitySerializer
from .models import Profile
from .serializers import ProfileSerializer
from .utility.utils import transcribe_audio, summarize_text

class ActivityViewSet(viewsets.ModelViewSet):
    queryset = DailyActivity.objects.all()
    serializer_class = ActivitySerializer

logger = logging.getLogger('activity_logger')

@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
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