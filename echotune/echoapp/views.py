from http.client import HTTPResponse
from io import BytesIO
from echotune.settings import BASE_DIR
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework import status
from .models import UserProfile, GuestProfile, Topic, Source
from .serializers import UserSerializer
import requests
import uuid
from openai import OpenAI
from decouple import config
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.http import HttpResponseNotFound, FileResponse  
import os
from hashlib import md5
import logging


@api_view(['POST'])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "user": UserSerializer(user).data,
                "token": token.key,
                "message": "🧏🏻‍♀️ User Created Successfully."
            }, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['POST'])
# def login_user(request):
#     serializer = AuthTokenSerializer(data=request.data)
#     if serializer.is_valid():
#         user = serializer.validated_data['user']
#         token, created = Token.objects.get_or_create(user=user)
#         return Response({
#             'user_id': user.pk,
#             'username': user.username,
#             'email': user.email,
#             'token': token.key,
#             'message': "Welcome back, {user.username}!"
#         })
#     else:
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


      
@api_view(['POST'])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            "message": "Login Successful."
        }, status=status.HTTP_200_OK)
    else:
        # Authentication failed
        return Response({"error": "Invalid username or password"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_preferences(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    print(f"Received auth header: {auth_header}")

    is_guest = request.data.get('is_guest')
    session_id_str = request.data.get('session_id', None)

    try:
        session_id = uuid.UUID(session_id_str) if session_id_str else None
    except ValueError:
        return Response({"error": "Invalid session_id provided"}, status=status.HTTP_400_BAD_REQUEST)

    topics_names = request.data.get('topics', [])
    sources_names = request.data.get('sources', [])
    print(topics_names)
    print(sources_names)

    if is_guest and session_id:
        profile, _ = GuestProfile.objects.get_or_create(session_id=session_id)
    else:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

    # Save topics and sources for either profile
    profile.topics.clear()
    for name in topics_names:
        topic, _ = Topic.objects.get_or_create(name=name)
        profile.topics.add(topic)

    profile.sources.clear()
    for name in sources_names:
        source, _ = Source.objects.get_or_create(name=name)
        profile.sources.add(source)

    return Response({"message": "Preferences saved successfully"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_topics(request):
    if request.user.is_authenticated:
        user_profile = request.user.userprofile
        topics = user_profile.topics.all()
        topics_data = [{'id': topic.id, 'name': topic.name} for topic in topics]
        return Response(topics_data)
    else:
        return Response({"error": "User is not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_news(request):
    is_guest = request.query_params.get('is_guest')
    session_id = request.query_params.get('session_id', None)

    if is_guest and session_id:
        profile = GuestProfile.objects.filter(session_id=session_id).first()
    else:
        profile = UserProfile.objects.filter(user=request.user).first()

    if not profile:
        return Response({"error": "Profile not found"}, status=404)
    
    print(profile)

    topics = profile.topics.all()
    sources = profile.sources.all()

    # Constructing the query
    topics = [topic.name for topic in profile.topics.all()]
    # TODO: first try ADD, and then append OR to the results
    topics_query = ' OR '.join(topics)
    query_params = {
        'q': topics_query,
        'lang': 'en', 
        'sortBy': 'publishedAt',  # Sort by publication date
        'apikey': settings.GNEWS_API_KEY,
        'expand' : 'content'
    }

    # Making the request to GNews API
    api_url = 'https://gnews.io/api/v4/search'
    response = requests.get(api_url, params=query_params)
    
    if response.status_code != 200:
        # Handling possible errors from the API request
        return Response({"error": "Failed to fetch news from GNews"}, status=response.status_code)

    news_data = response.json()

    # Formatting the response
    formatted_news = [{
        "id": idx,
        "title": article["title"],
        "description": article["description"],
        "content": article["content"],
        "url": article["url"],
        "image": article["image"],
        "publishedAt": article["publishedAt"],
        "source_name": article["source"]["name"],
        "source_url": article["source"]["url"]
    } for idx, article in enumerate(news_data.get('articles', []))]

    return Response(formatted_news)

@api_view(['POST'])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "user_id": user.pk,
                "username": user.username,
                "email": user.email,
                "token": token.key,
                # "message": "User Created Successfully."
                # "user": UserSerializer(user).data,
                # "token": token.key,
                "message": "🧏🏻‍♀️ User Created Successfully."
            }, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

     

@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def learning_goal(request):
    learning_goal = request.data.get('learningGoal')
    
    if not learning_goal:
        return Response({'error': 'No text provided!'}, status=400)
    
    client = OpenAI(api_key=config('OPENAI_API_KEY'))

    if not client:
        raise ValueError("Missing OpenAI API key.")
    # print(config('OPENAI_API_KEY'))

    prompt_text = f"Given the text: \"{learning_goal}\", identify 10 most relevant keywords or tags that can help categorize articles related to this topic. Create a list based on relevance. Return the list as comma separated values"
    # print(prompt_text)
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": prompt_text}])
            # max_tokens=5)

    #     # keywords = response.choices[0].text.strip()fetc
        generateTags = response.choices[0].message.content.strip()
        print(generateTags)
        return Response({'status': 'success', 'GeneratedTags': generateTags})


        # return Response({'keywords': keywords})
    except Exception as e:
        print(f"OpenAI API call failed: {e}")
        return Response({'error': 'Failed to process the request'}, status=500)
        # return Response({'error': str(e)}, status=500)


@api_view(['POST'])
def generate_summary(request):
    content = request.data.get('content')
    
    if not content:
        return Response({'error': 'No text provided!'}, status=400)
    
    client = OpenAI(api_key=config('OPENAI_API_KEY'))

    if not client:
        raise ValueError("Missing OpenAI API key.")
    # print(config('OPENAI_API_KEY'))

    prompt_text = f"Given the text: \"{content}\", generate a summary which would make sense when an audio is generated from it."
    # print(prompt_text)
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": prompt_text}])
            # max_tokens=5)

    #     # keywords = response.choices[0].text.strip()
        generatedSummary = response.choices[0].message.content.strip()
        print(generatedSummary)
        return Response({'status': 'success', 'generateSummary': generatedSummary})


        # return Response({'keywords': keywords})
    except Exception as e:
        print(f"OpenAI API call failed: {e}")
        return Response({'error': 'Failed to process the request'}, status=500)
        # return Response({'error': str(e)}, status=500)


def serve_audio(request, filename):
    # Define the path to the cache directory
    cache_directory = os.path.join(BASE_DIR, 'audio_cache')
    
    # Define the path to the requested audio file
    filepath = os.path.join(cache_directory, filename)

    # Check if the file exists
    if os.path.exists(filepath):
        # Serve the audio file
        with open(filepath, 'rb') as audio_file:
            response = FileResponse(audio_file)
            return response
    else:
        # Return a 404 response if the file does not exist
        return HttpResponseNotFound("Audio file not found")


@api_view(['POST'])
def generate_audio(request, cache_directory='audio_cache'):
    os.makedirs(cache_directory, exist_ok=True)

    # Extract the article content from the request.
    summary = request.data.get('articleContent')

    # Check if the article content is provided.
    if not summary:
        return Response({'error': 'No article content provided!'}, status=status.HTTP_400_BAD_REQUEST)
    
    client = OpenAI(api_key=config('OPENAI_API_KEY'))
    print("A")


    filename = f"{md5(summary.encode('utf-8')).hexdigest()}.mp3"
    filepath = os.path.join(cache_directory, filename)
    print("B")

    # Check if the file already exists
    if not os.path.exists(filepath):

        response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=summary,
    )
        
        print("C")

        
        # Save the audio file
        with open(filepath, 'wb') as audio_file:
            audio_file.write(response.content)
            print("D")

        print(f"Generated and saved audio to {filepath}")
        audio_data = open(filepath, 'rb')
        response = FileResponse(audio_data, content_type='audio/mpeg')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
    else:
        print(f"Audio file already cached at {filepath}")


    return
    


    # # The 'stream_to_file' method seems to imply you're saving to a file, 
    # # which may not be necessary if you're streaming audio back to the client.
    # audio_content = response.content

    # return HTTPResponse(audio_content)



# @api_view(['POST'])
# def play_audio(request):
#     # audio_player = request.data.get('learningGoal')
    
#     # if not learning_goal:
#     #     return Response({'error': 'No text provided!'}, status=400)
    
#     # client = OpenAI(api_key=config('OPENAI_API_KEY'))
#     client = OpenAI()

#     print("A")


#     response = client.audio.speech.create(
#         model="tts-1",
#         voice="alloy",
#         input="Hello world! This is a streaming test!",
#     )

#     print("B")

#     response.stream_to_file("output.mp3")

#     print("C")

#     if not client:
#         raise ValueError("Missing OpenAI API key.")
    
#     return Response({'status': 'success'})



