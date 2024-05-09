import random
import re
from echotune.settings import BASE_DIR
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework import status
from .models import UserProfile, GuestProfile, Topic, Source, Hashtag
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

openai_voices = ["echo","alloy","shimmer","nova", "fable"]

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
    hashtags_names = request.data.get('hashtags', [])
    print(topics_names)
    print(sources_names)
    print(hashtags_names)

    if is_guest and session_id:
        profile, _ = GuestProfile.objects.get_or_create(session_id=session_id)
    else:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

    # Save topics and sources for either profile
    # profile.topics.clear()
    # for name in topics_names:
    #     topic, _ = Topic.objects.get_or_create(name=name)
    #     profile.topics.add(topic)

    # # profile.sources.clear()
    # for name in sources_names:
    #     source, _ = Source.objects.get_or_create(name=name)
    #     profile.sources.add(source)
    
    # # profile.hashtags.clear()
    # for name in hashtags_names:
    #     hashtag, _ = Hashtag.objects.get_or_create(name=name)
    #     hashtag.topics.set(profile.topics.all())
    #     profile.hashtags.add(hashtag)

    # Update topics
    new_topics = [Topic.objects.get_or_create(name=name)[0] for name in topics_names]
    profile.topics.set(new_topics)  # Update topics association

    # Update sources
    new_sources = [Source.objects.get_or_create(name=name)[0] for name in sources_names]
    profile.sources.set(new_sources)  # Update sources association

    # Update hashtags
    new_hashtags = [Hashtag.objects.get_or_create(name=name)[0] for name in hashtags_names]
    for hashtag in new_hashtags:
        hashtag.topics.set(new_topics)
        profile.hashtags.add(hashtag)
    
    profile.save()

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
def get_user_hashtags(request):
    if request.user.is_authenticated:
        user_profile = request.user.userprofile
        hashtags = user_profile.hashtags.all()
        hashtags_data = [{'id': hashtag.id, 'name': hashtag.name} for hashtag in hashtags]
        return Response(hashtags_data)
    else:
        return Response({"error": "User is not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_topics_for_hashtag(request, hashtag_name):
    is_guest = request.query_params.get('is_guest') == 'true'
    session_id = request.query_params.get('session_id', None)

    if is_guest and session_id:
        profile = GuestProfile.objects.filter(session_id=session_id).first()
    else:
        profile = UserProfile.objects.filter(user=request.user).first()

    if not profile:
        return Response({"error": "Profile not found"}, status=404)

    try:
        hashtag = Hashtag.objects.get(name=hashtag_name)

        # Check if the profile is associated with this hashtag
        if is_guest:
            if not profile.hashtags.filter(id=hashtag.id).exists():
                return Response({"error": "Hashtag not found for this guest"}, status=404)
        else:
            if not profile.hashtags.filter(id=hashtag.id).exists():
                return Response({"error": "Hashtag not found for this user"}, status=404)

        topics = hashtag.topics.all()
        topics_data = [{'id': topic.id, 'name': topic.name} for topic in topics]
        return Response(topics_data)
    except Hashtag.DoesNotExist:
        return Response({"error": "Hashtag not found"}, status=404)


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def fetch_news(request):
#     is_guest = request.query_params.get('is_guest')
#     session_id = request.query_params.get('session_id', None)
#     topics_query = request.query_params.get('q', None).replace('"', '').strip()
#     print(f"Original topics_query is: {topics_query}")

#     if is_guest and session_id:
#         profile = GuestProfile.objects.filter(session_id=session_id).first()
#     else:
#         profile = UserProfile.objects.filter(user=request.user).first()

#     if not profile:
#         return Response({"error": "Profile not found"}, status=404)
    
#     def get_articles(query):
#         query_params = {
#             'q': query,
#             'lang': 'en',
#             'sortBy': 'publishedAt',
#             'apikey': settings.GNEWS_API_KEY,
#             'max': 20,
#             'expand': 'content'
#         }
#         response = requests.get('https://gnews.io/api/v4/search', params=query_params)
#         response.raise_for_status()
#         return response.json().get('articles', [])
    
#     try:
#         articles = get_articles(topics_query)

#         # Fall back to a broader query if no articles found
#         if not articles:
#             print(f"No articles found for query: {topics_query}")
#             broad_query = topics_query.split(" OR ")[0]  # Use only the first part of the query
#             articles = get_articles(broad_query)

#         if not articles:
#             return Response({"error": "No articles found"}, status=404)

#         formatted_news = [{
#             "id": idx,
#             "title": article["title"],
#             "description": article["description"],
#             "content": article["content"],
#             "url": article["url"],
#             "image": article["image"],
#             "publishedAt": article["publishedAt"],
#             "source_name": article["source"]["name"],
#             "source_url": article["source"]["url"]
#         } for idx, article in enumerate(articles[:20])]

#         return Response(formatted_news)

#     except requests.RequestException as e:
#         return Response({"error": str(e)}, status=500)


def format_news_articles(articles):
    formatted_news = [
        {
            "id": idx,
            "title": article["title"],
            "description": article["description"],
            "content": article["content"],
            "url": article["url"],
            "image": article["image"],
            "publishedAt": article["publishedAt"],
            "source_name": article["source"]["name"],
            "source_url": article["source"]["url"]
        }
        for idx, article in enumerate(articles[:20])
    ]
    return formatted_news

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

    topics_query = ' OR '.join([f'"{topic.name.strip()}"' for topic in profile.topics.all()])

    print(topics_query)

    query_params = {
        'q': topics_query,
        'lang': 'en', 
        'sortBy': 'publishedAt',
        'apikey': settings.GNEWS_API_KEY,
        'max': 10,
        'expand': 'content'
    }

    try:
        response = requests.get('https://gnews.io/api/v4/search', params=query_params)
        response.raise_for_status()  # Raises a HTTPError for bad responses
        articles = response.json().get('articles', [])

        if len(articles) < 10:
            query_params['q'] = ' OR '.join([f'({topic.name.strip()})' for topic in profile.topics.all()])

            response = requests.get('https://gnews.io/api/v4/search', params=query_params)
            response.raise_for_status()
            articles.extend(response.json().get('articles', []))

        if not articles:
            return Response({"error": "No articles found"}, status=404)

        formatted_news = format_news_articles(articles)
        return Response(formatted_news)
    except requests.RequestException as e:
        return Response({"error": str(e)}, status=500)
    

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
                "message": "🧏🏻‍♀️ User Created Successfully."
            }, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def clean_keywords(keywords):
  clean_keywords = []
  # Check for unexpected format (optional)
  if len(keywords.split(',')) < 5:
    raise ValueError("Incorrect number of keywords (expected 10)")
  
  for keyword in keywords.split(','):
    cleaned_keyword = re.sub(r',.^"|"$-[0-9]', '', keyword)
    cleaned_keyword = cleaned_keyword.replace('"', '')
    clean_keyword = cleaned_keyword.replace(',', ' ').split(' ')
    cleaned_keyword = cleaned_keyword.strip()
    clean_keyword = ' '.join(clean_keyword)
    clean_keywords.append(clean_keyword)

  return (clean_keywords)
     

@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def learning_goal(request):
    learning_goal = request.data.get('learningGoal')
    
    if not learning_goal:
        return Response({'error': 'No text provided!'}, status=400)
    
    client = OpenAI(api_key=config('OPENAI_API_KEY'))

    if not client:
        raise ValueError("Missing OpenAI API key.")
    

    # prompt_text = f"Given the user goal: \"{learning_goal}\", create an ordered comma separated values List of 10 most relevant keywords that might help identify news articles. confirm the format of output: keyword a, keyword b, keyword c"
    # prompt_text = f"Take this learning goal : \"{learning_goal}\" and come up with 10 distinct most relevant 1-2 word search query strings to retrieve articles about this topic. Return these 10 queries in comma separated values (CSV) format"
    prompt_text=f"Take this learning goal: \"{learning_goal}\" and come up with 10 distinct most relevant 1-2 word search query strings to retrieve articles about this topic. Return these 10 queries in comma separated values (CSV) format. Don't add anything extra except the queries. No inverted commas, hyphens, any other extra text. Nothing else - just the queries in x, y, z format."
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "system", "content": "You are a helpful assistant designed to output comma separated values.",
                "role": "user", "content": prompt_text}])
                # "role": "user",
                # "content": prompt_text}])
            # max_tokens=5)

    #     # keywords = response.choices[0].text.strip()

        keywords = response.choices[0].message.content.strip()
        print(keywords)
        print(len(keywords.split(',')))
        if len(keywords.split(',')) > 5:
            clean = clean_keywords(keywords)
            print('clean_keywords {}'.format(clean))
            return Response({'status': 'success', 'GeneratedTags': clean})
        

        elif "\n" in keywords:
            keywords = [keyword.strip().rstrip(',') for keyword in keywords.split('\n')]
            keywords = [keyword.strip('"') for keyword in keywords]
            pattern = r"^\d+\.\s?"
            keywords = [re.sub(pattern, "", keyword) for keyword in keywords]
            print("here {}".format(keywords))

        elif len(keywords.split(',')) == 1:
            keywords = keywords.split(',')
        if len(keywords) < 1:
            return Response({'error': 'Failed to generate keywords'}, status=500)
        return Response({'status': 'success', 'GeneratedTags': keywords})
    except Exception as e:
        print(f"OpenAI API call failed: {e}")
        return Response({'error': 'Failed to process the request'}, status=500)


@api_view(['POST'])
def generate_summary(request):
    content = request.data.get('content')
    
    if not content:
        return Response({'error': 'No text provided!'}, status=400)
    
    client = OpenAI(api_key=config('OPENAI_API_KEY'))

    if not client:
        raise ValueError("Missing OpenAI API key.")

    # prompt_text = f"Given the text: \"{content}\", generate a summary which would make sense when an audio is generated from it."
    prompt_text = f"Given the text: \"{content}\", generate a summary for spoken delivery of the following article that should last between 1 to 2 minutes. Focus on capturing the main points, important details, and any notable quotes or statistics. The summary should be engaging, easy to follow, and provide a clear understanding of the article's content. Don't give me keywords like hello, today, summary, good morning in the output. Get to the point."

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": prompt_text}])
            # max_tokens=5)

        generatedSummary = response.choices[0].message.content.strip()
        print(generatedSummary)
        return Response({'status': 'success', 'generateSummary': generatedSummary})

    except Exception as e:
        print(f"OpenAI API call failed: {e}")
        return Response({'error': 'Failed to process the generate summary request'}, status=500)


@api_view(['POST'])
def getHashtag(request):
    content = request.data.get('learningGoal')
    if not content:
        return Response({'error': 'No text provided!'}, status=400)
    
    client = OpenAI(api_key=config('OPENAI_API_KEY'))

    if not client:
        raise ValueError("Missing OpenAI API key.")

    prompt_text = f"Give me a hashtag for this learning goal which isn't too long: \"{content}\""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": prompt_text}])
            # max_tokens=5)

        generatedHashtag = response.choices[0].message.content.strip()
        print("generatedHashtag {}".format(generatedHashtag))
        return Response({'status': 'success', 'generatedHashtag': generatedHashtag})

    except Exception as e:
        print(f"OpenAI API call failed: {e}")
        return Response({'error': 'Failed to process the generate summary request'}, status=500)


def sanitize_filename(title):
    sanitized = re.sub(r'[^\w\s-]', '', title)
    sanitized = re.sub(r'[-\s]+', ' ', sanitized)
    sanitized = sanitized.strip('-')
    return sanitized


@api_view(['POST'])
def generate_audio(request, cache_directory='audio_cache'):
    os.makedirs(cache_directory, exist_ok=True)

    # Extract the article content from the request.
    summary = request.data.get('articleContent')
    title = request.data.get('articleTitle')
    voice_name = random.choice(openai_voices)

    # Check if the article content is provided.
    if not summary:
        return Response({'error': 'No article content provided!'}, status=status.HTTP_400_BAD_REQUEST)
    
    client = OpenAI(api_key=config('OPENAI_API_KEY'))
    print(title)

    title_sanitized = sanitize_filename(title[:20])
    filename = f"{title_sanitized}.wav"
    
    filepath = os.path.join(cache_directory, filename)

    # Check if the file already exists
    if not os.path.exists(filepath):

        response = client.audio.speech.create(
        model="tts-1",
        voice=voice_name,
        input=summary,
    )      
        # Save the audio file
        with open(filepath, 'wb') as audio_file:
            audio_file.write(response.content)

        print(f"Generated and saved audio to {filepath}")
    else:
        print(f"Audio file already cached at {filepath}")

    audio_data = open(filepath, 'rb')

    response = FileResponse(audio_data, content_type='audio/mp3')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    # return response
    return response

    
# @api_view(['POST'])
# def generate_audio(request, cache_directory='audio_cache'):
#   os.makedirs(cache_directory, exist_ok=True)

#   # Extract the article content from the request.
#   summary = request.data.get('articleContent')
#   title = request.data.get('articleTitle')

#   if not summary:
#     return Response({'error': 'No article content provided!'}, status=status.HTTP_400_BAD_REQUEST)


#   XI_API_KEY = "a5b1689de55886b8285a34e04ef7dafa"

#   VOICE_ID = "EXAVITQu4vr4xnSDxMaL"

#   title_sanitized = sanitize_filename(title[:20])
#   filename = f"{title_sanitized}.mp3"
#   filepath = os.path.join(cache_directory, filename)

#   # Check if the file already exists
#   if not os.path.exists(filepath):
#     # Construct the TTS API URL
#     tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"

#     # Headers with your API key
#     headers = {
#       "Accept": "application/json",
#       "xi-api-key": XI_API_KEY
#     }

#     # Data payload with text and voice settings (optional)
#     data = {
#                 "text": summary,
#                 "model_id": "eleven_turbo_v2",
#                 "voice_settings": {
#                     "stability": 0.5,
#                     "similarity_boost": 0.1,
#                     "style": 0.95,
#                     "use_speaker_boost": True,
#                     "optimize_streaming_latency": 3
#                 }
#          }

#     # Make the POST request with streaming enabled
#     response = requests.post(tts_url, headers=headers, json=data, stream=True)

#     # Check for successful request
#     if response.ok:
#       with open(filepath, 'wb') as audio_file:
#         for chunk in response.iter_content(chunk_size=1024):
#           audio_file.write(chunk)
#           print(filepath)

      
#       print(f"Generated and saved audio to {filepath}")
#     else:
#       print(f"Error during TTS request: {response.text}")

#   else:
#     print(f"Audio file already cached at {filepath}")

#   audio_data = open(filepath, 'rb')
#   response = FileResponse(audio_data, content_type='audio/mpeg')
#   response['Content-Disposition'] = f'attachment; filename={filename}'
#   return response
