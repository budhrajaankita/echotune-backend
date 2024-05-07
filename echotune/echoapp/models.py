from django.db import models
from django.contrib.auth.models import User
import uuid

class Topic(models.Model):
    name = models.CharField(max_length=100)

class Source(models.Model):
    name = models.CharField(max_length=100)

class Hashtag(models.Model):
    name = models.CharField(max_length=100)
    topics = models.ManyToManyField(Topic, related_name='hashtags')
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    topics = models.ManyToManyField(Topic, related_name='user_profiles')
    sources = models.ManyToManyField(Source, related_name='user_profiles')
    hashtags = models.ManyToManyField(Hashtag, related_name='user_profiles')

class GuestProfile(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topics = models.ManyToManyField(Topic, related_name='guest_profiles')
    sources = models.ManyToManyField(Source, related_name='guest_profiles')
    hashtags = models.ManyToManyField(Hashtag, related_name='guest_profiles')

