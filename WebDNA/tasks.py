from __future__ import absolute_import

import os
import subprocess

from WebDNA.models import *
from webdna_server.celery import app

pdb_file_count = {}


def traj2pdb(job_id, path):
    process = subprocess.Popen(["traj2pdb.py", "trajectory.dat", "generated.top", "trajectory.pdb"],
                         cwd=os.path.join(os.getcwd(), path))
    process.wait()


@app.task()
def execute_sim(job_id, project_id, path):
    job = Job(id=job_id, process_name=execute_sim.request.id, finish_time=None)
    job.save(update_fields=['process_name', 'finish_time'])

    try:
        os.remove(os.path.join(path, "trajectory.pdb"))
    except OSError:
        pass

    print("Received new execution for project: " + project_id)
    log_file = os.path.join(path, 'stdout.log')
    log = open(file=log_file, mode='w')
    cwd = os.path.join(os.getcwd(), 'path')

    process = subprocess.Popen(["oxDNA", "input.txt"], cwd=cwd, stdout=log)

    process.wait()
    log.close()

    job = Job(id=job_id, finish_time=timezone.now(), process_name=None)
    job.save(update_fields=['process_name', 'finish_time'])

    print("Simulation completed, generating pdb file for project: " + project_id)
    traj2pdb(job_id, path)


@app.task()
def get_pdb_file(project_id):
    tasks_path = os.path.dirname(os.path.realpath(__file__))
    project_path = tasks_path + r'/../server-data/server-projects/' + project_id
    pdb_script_path = project_path + r'/../../../oxDNA/UTILS/traj2pdb.py'
    # python_script = 'python ' + PDB_script_path ## even needed? use python3?
    process = subprocess.Popen([pdb_script_path, 'trajectory.dat', 'generated.top'], cwd=project_path)

    if project_id in pdb_file_count:
        pdb_file_count[project_id] = pdb_file_count[project_id] + 1
    else:
        pdb_file_count[project_id] = 0

    process.wait()  # makes it blocking?
    os.rename(project_path + r'/trajectory.dat.pdb', project_path + r'/' + pdb_file_count[project_id]
              + r'trajectory.pdb')

    trajectory_string = ''
    trajectory_file = open(file=project_path + r'/' + pdb_file_count[project_id] + r'trajectory.pdb', mode='r')
    for line in trajectory_file.readlines():
        trajectory_string = trajectory_string + line  # includes newline character
    return trajectory_string
