from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import *
from django.contrib.auth.hashers import make_password, check_password
from .messages import *
import re
import random


class ExecutionSerializer(serializers.Serializer):
    class Meta:
        model = Job
        fields = 'project_id'

    project_id = serializers.CharField(max_length=36)
    fetched_job = None

    def create(self, validated_data):
        job = Job.objects.create(project_id=validated_data['project_id'])
        job.save()
        return job

    def update(self, instance, validated_data):
        pass

    def validate(self, execution_data):
        project_id = execution_data['project_id']

        query_set = Project.objects.all()
        fetched = query_set.filter(id=project_id)
        if not fetched:
            raise serializers.ValidationError(PROJECT_NOT_FOUND)

        query_set = Job.objects.all()
        fetched = query_set.filter(project_id=project_id)
        if not fetched:
            return execution_data
        else:
            self.fetched_job = fetched[0]
            if self.fetched_job.finish_time is None:
                raise serializers.ValidationError(JOB_ALREADY_EXECUTING)
            else:
                return execution_data


class VisualizationSerializer(ExecutionSerializer):
    def validate(self, execution_data):
        project_id = execution_data['project_id']

        query_set = Job.objects.all()
        fetched = query_set.filter(project_id=project_id)
        if not fetched:
            raise serializers.ValidationError(JOB_NOT_FOUND)
        else:
            self.fetched_job = fetched[0]
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
        fields = 'project_id'

    project_id = serializers.UUIDField()
    fetched_job = None

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def validate(self, data):
        project_id = data['project_id']
        query_set = Job.objects.all()
        fetched = query_set.filter(project_id=project_id)

        if not fetched:
            raise(serializers.ValidationError(JOB_NOT_FOUND))

        self.fetched_job = fetched[0]

        return data


def randint():
    return random.randint(0, 1000000000)


class ProjectSettingsSerializer(serializers.Serializer):

    def validate(self, project_settings_data):
        project_id = project_settings_data['project_id']

        query_set = Project.objects.all()
        fetched = query_set.filter(id=project_id)
        if not fetched:
            raise serializers.ValidationError(PROJECT_NOT_FOUND)

        return project_settings_data

    project_id = serializers.UUIDField()

    # Generation options
    box_size = serializers.IntegerField(min_value=1, default=20)  # box side

    # Generic Options
    interaction_type = serializers.CharField(max_length=10, default='DNA')
    sim_type = serializers.CharField(max_length=10, default='MD')
    backend = serializers.CharField(max_length=10, default='CPU')
    backend_precision = serializers.CharField(max_length=10)
    debug = serializers.IntegerField(default=0, read_only=True, min_value=0, max_value=1)

    # Simulation Options
    steps = serializers.IntegerField()
    restart_step_counter = serializers.IntegerField(default=0, min_value=0, max_value=1)
    seed = serializers.IntegerField(default=randint)
    T = serializers.CharField(max_length=20)
    fix_diffusion = serializers.IntegerField(default=1, min_value=0, max_value=1)
    verlet_skin = serializers.FloatField()
    back_in_box = serializers.IntegerField(default=0, min_value=0, max_value=1)
    salt_concentration = serializers.FloatField(required=False)  # only used with DNA2
    use_average_seq = serializers.IntegerField(default=1, min_value=0, max_value=1)
    seq_dep_file = serializers.CharField(max_length=128, required=False)
    external_forces = serializers.IntegerField(default=0, min_value=0, max_value=1)  # if 1, must set external_forces_file
    external_forces_file = serializers.CharField(max_length=128, required=False)

    # Molecular Dynamics Simulations Options
    dt = serializers.FloatField(required=True)
    thermostat = serializers.CharField(max_length=10)
    newtonian_steps = serializers.IntegerField()  # required if thermostat != "no"
    pt = serializers.FloatField(required=False)  # only used if thermostat == "john"
    diff_coeff = serializers.FloatField(required=True)  # required if pt is not specified

    # NOT USING MONTE CARLO SIMULATION SETTINGS

    # Input/Output
    conf_file = serializers.CharField(max_length=128, required=False, default='generated.dat')
    topology = serializers.CharField(max_length=128, default='generated.top')
    trajectory_file = serializers.CharField(default='trajectory.dat', max_length=128)
    confs_to_skip = serializers.IntegerField(default=0)  # only used if conf_file is a trajectory
    lastconf_file = serializers.CharField(max_length=128, default='last_conf.dat')
    lastconf_file_bin = serializers.CharField(max_length=0, required=False)
    binary_initial_conf = serializers.IntegerField(default=0, min_value=0, max_value=1)
    refresh_vel = serializers.IntegerField(default=0, min_value=0, max_value=1)
    energy_file = serializers.CharField(default='energy.dat', max_length=128)
    print_energy_every = serializers.IntegerField(default=1000)
    no_stdout_energy = serializers.IntegerField(default=0, min_value=0, max_value=1)
    time_scale = serializers.CharField(default='linear', max_length=128)
    print_conf_ppc = serializers.IntegerField(required=False)  # mandatory only if time_scale==log_line
    print_conf_interval = serializers.IntegerField(required=False)
    print_reduced_conf_every = serializers.IntegerField(default=0, min_value=0)
    reduced_conf_output_dir = serializers.CharField(max_length=128, required=False)  # if print_red_conf_every > 0
    log_file = serializers.CharField(default='log.dat', max_length=128)
    print_timings = serializers.IntegerField(default=0, min_value=0, max_value=1)
    timings_filename = serializers.CharField(max_length=128, required=False)
    output_prefix = serializers.CharField(default='', max_length=128)
    print_input = serializers.IntegerField(default=0, min_value=0, max_value=1)
    equilibration_steps = serializers.IntegerField(default=0, min_value=0)


class GetPDBSerializer(serializers.Serializer):
    class Meta:
        model = Job
        fields = 'project_id'

    project_id = serializers.UUIDField()
    fetched_job = None

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def validate(self, data):
        project_id = data['project_id']
        query_set = Job.objects.all()
        fetched = query_set.filter(project_id=project_id)

        if not fetched:
            raise(serializers.ValidationError(JOB_NOT_FOUND))

        self.fetched_job = fetched[0]

        return data
