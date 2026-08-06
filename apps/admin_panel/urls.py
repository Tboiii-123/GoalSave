from django.urls import path

from . import views

urlpatterns = [
    path(
        "",
        views.list_withdrawals
    ),

    # path(
    #     "<int:pk>/",
    #     views.retrieve_withdrawal
    # ),

    # Admin
    path(
        "withdrawal-list/",
        views.list_withdrawals
    ),

    path(
        "admin/<int:pk>/",
        views.retrieve_admin_withdrawal
    ),

    path(
        "withdrawal/<int:pk>/approve/",
        views.approve_withdrawal
    ),

    path(
        "withdrawal/<int:pk>/reject/",
        views.reject_withdrawal
    ),




    #User-details

    path("create-users/",views.reject_withdrawal),
    path("update-users/<int:user_id>/",views.update_user),
    path("users/",views.list_users),

    path("delete-users/<int:user_id>/",views.delete_user),
    

]