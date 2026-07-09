from  django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path('auth/register/', views.register_view, name='register'),
    #Return access token ad refresh token
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('auth/logout/', views.logout_view, name='logout_view'),

    path('auth/profile/',views.my_profile, name='profile'),

    path('auth/get_all_user/',views.get_users, name='profile'),
    


]