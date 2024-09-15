from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ActivityViewSet, record_activity_api,get_audio_files_for_date,delete_audio_file,signup, user_profile
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView,TokenVerifyView 
from django.contrib.auth.views import LoginView
from .views import ProtectedView

router = DefaultRouter()
router.register(r'activities', ActivityViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),  # Add this for token verification
    path('api/signup/', signup, name='signup'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/profile/', user_profile, name='user_profile'),
    path('api/record/',record_activity_api, name='record_activity_api'),
    path('api/audio/date/<str:date>/',get_audio_files_for_date, name='get_audio_files_for_date'),
    path('api/audio/delete/',delete_audio_file, name='delete_audio_file'),
    path('api/protected/', ProtectedView.as_view(), name='protected'),
]
