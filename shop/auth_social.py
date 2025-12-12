from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from social_django.utils import load_backend, load_strategy
from django.contrib.auth import login
from rest_framework_simplejwt.tokens import RefreshToken


class SocialLoginView(APIView):
    """
    Принимает provider (google-oauth2, github)
    и access_token, выданный соцсетью.
    Возвращает JWT.
    """

    def post(self, request):
        provider = request.data.get("provider")
        access_token = request.data.get("access_token")

        if not provider or not access_token:
            return Response(
                {"error": "provider и access_token обязательны"},
                status=status.HTTP_400_BAD_REQUEST
            )

        strategy = load_strategy(request)
        backend = load_backend(strategy, provider, redirect_uri=None)

        try:
            user = backend.do_auth(access_token)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if user and user.is_active:
            login(request, user)
            refresh = RefreshToken.for_user(user)

            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            })

        return Response({"error": "Authentication failed"}, status=status.HTTP_400_BAD_REQUEST)