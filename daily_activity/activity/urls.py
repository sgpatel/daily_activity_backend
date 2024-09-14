from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ActivityViewSet, record_activity_api,get_audio_files_for_date,delete_audio_file,signup, user_profile
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'activities', ActivityViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/signup/', signup, name='signup'),
    path('api/profile/', user_profile, name='user_profile'),
    path('api/record/',record_activity_api, name='record_activity_api'),
    path('api/audio/date/<str:date>/',get_audio_files_for_date, name='get_audio_files_for_date'),
    path('api/audio/delete/',delete_audio_file, name='delete_audio_file'),

]
