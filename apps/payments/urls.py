from django.urls import path
from . import views
from . import services


urlpatterns = [
    # Initialize deposit (Paystack)
    path(
        "deposit/",
        views.initialize_deposit,
        name="initialize-deposit"
    ),

    # Deposit history
    path(
        "deposits/",
        views.list_deposits,
        name="list-deposits"
    ),

    # Verify deposit (manual check)
    path(
        "verify/<str:reference>/",
        views.verify_deposit,
        name="verify-deposit"
    ),

     path("webhook/", services.paystack_webhook, name="paystack-webhook"),
]