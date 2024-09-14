from rest_framework import viewsets

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from .models import Activity
from .serializers import ActivitySerializer
from .models import Profile
from .serializers import ProfileSerializer

class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer


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