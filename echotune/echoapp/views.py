from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import UserProfile, GuestProfile, Topic, Source
from .serializers import UserSerializer
import requests
import uuid
from openai import OpenAI
from decouple import config
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken


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


@api_view(['POST'])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        # create token
        refresh = RefreshToken.for_user(user)
        resp =  Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            "message": "Login Successful."
        }, status=status.HTTP_200_OK)
        print(resp)
        return resp
    else:
        # Authentication failed
        return Response({"error": "Invalid username or password"}, status=status.HTTP_401_UNAUTHORIZED)
    

@api_view(['POST'])
def learning_goal(request):
    learning_goal = request.data.get('learningGoal')
    
    if not learning_goal:
        return Response({'error': 'No text provided!'}, status=400)
    
    client = OpenAI(api_key=config('OPENAI_API_KEY'))

    if not client:
        raise ValueError("Missing OpenAI API key.")
    # print(config('OPENAI_API_KEY'))

    prompt_text = f"Given the text: \"{learning_goal}\", identify 10 most relevant keywords or tags that can help categorize articles related to this topic. Create a list based on relevance. Return the list as comma separated values"
    print(prompt_text)
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": prompt_text}])
            # max_tokens=5)

    #     # keywords = response.choices[0].text.strip()
        generateTags = response.choices[0].message.content.strip()
        print(generateTags)
        return Response({'status': 'success', 'GeneratedTags': generateTags})


        # return Response({'keywords': keywords})
    except Exception as e:
        print(f"OpenAI API call failed: {e}")
        return Response({'error': 'Failed to process the request'}, status=500)
        # return Response({'error': str(e)}, status=500)




