from django.urls import path

from . import views

urlpatterns = [
path("goals/summary/",views.goal_summary,name="goal-summary"),
path("goals/",views.monthly_savings,name="monthly-savings"),
path("goals/top/",views.top_saving_goals,name="top-saving-goals"),
]