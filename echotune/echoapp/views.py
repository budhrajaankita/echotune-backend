from django.shortcuts import get_list_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer, TopicSerializer
from .models import UserProfile, Topic, GuestProfile

class RegisterUserAPIView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                return Response({
                    "user": UserSerializer(user).data,
                    "message": "User Created Successfully."
                }, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class UserPreferencesAPIView(APIView):
    
#     def post(self, request):
#         user_profile = request.user.userprofile
#         topic_ids = request.data.get('topics', [])
        
#         # Validate that the topics exist to avoid invalid data
#         topics = Topic.objects.filter(id__in=topic_ids)
#         if not topics.exists():
#             return Response({'error': 'Invalid topic IDs'}, status=status.HTTP_400_BAD_REQUEST)
        
#         user_profile.topics.set(topics)  # Clear any previous topics and set the new ones
#         user_profile.save()

#         serialized_topics = TopicSerializer(user_profile.topics.all(), many=True)
#         return Response({
#             'status': 'preferences updated',
#             'topics': serialized_topics.data
#         }, status=status.HTTP_200_OK)

class UserPreferencesAPIView(APIView):
    def post(self, request, *args, **kwargs):
        topic_ids = request.data.get('topics', [])
        # Validate topic IDs
        topics = get_list_or_404(Topic, id__in=topic_ids)

        # Create or update a GuestProfile
        guest_id = request.COOKIES.get('guest_id')
        if guest_id:
            guest_profile, created = GuestProfile.objects.get_or_create(id=guest_id)
        else:
            guest_profile = GuestProfile.objects.create()

        guest_profile.topics.set(topics)
        guest_profile.save()

        response = Response({'status': 'preferences updated for guest'})
        if not guest_id:
            response.set_cookie('guest_id', str(guest_profile.id))

        return response
