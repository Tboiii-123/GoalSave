from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,throttle_classes
# Create your views here.
from .serializers import RegisterSerializer, UserSerializer,ProfileSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User




@api_view(['POST'])
@permission_classes([AllowAny])
# @throttle_classes([RegisterThrottle])
def register_view(request):
    serializer =RegisterSerializer(data=request.data)
    if serializer.is_valid():
        register=serializer.save()
      

        return Response({
             "message": "User registered successfully ",
            "data": serializer.data
        }, status =201)
    print(serializer.errors)
    return Response({
        "error":serializer.errors
    }, status=400)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
# @throttle_classes([UserThrottle])
def get_users(request):
    users = User.objects.select_related("profile").all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)




@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def my_profile(request):
    profile = request.user.profile

    if request.method == "GET":
        serializer = ProfileSerializer(profile)
        return Response(
               {
            "message": "Profile",
            "profile": serializer.data
        },
        )

    serializer = ProfileSerializer(
        profile,
        data=request.data,
        partial=True
    )

    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        {
            "message": "Profile updated successfully.",
            "profile": serializer.data
        },
        status=status.HTTP_200_OK
    )



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
        
    try:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token is required"}, status=400)
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"detail": "Logout successful"})
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=400)
       


#Google Auth Login


# @api_view(["POST"])
# @permission_classes([AllowAny])
# @throttle_classes([LoginThrottle])
# def google_login(request):

#     serializer = GoogleAuthSerializer(data=request.data)

#     serializer.is_valid(raise_exception=True)

#     try:
#         token = serializer.validated_data["id_token"]

#         payload = GoogleAuthService.verify_google_token(token)

#         user = GoogleAuthService.create_or_update_user(payload)

#         refresh = (
#             RefreshToken.for_user(user)
#         )

#         return Response(
#             {
#                 "status": True,
#                 "message":
#                 "Google login successful",

#                 "user": {
#                     "email": user.email,
#                     "user_name": user.user_name,
#                     "first_name": user.first_name,
#                     "last_name":user.last_name,
#                 },

#                 "tokens": {
#                 "access": str(refresh.access_token),
#                 "refresh":str(refresh),
#                 }
#             },
#             status=status.HTTP_200_OK
#         )

#     except ValueError as e:
#         return Response(
#             {
#                 "status": False,
#                 "message": str(e)
#             },
#             status=status.HTTP_400_BAD_REQUEST
#         )
