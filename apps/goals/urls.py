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
    path("<int:pk>/fund/",views.fund_goal,name="fund-goal")
]