from django.contrib import admin
from .models import Topic, UserProfile, GuestProfile

admin.site.register(Topic)
admin.site.register(UserProfile)
admin.site.register(GuestProfile)
