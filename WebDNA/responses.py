from rest_framework.response import Response
from .util.jwt_util import *


class ErrorResponse:
    @staticmethod
    def make(status=400, message="error"):
        response = {
            'status': status,
            'message': message
        }

        return Response(data=response)


class ObjectResponse:
    @staticmethod
    def make(obj, status=200, message="success"):
        response = {
            'status': status,
            'message': message,
            'response': obj
        }

        return Response(data=response)


class AuthenticationResponse:
    @staticmethod
    def make(user):
        response = {
            'status': 200,
            'message': 'authenticated',
            'response': {
                'user': user,
                'token': encode(user)
            }
        }

        return Response(data=response)