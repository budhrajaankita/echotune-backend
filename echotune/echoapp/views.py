from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import UserProfile, GuestProfile, Topic, Source
from .serializers import UserSerializer
import requests
import uuid

@api_view(['POST'])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        if user:
            return Response({
                "user": UserSerializer(user).data,
                "message": "User Created Successfully."
            }, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def save_preferences(request):
    is_guest = request.data.get('is_guest')
    session_id = uuid.UUID(request.data.get('session_id', None))
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

    query = ' OR '.join([topic.name for topic in topics])
    sources_query = 'source:(' + ' OR '.join([source.name for source in sources]) + ')'

    api_url = f'https://newsapi.org/v2/everything?q={query} AND {sources_query}&apiKey=YOUR_API_KEY'
    response = requests.get(api_url)
    news_data = response.json()

    formatted_news = [{"id": idx, "title": article["title"]} for idx, article in enumerate(news_data.get('articles', []))]

    return Response(formatted_news)
