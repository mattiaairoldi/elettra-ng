from django.urls import path

from .views import (
    ForgotPasswordView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    ResetPasswordView,
    TokenLoginView,
    TokenLogoutView,
    TokenRefreshView,
    VerifyEmailView,
)


app_name = "identity"

urlpatterns = [
    path("register", RegisterView.as_view(), name="register"),
    path("login", LoginView.as_view(), name="login"),
    path("token/login", TokenLoginView.as_view(), name="token-login"),
    path("token/refresh", TokenRefreshView.as_view(), name="token-refresh"),
    path("token/logout", TokenLogoutView.as_view(), name="token-logout"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("me", MeView.as_view(), name="me"),
    path("forgot-password", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password", ResetPasswordView.as_view(), name="reset-password"),
    path("verify-email", VerifyEmailView.as_view(), name="verify-email"),
]
