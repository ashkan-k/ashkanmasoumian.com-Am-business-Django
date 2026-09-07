from django.urls import path
from . import views

urlpatterns = [
    path("", views.accounts_redirect, name="accounts_redirect"),
]
