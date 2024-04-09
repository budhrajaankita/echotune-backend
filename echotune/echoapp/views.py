from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework import status
from .models import UserProfile, GuestProfile, Topic, Source
from .serializers import UserSerializer
import requests
import uuid
from django.conf import settings

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
@permission_classes([IsAuthenticated])
def save_preferences(request):
    is_guest = request.data.get('is_guest')
    session_id_str = request.data.get('session_id', None)

    try:
        session_id = uuid.UUID(session_id_str) if session_id_str else None
    except ValueError:
        return Response({"error": "Invalid session_id provided"}, status=status.HTTP_400_BAD_REQUEST)

    topics_names = request.data.get('topics', [])
    sources_names = request.data.get('sources', [])

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
def fetch_news(request):
    is_guest = request.query_params.get('is_guest')
    session_id = request.query_params.get('session_id', None)

    if is_guest and session_id:
        profile = GuestProfile.objects.filter(session_id=session_id).first()
    else:
        profile = UserProfile.objects.filter(user=request.user).first()

    if not profile:
        return Response({"error": "Profile not found"}, status=404)

    topics = profile.topics.all()
    sources = profile.sources.all()

    # Constructing the query
    topics = [topic.name for topic in profile.topics.all()]
    topics_query = ' OR '.join(topics)
    query_params = {
        'q': topics_query,
        'lang': 'en', 
        'sortBy': 'publishedAt',  # Sort by publication date
        'apikey': settings.GNEWS_API_KEY,
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
