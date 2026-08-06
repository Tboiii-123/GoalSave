from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,throttle_classes
# Create your views here.
from .serializers import RegisterSerializer, UserSerializer,ProfileSerializer,LogoutSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from apps.utils.throttles import RegisterThrottle,MessageThrottle

from .models import User

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
)



@extend_schema(
    tags=["Authentication"],
    summary="Register a new user",
    description="Creates a new GoalSave user account.",
    request=RegisterSerializer,
    responses={
        201: RegisterSerializer,
        400: OpenApiResponse(description="Validation error"),
    },
)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RegisterThrottle])
def register_view(request):
    serializer =RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
      

        return Response({
             "message": "User registered successfully ",
            "data": serializer.data
        }, status =201)

    return Response({
        "error":serializer.errors
    }, status=400)



@extend_schema(
    tags=["Authentication"],
    summary="List users",
    description="Returns all registered users.",
    responses={
        200: UserSerializer(many=True),
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def get_users(request):
    users = User.objects.select_related("profile").all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)



@extend_schema(
    methods=["GET"],
    tags=["Authentication"],
    summary="Retrieve my profile",
    description="Returns the authenticated user's profile.",
    responses={
        200: ProfileSerializer,
    },
)
@extend_schema(
    methods=["PATCH"],
    tags=["Authentication"],
    summary="Update my profile",
    description="Updates the authenticated user's profile.",
    request=ProfileSerializer,
    responses={
        200: ProfileSerializer,
        400: OpenApiResponse(description="Validation error"),
    },
)
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def my_profile(request):
    profile = request.user

    if request.method == "GET":
        serializer = UserSerializer(profile)
        return Response(
               {
            "message": "Profile",
            "profile": serializer.data
        },
        )

    serializer = User(
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



@extend_schema(
    tags=["Authentication"],
    summary="Logout",
    description="Logs out the authenticated user by blacklisting the provided refresh token.",
    request=LogoutSerializer,
    responses={
        200: OpenApiResponse(description="Logout successful"),
        400: OpenApiResponse(description="Invalid or missing refresh token"),
    },
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
