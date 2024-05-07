"""
URL configuration for echotune project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from echoapp.views import register_user, save_preferences, learning_goal, login_user, fetch_news, generate_summary, generate_audio, serve_audio, get_user_hashtags, get_user_topics, get_topics_for_hashtag, getHashtag


urlpatterns = [
    path('admin/', admin.site.urls),
    # path('login/', auth_views.LoginView.as_view(), name='login'),
    # path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('api/register/', register_user, name='register'),
    path('api/save_preferences/', save_preferences, name='save_preferences'),
    path('api/learning-goal/', learning_goal, name='api_learning_goal'),
    path('api/login/', login_user, name='api_login'),
    path('api/fetch_news/', fetch_news, name='fetch_news'),
    path('api/generate_audio/', generate_audio, name='generate_audio'),
    path('api/generate_summary/', generate_summary, name='generate_summary'),
    path('audio/<str:filename>/', serve_audio, name='serve_audio'),
    path('api/get_user_topics/', get_user_topics, name='get_user_topics'),
    path('api/get_user_hashtags/', get_user_hashtags, name='get_user_hashtags'),
    path('api/get_topics_for_hashtag/<str:hashtag_name>/', get_topics_for_hashtag, name='get_topics_for_hashtag'),
    path('api/getHashtag/', getHashtag, name='getHashtag'),
]

