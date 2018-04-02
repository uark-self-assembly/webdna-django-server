from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import *
from django.contrib.auth.hashers import make_password, check_password
from .messages import *
import re
import random


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

        self.fetched_project = fetched[0]

        if self.fetched_project.job_running:
            raise serializers.ValidationError(JOB_ALREADY_EXECUTING)

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


def randint():
    return random.randint(0, 1000000000)


class ProjectSettingsSerializer(serializers.Serializer):
    # Generic Options
    interaction_type = serializers.CharField(max_length=10, default='DNA')
    sim_type = serializers.CharField(max_length=10, default='MD')
    backend = serializers.CharField(max_length=10)
    backend_precision = serializers.CharField(max_length=10)
    debug = serializers.IntegerField(default=0, read_only=True)

    # Simulation Options
    steps = serializers.IntegerField()
    restart_step_counter = serializers.IntegerField(default=0)
    seed = serializers.IntegerField(default=randint)
    T = serializers.CharField(max_length=20)
    fix_diffusion = serializers.IntegerField(default=1)
    verlet_skin = serializers.FloatField()
    back_in_box = serializers.IntegerField(default=0)
    salt_concentration = serializers.FloatField()  # only used with DNA2
    use_average_seq = serializers.IntegerField(default=1)
    seq_dep_file = serializers.CharField(max_length=128)
    external_forces = serializers.IntegerField(default=0, min_value=0, max_value=1) # if 1, must set external_forces_file
    external_forces_file = serializers.CharField(max_length=128)

    # Molecular Dynamics Simulations Options
    dt = serializers.FloatField()
    thermostat = serializers.CharField(max_length=10)
    newtonian_steps = serializers.IntegerField()  # required if thermostat != "no"
    pt = serializers.FloatField()  # only used if thermostat == "john"
    diff_coeff = serializers.FloatField()  # required if pt is not specified

    # NOT USING MONTE CARLO SIMULATION SETTINGS

    # Input/Output
    conf_file = serializers.CharField(max_length=128)
    topology = serializers.CharField(max_length=128)
    trajectory_file = serializers.CharField(max_length=128)
    confs_to_skip = serializers.IntegerField(default=0) # only used if conf_file is a trajectory
    lastconf_file = serializers.CharField(max_length=128, default='last_conf.dat')
    lastconf_file_bin = serializers.CharField(max_length=0)
    binary_initial_conf = serializers.IntegerField(default=0, min_value=0, max_value=1)
    refresh_vel = serializers.IntegerField(default=0, min_value=0, max_value=1)
    energy_file = serializers.CharField(max_length=128)
    print_energy_every = serializers.IntegerField(default=1000)
    no_stdout_energy = serializers.IntegerField(default=0, min_value=0, max_value=1)
    time_scale = serializers.CharField(default='linear', max_length=128)
    print_conf_ppc = serializers.IntegerField()
    print_conf_interval = serializers.IntegerField()
    print_reduced_conf_every = serializers.IntegerField(default=0)
