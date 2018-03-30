# Generated by Django 2.0.3 on 2018-03-30 01:50

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, unique=True)),
                ('start_time', models.DateTimeField(editable=False)),
                ('finish_time', models.DateTimeField(editable=False)),
                ('process_name', models.CharField(max_length=128)),
            ],
            options={
                'db_table': '"webdna"."job"',
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=128)),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now)),
                ('job_running', models.BooleanField(default=False)),
            ],
            options={
                'db_table': '"webdna"."project"',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('username', models.CharField(max_length=128, unique=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('first_name', models.CharField(max_length=30)),
                ('last_name', models.CharField(max_length=30)),
                ('password', models.CharField(max_length=128)),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
            ],
            options={
                'db_table': '"webdna"."user"',
            },
        ),
        migrations.AddField(
            model_name='project',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='WebDNA.User'),
        ),
        migrations.AddField(
            model_name='job',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='WebDNA.Project'),
        ),
    ]
