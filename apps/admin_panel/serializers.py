from rest_framework import serializers
from django.db import transaction
from apps.accounts.models import User, Profile


class AdminUserSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    home_address = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    country = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    state = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    dob = serializers.DateField(
        write_only=True,
        required=False,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
            "role",
            "is_approved",
            "is_suspended",
            "phone_number",
            "home_address",
            "country",
            "state",
            "dob",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]

        extra_kwargs = {
            "password": {
                "write_only": True
            }
        }

    @transaction.atomic
    def create(self, validated_data):

        profile_data = {
            "phone_number": validated_data.pop("phone_number", ""),
            "home_address": validated_data.pop("home_address", ""),
            "country": validated_data.pop("country", ""),
            "state": validated_data.pop("state", ""),
            "dob": validated_data.pop("dob", None),
        }

        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        Profile.objects.create(
            user=user,
            **profile_data
        )

        return user

    @transaction.atomic
    def update(self, instance, validated_data):

        profile = instance.profile

        profile.phone_number = validated_data.pop(
            "phone_number",
            profile.phone_number
        )

        profile.home_address = validated_data.pop(
            "home_address",
            profile.home_address
        )

        profile.country = validated_data.pop(
            "country",
            profile.country
        )

        profile.state = validated_data.pop(
            "state",
            profile.state
        )

        profile.dob = validated_data.pop(
            "dob",
            profile.dob
        )

        profile.save()

        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        return instance


class RejectWithdrawalSerializer(serializers.Serializer):
    remarks = serializers.CharField(required=False, allow_blank=True)





class WithdrawalApprovalResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    reference = serializers.CharField()
    status = serializers.CharField()





class AdminMessageSerializer(serializers.Serializer):
    detail = serializers.CharField()