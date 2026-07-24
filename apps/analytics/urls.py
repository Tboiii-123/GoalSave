from django.urls import path

from . import views

urlpatterns = [
path("goals/summary/",views.goal_summary,name="goal-summary"),
path("goals/",views.monthly_savings,name="monthly-savings"),
path("goals/top/",views.top_saving_goals,name="top-saving-goals"),
path("goals/recent-fundings/",views.recent_goal_fundings,name="recent-goal-fundings"),
path( "goals/<int:goal_id>/funding/",views.goal_funding_details,name="goal-funding-details"),
]