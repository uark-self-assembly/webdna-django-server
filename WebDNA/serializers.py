from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import *
from django.contrib.auth.hashers import make_password, check_password
from .messages import *
import re
import random
import os


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


class ScriptUploadSerializer(serializers.Serializer):
    class Meta:
        model = Script
        fields = ('file_name', 'user')

        file_name = serializers.CharField(max_length=128)
        user = serializers.CharField(max_length=36)
        file_obj = serializers.FileField()

        def create(self, validated_data):
            script = Script.objects.create(file_name=validated_data['file_name'], user=validated_data['user'])
            script.save()
            return script

        def update(self, instance, validated_data):
            pass

        def validate(self, script_data):
            file_name = script_data['file_name']
            user = script_data['user']
            file_obj = script_data['file']

            # make sure it doesn't already exist
            query_set = Script.objects.all()
            fetched = query_set.filter(file_name=file_name, user=user)
            if fetched:
                raise serializers.ValidationError(SCRIPTS_ALREADY_EXISTS)

            # make the directory
            path = os.path.join(os.getcwd(), 'server-data', 'server-users', str(user), 'scripts')
            if not os.path.isdir(path):
                os.makedirs(path)

            return script_data

class FileSerializer(ExecutionSerializer):
    file_name = serializers.CharField(max_length=128)

    def validate(self, execution_data):
        try:
            valid_job_proj = super().validate(self, execution_data)
        except serializers.ValidationError as error:
            raise error

        project_id = valid_job_proj['project_id']
        file_name = valid_job_proj['file_name']
        file_path = os.path.join('server-data', 'server-projects', str(project_id), str(file_name))
        if not os.path.isfile(file_path):
            raise serializers.ValidationError(MISSING_PROJECT_FILES)

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


class UserScriptSerializer(serializers.Serializer):
    class Meta:
        model = User
        fields = 'id'

    user_id = serializers.CharField(max_length=36)

    def validate(self, user_data):
        user_id = user_data['user_id']

        query_set = User.objects.all()
        fetched = query_set.filter(id=user_id)

        if not fetched:
            raise serializers.ValidationError(USER_NOT_FOUND)

        path = os.path.join('server-data', 'server-users', str(user_id), 'scripts')
        if not os.path.isdir(path):
            raise serializers.ValidationError(SCRIPTS_NOT_FOUND)

        return user_data


class ProjectExistenceSerializer(serializers.Serializer):
    class Meta:
        model = Project
        fields = 'id'

    project_id = serializers.CharField(max_length=36)

    def validate(self, project_data):
        project_id = project_data['project_id']

        query_set = Project.objects.all()
        fetched = query_set.filter(id=project_id)

        if not fetched:
            raise serializers.ValidationError(PROJECT_NOT_FOUND)

        return project_data


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

        project_path = os.path.join('server-data', 'server-projects', str(project_id))

        # If sequence dependence is to be used, set this to 0 and specify seq_dep_file.
        use_average_seq = project_settings_data['use_average_seq']
        seq_dep_file = project_settings_data['seq_dep_file']
        seq_dep_file_path = os.path.join(project_path, str(seq_dep_file))
        if (int(use_average_seq) == 0 and not seq_dep_file) or not os.path.isfile(seq_dep_file_path):
            raise serializers.ValidationError(INPUT_SETTINGS_INVALID)

        # if 1, must set external_forces_file
        external_forces = project_settings_data['external_forces']
        external_forces_file = project_settings_data['external_forces_file']
        external_forces_file_path = os.path.join(project_path, str(external_forces_file))
        if (int(external_forces) == 1 and not external_forces_file) or not os.path.isfile(external_forces_file_path):
            raise serializers.ValidationError(INPUT_SETTINGS_INVALID)

        # if print_red_conf_every > 0
        print_reduced_conf_every = project_settings_data['print_reduced_conf_every']
        if int(print_reduced_conf_every) > 0:
            conf_path = os.path.join(os.getcwd(), project_path, 'reduced_conf_output_dir')
            project_settings_data['reduced_conf_output_dir'] = conf_path

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
    use_average_seq = serializers.IntegerField(default=1, min_value=0, max_value=1)  # If sequence dependence is to be used, set this to 0 and specify seq_dep_file.
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
