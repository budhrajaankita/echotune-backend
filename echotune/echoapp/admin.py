from django.contrib import admin
from .models import Topic, Source, UserProfile, GuestProfile

admin.site.register(Topic)
admin.site.register(Source)
admin.site.register(UserProfile)
admin.site.register(GuestProfile)
