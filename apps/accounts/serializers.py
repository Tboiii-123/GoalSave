from rest_framework import serializers
from .models import User,Profile


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password"
        ]

    def create(self, validated_data):
        user = User(email=validated_data['email'],username=validated_data['username'],first_name =validated_data['first_name'], last_name=validated_data['last_name'])
        user.set_password(validated_data['password'])
        user.save()
        return user


# If dey are optional
#     username=validated_data.get('username'),
        # first_name=validated_data.get('first_name'),
        # last_name=validated_data.get('last_name')


class ProfileSerializer(serializers.ModelSerializer):
    # avatar = serializers.SerializerMethodField()

    # def get_image(self, obj):
    #     if obj.avatar:
    #         return obj.avatar.url
    #     return None
    class Meta:
        model = Profile
        fields = [
            "phone_number",
            "home_address",
            "dob",
            "country",
            "state",
            # "avatar",

        ]



class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "profile"
        ]

    def update(self, instance, validated_data):

        profile_data = validated_data.pop("profile", None)

        # update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # update profile fields
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


# class GoogleAuthSerializer(serializers.Serializer):
#     id_token = serializers.CharField(required=True)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()