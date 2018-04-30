from __future__ import absolute_import

import os
import subprocess
import shutil
import runpy
import sys
from zipfile import ZipFile
from WebDNA.models import *
from webdna_server.celery import app
from WebDNA.messages import *


@app.task()
def traj2pdb(path):
    process = subprocess.Popen(["traj2pdb.py", "trajectory.dat", "generated.top", "trajectory.pdb"],
                               cwd=os.path.join(os.getcwd(), path))
    process.wait()


@app.task()
def traj2xtc(path, input_path='trajectory.pdb', output_path='sim/trajectory.xtc'):
    print('gmx trjconv -f {} -o {}'.format(input_path, output_path))
    process = subprocess.Popen(["gmx", "trjconv", "-f", input_path, "-o", output_path],
                               cwd=os.path.join(os.getcwd(), path), stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    process.wait()


def pdb2first_frame(path, input_file='trajectory.pdb', output_file='trajectory_0.pdb'):
    input_path = os.path.join(path, input_file)
    output_path = os.path.join(path, output_file)

    outfile = open(output_path, 'w')

    with open(input_path) as infile:
        for line in infile:
            if 'ENDMDL' not in line:
                outfile.write(line)
            else:
                outfile.write('ENDMDL')
                break

    outfile.close()


def zip_simulation(path):
    if os.path.exists(os.path.join(path, 'trajectory.pdb')):
        if os.path.exists(os.path.join(path, 'trajectory.xtc')):
            with ZipFile(os.path.join(path, 'simulation.zip'), 'w') as archive:
                archive.write(os.path.join(path, 'trajectory.pdb'), 'trajectory.pdb')
                archive.write(os.path.join(path, 'trajectory.xtc'), 'trajectory.xtc')


@app.task()
def generate_dat_top(project_id, box_size):
    path = os.path.join('server-data', 'server-projects', str(project_id))
    sequence_path = os.path.join(path, "sequence.txt")

    if not os.path.isfile(sequence_path):
        return MISSING_PROJECT_FILES

    process = subprocess.Popen(["generate-sa.py", str(box_size), "sequence.txt"], cwd=os.path.join(os.getcwd(), path))
    process.wait()
    return GENERATED_FILES


@app.task()
def execute_sim(job_id, project_id, user_id, path):
    job = Job(id=job_id, process_name=execute_sim.request.id, finish_time=None)
    job.save(update_fields=['process_name', 'finish_time'])

    try:
        os.remove(os.path.join(path, "trajectory.xtc"))
        os.remove(os.path.join(path, "trajectory.pdb"))
        os.remove(os.path.join(path, project_id + ".zip"))
    except OSError:
        pass

    print("Received new execution for project: " + project_id)
    log_file = os.path.join(path, 'stdout.log')
    log = open(file=log_file, mode='w')
    cwd = os.path.join(os.getcwd(), path)

    process = subprocess.Popen(["oxDNA", "input.txt"], cwd=cwd, stdout=log)

    process.wait()
    log.close()

    print("Simulation completed, generating pdb file for project: " + project_id)
    generate_sim_files(path)

    print("Running analysis scripts for project: " + project_id)
    execute_output_analysis(project_id, user_id, path)

    job = Job(id=job_id, finish_time=timezone.now(), process_name=None)
    job.save(update_fields=['process_name', 'finish_time'])


def generate_sim_files(path):
    print('In generate_sim_files: ' + path)
    traj2pdb(path)

    sim_output_path = os.path.join(path, 'sim')

    try:
        os.makedirs(sim_output_path)
    except FileExistsError:
        pass

    pdb_file_path = os.path.join(sim_output_path, 'trajectory.pdb')
    xtc_file_path = os.path.join(sim_output_path, 'trajectory.xtc')

    try:
        os.remove(pdb_file_path)
        os.remove(xtc_file_path)
    except OSError:
        pass

    traj2xtc(path, input_path='trajectory.pdb', output_path=os.path.join('sim', 'trajectory.xtc'))
    pdb2first_frame(path, input_file='trajectory.pdb', output_file=os.path.join('sim', 'trajectory.pdb'))

    zip_simulation(sim_output_path)


def execute_output_analysis(project_id, user_id, path):

    with open(os.path.join(path, 'scriptchain.txt'), mode='r') as scriptchain:
        script_string = scriptchain.readline()

    if len(script_string) == 0:
        return

    scripts = [x.strip() for x in script_string.split(',')]

    for script in scripts:
        shutil.copy2(os.path.join('server-data', 'server-users', str(user_id), 'scripts', script),
                     os.path.join(path, 'analysis'))

    file_globals = {}
    stdout = sys.stdout
    sys.stdout = open(os.path.join(path, 'analysis', 'analysis.log'), 'w')
    try:
        for script in scripts:
            file_globals = runpy.run_path(os.path.join(path, 'analysis', script), init_globals=file_globals)
    except Exception as e:
        print("Error caught in user script: " + str(e))
    sys.stdout.close()
    sys.stdout = stdout

    print('Analysis scripts finished for project: ' + str(project_id))


