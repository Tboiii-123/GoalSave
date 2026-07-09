from django.urls import path
from . import views






urlpatterns = [
    path( "admin/ledger/", views.list_ledger_entries, name="admin-ledger-list"),


    path("admin/ledger/user/<int:user_id>/",views.list_user_ledger_entries,name="admin-user-ledger-list"),

    path( "admin/ledger/<int:pk>", views.retrieve_ledger_entry, name="retrieve_ledger_entry"),
    
]