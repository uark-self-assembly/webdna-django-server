from __future__ import absolute_import
from django.utils import timezone
from webdna_server.celery import app
from WebDNA.models import *
import subprocess
import os


@app.task()
def execute_sim(job_id, proj_id, path):
    j = Job(id=job_id, process_name=execute_sim.request.id)
    j.save(update_fields=['process_name'])
    print("Received new execution for project: " + proj_id)
    log = open(file=path + "/" + "stdout.log", mode='w')
    p = subprocess.Popen(["oxDNA", "input.txt"], cwd=os.getcwd() + "/" + path, stdout=log)
    p.wait()
    log.close()
    j = Job(id=job_id, finish_time=timezone.now(), process_name=None)
    j.save(update_fields=['process_name', 'finish_time'])


@app.task
def test():
    print("Test task received from WebDNA server!")
