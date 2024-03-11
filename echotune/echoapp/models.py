from django.db import models
from django.contrib.auth.models import User
import uuid

class Topic(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    topics = models.ManyToManyField(Topic)

    def __str__(self):
        return self.user.username

class GuestProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topics = models.ManyToManyField(Topic)
    created = models.DateTimeField(auto_now_add=True)

