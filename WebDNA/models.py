from django.db import models
from django.utils import timezone
import uuid


# Create your models here.
class User(models.Model):
    class Meta:
        db_table = '"webdna"."user"'

    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=128, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    password = models.CharField(max_length=128)
    created_on = models.DateTimeField(editable=False, default=timezone.now)


class Project(models.Model):
    class Meta:
        db_table = '"webdna"."project"'

    id = models.UUIDField(primary_key=True, unique=True)
    user_id = models.UUIDField(unique=True)
    name = models.CharField(max_length=128)
    data_file = models.CharField(max_length=128)
    created_on = models.DateTimeField()
    job_running = models.BooleanField()


class Job(models.Model):
    class Meta:
        db_table = '"webdna"."job"'

    id = models.UUIDField(primary_key=True, unique=True)
    project_id = models.UUIDField()
    start_time = models.DateTimeField(editable=False)
    finish_time = models.DateTimeField(editable=False)
    process_name = models.CharField(max_length=128)
