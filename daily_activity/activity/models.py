from django.db import models
from django.contrib.auth.models import User

# Function to store audio files in a directory based on the date
def audio_directory_path(instance, filename):
    # Generates a path like: 'audios/YYYY-MM-DD/audio_HH-MM-SS.wav'
    return f'audios/{instance.date}/{filename}'


# Model to store daily activities
class DailyActivity(models.Model):
    date = models.DateField()
    audio_file = models.FileField(upload_to=audio_directory_path, null=True, blank=True) 
    transcript = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    reminders = models.TextField(blank=True)
    spending = models.FloatField(default=0)

    def __str__(self):
        return f"Activity on {self.date}"  # String representation for easy identification in admin

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_photo = models.ImageField(upload_to='profile_pics/', blank=True)

    def __str__(self):
        return self.user.username