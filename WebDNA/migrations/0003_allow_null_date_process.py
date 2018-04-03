# Generated by Django 2.0.2 on 2018-04-03 04:03

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('WebDNA', '0002_add_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='finish_time',
            field=models.DateTimeField(default=None, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='process_name',
            field=models.CharField(default=None, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='start_time',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
    ]