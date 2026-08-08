from django.urls import path

from accounts.tournament_views import (
    tournament_create,
    tournament_detail,
    tournament_join,
    tournament_lobby,
    tournament_ready,
    tournament_status,
)
from accounts.views import EmailLoginView, EmailLogoutView, RegisterView, VerifyEmailView, home

urlpatterns = [
    path("", home, name="home"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", EmailLoginView.as_view(), name="login"),
    path("logout/", EmailLogoutView.as_view(), name="logout"),
    path("verify/<uidb64>/<token>/", VerifyEmailView.as_view(), name="verify_email"),
    path("tournaments/create/", tournament_create, name="tournament_create"),
    path("tournaments/join/", tournament_join, name="tournament_join"),
    path("tournaments/<int:pk>/lobby/", tournament_lobby, name="tournament_lobby"),
    path("tournaments/<int:pk>/ready/", tournament_ready, name="tournament_ready"),
    path("tournaments/<int:pk>/status/", tournament_status, name="tournament_status"),
    path("tournaments/<int:pk>/", tournament_detail, name="tournament_detail"),
]
