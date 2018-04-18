from __future__ import absolute_import
from django.utils import timezone
from webdna_server.celery import app
from WebDNA.models import *
import subprocess
import os


pdb_file_count = {}


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


@app.task()
def get_PDB_file(project_id):
    tasks_path = os.path.dirname(os.path.realpath(__file__))
    project_path = tasks_path + r'/../server-data/server-projects/' + project_id
    PDB_script_path = project_path + r'/../../../oxDNA/UTILS/traj2pdb.py'
    # python_script = 'python ' + PDB_script_path ## even needed? use python3?
    process = subprocess.Popen([PDB_script_path, 'trajectory.dat', 'generated.top'], cwd=project_path)

    if project_id in pdb_file_count:
        pdb_file_count[project_id] = pdb_file_count[project_id] + 1
    else:
        pdb_file_count[project_id] = 0

    process.wait()  # makes it blocking?
    os.rename(project_path + r'/trajectory.dat.pdb', project_path + r'/' + pdb_file_count[project_id] + r'trajectory.pdb')

    trajectory_string = ''
    trajectory_file = open(file=project_path + r'/' + pdb_file_count[project_id] + r'trajectory.pdb', mode='r')
    for line in trajectory_file.readlines():
        trajectory_string = trajectory_string + line # includes newline character
    return trajectory_string


@app.task
def test():
    print("Test task received from WebDNA server!")
