from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from accounts.serializers import (
    CustomTokenObtainPairSerializer,
    LoginRequestSerializer,
    LoginResponseSerializer,
)


class LoginView(APIView):
    permission_classes = []

    @swagger_auto_schema(
        operation_summary='Obtain JWT access and refresh tokens',
        request_body=LoginRequestSerializer,
        responses={200: LoginResponseSerializer},
        security=[],
    )
    def post(self, request, *args, **kwargs):
        serializer = CustomTokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_data = serializer.validated_data
        return Response(
            {
                'refresh': token_data['refresh'],
                'access': token_data['access'],
            },
            status=status.HTTP_200_OK,
        )
