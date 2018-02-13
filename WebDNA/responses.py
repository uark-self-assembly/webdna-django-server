from rest_framework.response import Response
from rest_framework import status
from .util.jwt_util import *


class ErrorResponse:
    @staticmethod
    def make(http_status=400, message="error"):
        response = {
            'status': http_status,
            'message': message
        }

        return Response(data=response, status=http_status)


class ObjectResponse:
    @staticmethod
    def make(obj, http_status=200, message='success'):
        response = {
            'status': http_status,
            'message': message,
            'response': obj
        }

        return Response(data=response, status=http_status)


class AuthenticationResponse:
    @staticmethod
    def make(user, http_status=status.HTTP_200_OK, message='authenticated'):
        return ObjectResponse.make(
            obj={
                'user': user,
                'token': encode(user)
            },
            http_status=http_status,
            message=message
        )


class RegistrationResponse:
    @staticmethod
    def make(user):
        return AuthenticationResponse.make(
            user=user,
            http_status=status.HTTP_201_CREATED,
            message='registered'
        )
