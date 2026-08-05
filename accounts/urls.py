from django.urls import path

from accounts.views import EmailLoginView, EmailLogoutView, RegisterView, VerifyEmailView, home

urlpatterns = [
    path("", home, name="home"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", EmailLoginView.as_view(), name="login"),
    path("logout/", EmailLogoutView.as_view(), name="logout"),
    path("verify/<uidb64>/<token>/", VerifyEmailView.as_view(), name="verify_email"),
]
