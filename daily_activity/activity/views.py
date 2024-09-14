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
        logger.info("Started processing record_activity request")

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

        # Handle base64 encoded audio data from React
        audio_data = request.POST.get('audio_data')
        if audio_data:
            logger.info("Processing base64 encoded audio data")
            try:
                format, audio_str = audio_data.split(';base64,')  # Split the base64 string
                audio_decoded = base64.b64decode(audio_str)  # Decode the base64 string
                audio_segment = AudioSegment.from_file(BytesIO(audio_decoded))
                audio_temp = BytesIO()
                audio_segment.export(audio_temp, format="wav")  # Export to WAV

                audio_file_name = f'audio_{formatted_date}_{datetime.now().strftime("%H-%M-%S")}.wav'
                audio_content = ContentFile(audio_temp.getvalue())

                # Create file path inside the date-based folder
                file_path = os.path.join(date_folder_path, audio_file_name)
                with open(file_path, 'wb') as f:
                    f.write(audio_content.read())

                logger.info(f"Audio file saved successfully at {file_path}")

            except Exception as e:
                logger.error(f"Error processing audio data: {str(e)}", exc_info=True)
                return JsonResponse({'error': f"Error processing audio data: {str(e)}"}, status=400)

        # Handle file upload from React and convert to .wav
        if 'audio_file' in request.FILES:
            uploaded_audio = request.FILES['audio_file']
            logger.info("Processing uploaded audio file")
            
            try:
                # Convert uploaded file to WAV format
                audio_segment = AudioSegment.from_file(uploaded_audio)
                audio_temp = BytesIO()
                audio_segment.export(audio_temp, format="wav")  # Convert to WAV

                audio_file_name = f'audio_{formatted_date}_{datetime.now().strftime("%H-%M-%S")}.wav'
                audio_content = ContentFile(audio_temp.getvalue())

                # Save the uploaded file in the date-based folder in .wav format
                file_path = os.path.join(date_folder_path, audio_file_name)
                with open(file_path, 'wb') as f:
                    f.write(audio_content.read())

                logger.info(f"Uploaded audio file successfully converted and saved at {file_path}")

            except Exception as e:
                logger.error(f"Error processing uploaded audio file: {str(e)}", exc_info=True)
                return JsonResponse({'error': f"Error converting audio: {str(e)}"}, status=400)

        logger.info("Successfully processed record_activity request")
        return JsonResponse({'message': 'Activity saved and converted to .wav successfully'})

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