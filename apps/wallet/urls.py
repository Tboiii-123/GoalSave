from django.urls import path

from . import views

urlpatterns = [
    path("",views.get_wallet,name="get-wallet"),

    path("transactions/",views.wallet_transactions,name="wallet-transactions"),
]