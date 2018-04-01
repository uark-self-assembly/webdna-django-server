from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import *
from django.contrib.auth.hashers import make_password, check_password
from .messages import *
import re


class ExecutionSerializer(serializers.Serializer):
    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    class Meta:
        model = Project
        fields = 'id'

    id = serializers.CharField(max_length=36)
    fetched_project = None

    def validate(self, execution_data):
        proj_id = execution_data['id']

        query_set = Project.objects.all()
        fetched = query_set.filter(id=proj_id)
        if not fetched:
            raise serializers.ValidationError(PROJECT_NOT_FOUND)

        proj = fetched[0]
        self.fetched_project = proj

        return execution_data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'created_on')


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'


class LoginSerializer(serializers.Serializer):
    class Meta:
        model = User
        fields = ('username', 'password')

    username = serializers.CharField(max_length=128)
    password = serializers.CharField(max_length=128)

    fetched_user = None

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    def validate(self, login_data):
        username = login_data['username']
        password = login_data['password']

        query_set = User.objects.all()
        fetched = query_set.filter(username=username)
        if not fetched:
            raise serializers.ValidationError(USER_NOT_FOUND)

        user_object = fetched[0]
        if not check_password(password, user_object.password):
            raise serializers.ValidationError(INVALID_PASSWORD)

        self.fetched_user = user_object

        return login_data


class RegistrationSerializer(serializers.Serializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password')
        write_only_fields = 'password'

    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    password = serializers.CharField(max_length=128)

    def validate_password(self, password):
        flag = False
        if len(str(password)) < 8:
            flag = True
        elif re.search('[0-9]', str(password)) is None:
            flag = True
        elif re.search('[a-z]', str(password)) is None:
            flag = True
        elif re.search('[A-Z]', str(password)) is None:
            flag = True

        if flag:
            raise serializers.ValidationError(INVALID_PASSWORD_FORMAT)

        return password

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=make_password(validated_data['password'])
        )

        user.save()
        return user

    def update(self, instance, validated_data):
        pass


class CheckStatusSerializer(serializers.Serializer):
    class Meta:
        model = Job
        fields = ('project_id')

    project_id = serializers.UUIDField()

    def validate_project_id(self, project_id):
        query_set = Job.objects.get_queryset(project_id=project_id, finish_time__isnull=False)
        if not query_set.get():
            raise serializers.ValidationError(INVALID_BODY)
        return project_id
