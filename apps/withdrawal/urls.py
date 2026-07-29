from django.urls import path

from . import views

urlpatterns = [
    path("request/", views.request_withdrawal, name='request_withdrwal'),

    path("list/", views.list_withdrawals, name='list_withdrwals'),
    
]