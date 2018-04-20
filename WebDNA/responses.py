from rest_framework.response import Response
from rest_framework import status as http_status
from .util.jwt_util import *


class ErrorResponse:
    @staticmethod
    def make(status=http_status.HTTP_400_BAD_REQUEST, message='error', errors=None):
        data = {
            'status': status,
            'message': message,
            'response': errors
        }

        return Response(data=data, status=status)


class DefaultResponse:
    @staticmethod
    def make(status=http_status.HTTP_200_OK, message='success'):
        data = {
            'status': status,
            'message': message,
            'response': None
        }

        return Response(data=data, status=status)


class ObjectResponse:
    @staticmethod
    def make(obj=None, status=http_status.HTTP_200_OK, message='success', response=None):
        if response:
            data = {
                'status': response.status_code,
                'message': 'error' if (response.status_code >= 300) else 'success',
                'response': response.data
            }
        else:
            data = {
                'status': status,
                'message': message,
                'response': obj
            }

        return Response(data=data, status=status)


class AuthenticationResponse:
    @staticmethod
    def make(user, status=http_status.HTTP_200_OK, message='authenticated'):
        return ObjectResponse.make(
            obj={
                'user': user,
                'token': encode(user)
            },
            status=status,
            message=message
        )


class RegistrationResponse:
    @staticmethod
    def make(user):
        return AuthenticationResponse.make(
            user=user,
            status=http_status.HTTP_201_CREATED,
            message='registered'
        )


class ExecutionResponse:
    @staticmethod
    def make():
        return ObjectResponse.make(status=http_status.HTTP_202_ACCEPTED, message='Executing simulation...')
