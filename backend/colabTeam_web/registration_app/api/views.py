from django.contrib.auth import login, update_session_auth_hash
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from knox.views import LoginView as KnoxLoginView
from rest_framework import decorators, exceptions, permissions, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from .. import emails
from ..models import Profile, User
from ..tokens import email_verification_token_generator, password_reset_token_generator
from ..utils import TypedHttpRequest
from . import serializers


class LoginView(KnoxLoginView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.LoginSerializer

    def get_post_response_data(self, request: TypedHttpRequest, token, instance):
        user = serializers.UserSerializer(
            instance=request.user,
            context=self.get_context(),
        ).data
        return {
            "user": user,
            "token": {
                "expiry_date": self.format_expiry_datetime(instance.expiry),
                "key": token,
            },
        }

    def post(self, request: TypedHttpRequest, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]  # type: ignore
        profile = get_object_or_404(Profile, user=user)

        if not profile.is_verified:
            raise exceptions.PermissionDenied("Your email is not verified.")

        login(request, user)
        return super(LoginView, self).post(request, format)


class RegistrationView(CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.RegisterSerializer

    def get_validated_data(self, request: TypedHttpRequest) -> dict[str, str]:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        return serializer.validated_data  # type: ignore

    def post(self, request: TypedHttpRequest, format=None):
        data = self.get_validated_data(request)

        try:
            if get_object_or_404(User, username=data["username"]):
                raise exceptions.NotAcceptable("User with this username already exists")
            if get_object_or_404(User, email=data["email"]):
                raise exceptions.NotAcceptable(
                    "User with this email already exists",
                )
        except Http404:
            user = User.objects.create_user(
                username=data["username"],
                email=data["email"],
                password=data["password"],
            )

            emails.send_verification_email(request, user)

            return Response(None)


class ResendVerificationEmailView(CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.ResendVerificationEmailSerializer

    def get_validated_data(self, request: TypedHttpRequest) -> dict[str, str]:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        return serializer.validated_data  # type: ignore

    def post(self, request: TypedHttpRequest, format=None):
        data = self.get_validated_data(request)

        user = get_object_or_404(User, email=data["email"])

        emails.send_verification_email(request, user)

        return Response(None)


@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.AllowAny])
def verify_user(request, uid: int, token: str):
    user = get_object_or_404(User, pk=uid)

    profile: Profile = user.profile  # type: ignore
    if profile.is_verified:
        raise exceptions.PermissionDenied("Email is already verified")

    token_exists = email_verification_token_generator.check_token(user, token)
    if not token_exists:
        return Response(data="Token has expired.", status=status.HTTP_410_GONE)

    profile.is_verified = True
    profile.save()

    return redirect("http://localhost:5173/verify-email-success/")


class ForgotPasswordView(CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.ForgotPasswordSerializer

    def get_validated_data(self, request: TypedHttpRequest) -> dict[str, str]:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        return serializer.validated_data  # type: ignore

    def post(self, request: TypedHttpRequest, format=None):
        data = self.get_validated_data(request)

        user = get_object_or_404(User, email=data["email"])

        emails.send_password_reset_email(request, user)

        return Response(None)


class ResetPasswordView(CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.ResetPasswordSerializer

    def get_validated_data(self, request: TypedHttpRequest) -> dict[str, str]:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        return serializer.validated_data  # type: ignore

    def post(self, request: TypedHttpRequest, format=None):
        data = self.get_validated_data(request)

        user = get_object_or_404(User, pk=data["uid"])
        token_exists = password_reset_token_generator.check_token(user, data["token"])

        if not token_exists:
            return Response(data="Token has expired.", status=status.HTTP_410_GONE)

        user.set_password(data["new_password"])
        user.save()
        update_session_auth_hash(request, user)

        return Response(None)
