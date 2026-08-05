from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View

from accounts.forms import LoginForm, RegisterForm
from accounts.tokens import email_verification_token

User = get_user_model()


class RegisterView(View):
    template_name = "accounts/register.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect("home")
        return render(request, self.template_name, {"form": RegisterForm()})

    def post(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect("home")

        form = RegisterForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form}, status=400)

        user = form.save()
        self._send_verification_email(request, user)
        return render(
            request,
            "accounts/verify_pending.html",
            {"email": user.email},
        )

    def _send_verification_email(self, request: HttpRequest, user) -> None:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = email_verification_token.make_token(user)
        verify_path = reverse("verify_email", kwargs={"uidb64": uid, "token": token})
        domain = get_current_site(request).domain
        protocol = "https" if request.is_secure() else "http"
        verify_url = f"{protocol}://{domain}{verify_path}"

        send_mail(
            subject="Verify your email",
            message=(
                "Welcome!\n\n"
                f"Please verify your email by opening this link:\n{verify_url}\n"
            ),
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )


class VerifyEmailView(View):
    def get(self, request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
        user = self._get_user(uidb64)
        if user is None or not email_verification_token.check_token(user, token):
            return render(
                request,
                "accounts/verify_result.html",
                {
                    "ok": False,
                    "message": "This verification link is invalid or has expired.",
                },
                status=400,
            )

        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])

        return render(
            request,
            "accounts/verify_result.html",
            {
                "ok": True,
                "message": "Your email is verified. You can log in now.",
            },
        )

    def _get_user(self, uidb64: str):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            return User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None


class EmailLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class EmailLogoutView(LogoutView):
    next_page = reverse_lazy("login")


@login_required
def home(request: HttpRequest) -> HttpResponse:
    return render(request, "accounts/home.html")
