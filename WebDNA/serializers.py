from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import *
from django.contrib.auth.hashers import make_password
import re


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


class RegistrationSerializer(serializers.Serializer):
    class Meta:
        model = UserRegistration
        fields = ('username', 'email', 'first_name', 'last_name', 'password')
        write_only_fields = 'password'

    username = serializers.CharField(
        validators=[UniqueValidator(queryset=UserRegistration.objects.all())]
    )
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=UserRegistration.objects.all())]
    )
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    password = serializers.CharField(max_length=128)

    def validate_password(self, password):
        pattern = re.compile("^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$")
        if not pattern.match(password):
            raise serializers.ValidationError("password must be at least 8 characters, "
                                              "and have at least one uppercase, lowercase, and numeral character")

        return password

    def create(self, validated_data):
        user = UserRegistration.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=make_password(validated_data['password'])
        )

        user.save()
        return user
