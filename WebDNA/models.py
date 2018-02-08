from django.db import models

# Create your models here.
class User(models.Model):
    class Meta:
        db_table = '"webdna"."user"'

    id = models.UUIDField(primary_key=True, unique=True)
    username = models.CharField(max_length=128, unique=True)
    email = models.CharField(max_length=128, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    password = models.CharField(max_length=128)
    created_on = models.DateTimeField()


class Project(models.Model):
    class Meta:
        db_table = '"webdna"."project"'

    id = models.UUIDField(primary_key=True, unique=True)
    user_id = models.UUIDField(primary_key=True, unique=True)
    name = models.CharField(max_length=128)
    data_file = models.CharField(max_length=128)
    created_on = models.DateTimeField()
    job_running = models.BooleanField()
