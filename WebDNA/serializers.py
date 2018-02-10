from rest_framework import serializers
from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'created_on')


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=128)
    password = serializers.CharField(max_length=128)
