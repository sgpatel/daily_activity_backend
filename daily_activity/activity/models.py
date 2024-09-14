from django.db import models
from django.contrib.auth.models import User

class Activity(models.Model):
    date = models.DateField()
    audio_path = models.CharField(max_length=255, blank=True)
    transcript = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    reminders = models.TextField(blank=True)
    spending = models.FloatField(default=0)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_photo = models.ImageField(upload_to='profile_pics/', blank=True)

    def __str__(self):
        return self.user.username