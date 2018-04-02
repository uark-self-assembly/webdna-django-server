from __future__ import absolute_import
from webdna_server.celery import app
from WebDNA.models import *
import subprocess
import os

dictionaries = {}

@app.task()
def execute_sim(proj_id, path):
    print("Received new execution for project: " + proj_id)
    log = open(file=path + "/" + "stdout.log", mode='w')
    p = subprocess.Popen(["oxDNA", "input.txt"], cwd=os.getcwd() + "/" + path, stdout=log)

    dictionaries[proj_id] = execute_sim.request.id

    p.wait()
    log.close()
    p = Project(id=proj_id, job_running=False)
    p.save(update_fields=['job_running'])


@app.task
def test():
    print("Test task received from WebDNA server!")
