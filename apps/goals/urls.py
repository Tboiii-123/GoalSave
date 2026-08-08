from django.urls import path

from . import views

urlpatterns = [
    # Create & List
    path("", views.list_goals, name="list-goals"),
    path("create/", views.create_goal, name="create-goal"),

    # Goal CRUD
    path("<int:pk>/", views.retrieve_goal, name="retrieve-goal"),

    path("<int:pk>/delete/", views.delete_goal, name="delete-goal"),

    # Goal Status
    path("<int:pk>/pause/", views.pause_goal, name="pause-goal"),
    path("<int:pk>/resume/", views.resume_goal, name="resume-goal"),
    path("<int:pk>/complete/", views.complete_goal, name="complete-goal"),
    path("<int:pk>/fund/",views.fund_goal,name="fund-goal"),

      # Invitations
    path(
        "<int:pk>/invite/",
        views.invite_goal_member,
        name="invite-goal-member",
    ),

    path(
        "invitations/<uuid:token>/accept/",
        views.accept_goal_invitation,
        name="accept-goal-invitation",
    ),

    path(
        "invitations/<uuid:token>/decline/",
        views.decline_goal_invitation,
        name="decline-goal-invitation",
    ),

    path(
        "invitations/",
        views.my_goal_invitations,
        name="my-goal-invitations",
    ),

    # Members
    path(
        "<int:pk>/members/",
        views.goal_members,
        name="goal-members",
    ),

    path(
        "<int:goal_id>/members/<int:member_id>/remove/",
        views.remove_goal_member,
        name="remove-goal-member",
    ),

    path(
        "<int:pk>/leave/",
        views.leave_shared_goal,
        name="leave-shared-goal",
    ),

    # Contributions
    path(
        "<int:pk>/contributions/",
        views.goal_contributions,
        name="goal-contributions",
    ),

     path(
        "ai/plan-goal/",
        views.smart_goal_planner,
        name="smart-goal-planner",
    ),
]