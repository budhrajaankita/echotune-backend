from django.contrib import admin
from .models import Topic, Source, Hashtag, UserProfile, GuestProfile

admin.site.register(Topic)
admin.site.register(Source)
admin.site.register(Hashtag)
admin.site.register(UserProfile)
admin.site.register(GuestProfile)
