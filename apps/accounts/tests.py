
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User, Profile


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def registration_data():
    return {
        "username": "testuser",
        "email": "testuser@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "StrongPassword123!",
    }


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="loginuser@example.com",
        username="loginuser",
        first_name="Login",
        last_name="User",
        password="StrongPassword123!",
    )



@pytest.fixture
def profile_user(db):
    created_user = User.objects.create_user(
        email="profileuser@example.com",
        username="profileuser",
        first_name="Profile",
        last_name="User",
        password="StrongPassword123!",
    )

    profile = created_user.profile
    profile.country = "Nigeria"
    profile.state = "Lagos"
    profile.save()

    return created_user


@pytest.fixture
def logout_user(db):
    return User.objects.create_user(
        email="logoutuser@example.com",
        username="logoutuser",
        password="StrongPassword123!",
    )


@pytest.mark.django_db
def test_user_can_register_successfully(api_client, registration_data):
    response = api_client.post(
        reverse("register"),
        registration_data,
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED

    created_user = User.objects.get(email="testuser@example.com")
    assert created_user.check_password("StrongPassword123!")
    assert created_user.password != "StrongPassword123!"
    assert created_user.is_approved is False


@pytest.mark.django_db
def test_registration_rejects_duplicate_email(api_client, registration_data):
    User.objects.create_user(
        email="testuser@example.com",
        username="existinguser",
        password="ExistingPassword123!",
    )

    response = api_client.post(
        reverse("register"),
        registration_data,
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_registration_rejects_duplicate_username(api_client, registration_data):
    User.objects.create_user(
        email="existing@example.com",
        username="testuser",
        password="ExistingPassword123!",
    )

    response = api_client.post(
        reverse("register"),
        registration_data,
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_user_can_login_with_email_and_password(api_client, user):
    response = api_client.post(
        reverse("token_obtain_pair"),
        {
            "email": user.email,
            "password": "StrongPassword123!",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db
def test_login_rejects_wrong_password(api_client, user):
    response = api_client.post(
        reverse("token_obtain_pair"),
        {
            "email": user.email,
            "password": "WrongPassword123!",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_anonymous_user_cannot_access_profile(api_client):
    response = api_client.get(reverse("profile"))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_authenticated_user_can_retrieve_profile(api_client, profile_user):
    api_client.force_authenticate(user=profile_user)

    response = api_client.get(reverse("profile"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["profile"]["email"] == profile_user.email


@pytest.mark.django_db
def test_authenticated_user_can_update_first_name(api_client, profile_user):
    api_client.force_authenticate(user=profile_user)

    response = api_client.patch(
        reverse("profile"),
        {"first_name": "Updated"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    profile_user.refresh_from_db()
    assert profile_user.first_name == "Updated"


@pytest.mark.django_db
def test_logout_blacklists_refresh_token(api_client, logout_user):
    api_client.force_authenticate(user=logout_user)
    refresh = RefreshToken.for_user(logout_user)

    response = api_client.post(
        reverse("logout_view"),
        {"refresh": str(refresh)},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["detail"] == "Logout successful"


@pytest.mark.django_db
def test_logout_requires_refresh_token(api_client, logout_user):
    api_client.force_authenticate(user=logout_user)

    response = api_client.post(
        reverse("logout_view"),
        {},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST