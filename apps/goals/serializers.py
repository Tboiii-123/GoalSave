from rest_framework import serializers
from .models import SavingsGoal,GoalMember,GoalInvitation,GoalFunding
from decimal import Decimal
from drf_spectacular.utils import extend_schema_field


class SavingsGoalSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    class Meta:
        model = SavingsGoal
        fields = [
            "id",
            "name",
            "description",
            "target_amount",
            "saved_amount",
            "target_date",
            "status",
            "progress",
            "is_shared",
            "created_at",
            "updated_at",
        ]
        read_only_fields = (
            "saved_amount",
            "status",
            "created_at",
            "updated_at",
        )

    def get_progress(self, obj) -> float:
        if not obj.target_amount or obj.target_amount <= 0 or obj.target_amount == 0:
            return 0

        return round(
            (obj.saved_amount / obj.target_amount) * 100,2)

    def validate_target_amount(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError(
            "Target amount must be greater than zero."
        )
        return value

class GoalFundingSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    def validate_amount(self, value):
        if value <= Decimal("0"):
            raise serializers.ValidationError(
                "Amount must be greater than zero."
            )

        return value
   



class GoalInvitationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class GoalMemberSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = GoalMember
        fields = (
            "id",
            "full_name",
            "email",
            "role",
            "joined_at",
        )
    
    @extend_schema_field(str)
    def get_full_name(self, obj) -> str:
        return f"{obj.owner.first_name} {obj.owner.last_name}".strip()



class GoalInvitationListSerializer(serializers.ModelSerializer):
    goal_name = serializers.CharField(source="goal.name", read_only=True)
    owner = serializers.EmailField(source="goal.user.email", read_only=True)
    target_amount = serializers.DecimalField(
        source="goal.target_amount",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = GoalInvitation
        fields = (
            "id",
            "token",
            "goal_name",
            "owner",
            "target_amount",
            "status",
            "expires_at",
            "created_at",
        )


class GoalContributionSerializer(serializers.ModelSerializer):
    contributor = serializers.SerializerMethodField()

    class Meta:
        model = GoalFunding
        fields = (
            "id",
            "contributor",
            "amount",
            "created_at",
        )
    
    @extend_schema_field(str)
    def get_contributor(self, obj) -> str:
        return {
            "id": obj.user.id,
            "name": f"{obj.user.first_name} {obj.user.last_name}".strip(),
            "email": obj.user.email,
        }




class MessageSerializer(serializers.Serializer):
    detail = serializers.CharField()


class GoalInvitationResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    token = serializers.UUIDField()




#AI Integrtaion prompt

class SmartGoalPlannerSerializer(serializers.Serializer):
    prompt = serializers.CharField(
        required=True,
        allow_blank=False,
    )




class SmartGoalPlanSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)

    target_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True,
    )

    target_date = serializers.DateField(
        required=False,
        allow_null=True,
    )

    is_shared = serializers.BooleanField(
        default=False
    )

    def validate_target_amount(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "Target amount must be greater than zero."
            )

        return value