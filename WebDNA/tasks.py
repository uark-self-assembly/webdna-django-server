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
def traj2xtc(input_path='trajectory.pdb', output_path='sim/trajectory.xtc'):
    print('gmx trjconv -f {} -o {}'.format(input_path, output_path))
    process = subprocess.Popen(["gmx", "trjconv", "-f", input_path, "-o", output_path],
                               cwd=os.getcwd(), stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    process.wait()


def pdb2first_frame(input_file='trajectory.pdb', output_file='trajectory_0.pdb'):

    outfile = open(output_file, 'w')

    with open(input_file) as infile:
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


def zip_project(project_path):
    zip_path = os.path.join(project_path, 'project.zip')
    if os.path.isdir(project_path):
        if os.path.exists(zip_path):
            os.remove(zip_path)
        with ZipFile(os.path.join(project_path, 'project.zip'), 'w') as archive:
            for (dir_path, dir_names, file_names) in os.walk(project_path):
                file_names_len = len(file_names)
                for i in range(0, file_names_len):
                    archive.write(os.path.join(dir_path, file_names[i]), file_names[i])


@app.task()
def generate_dat_top(project_id, box_size):
    path = os.path.join('server-data', 'server-projects', str(project_id))
    sequence_path = os.path.join(path, "sequence.txt")

    if not os.path.isfile(sequence_path):
        return MISSING_PROJECT_FILES

    process = subprocess.Popen(["generate-sa.py", str(box_size), "sequence.txt"], cwd=os.path.join(os.getcwd(), path))
    process.wait()
    return GENERATED_FILES


def clean_files(path):
    files = ['trajectory.pdb', 'trajectory.dat', 'last_conf.dat', os.path.join('analysis', 'output.txt')]

    for file in files:
        file_path = os.path.join(path, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
        else:
            continue


@app.task()
def execute_sim(job_id, project_id, user_id, path):
    job = Job(id=job_id, process_name=execute_sim.request.id, finish_time=None)
    job.save(update_fields=['process_name', 'finish_time'])

    clean_files(path)

    print("Received new execution for project: " + project_id)
    log_file = os.path.join(path, 'stdout.log')
    log = open(file=log_file, mode='w')
    cwd = os.path.join(os.getcwd(), path)

    process = subprocess.Popen(["oxDNA", "input.txt"], cwd=cwd, stdout=log)

    process.wait()
    log.close()

    print("Simulation completed, generating pdb file for project: " + project_id)
    generate_sim_files(path, project_id)

    execute_output_analysis(project_id, user_id, path)

    job = Job(id=job_id, finish_time=timezone.now(), process_name=None)
    job.save(update_fields=['process_name', 'finish_time'])


def generate_sim_files(path, project_id):
    print('In generate_sim_files: ' + path)
    traj2pdb(path)

    sim_output_path = os.path.join('server-data', 'server-sims')

    try:
        os.makedirs(sim_output_path)
    except FileExistsError:
        pass

    pdb_file_path = os.path.join(sim_output_path, project_id + '.pdb')
    xtc_file_path = os.path.join(sim_output_path, project_id + '.xtc')

    original_pdb_path = os.path.join(path, 'trajectory.pdb')

    try:
        os.remove(pdb_file_path)
        os.remove(xtc_file_path)
    except OSError:
        pass

    traj2xtc(input_path=original_pdb_path, output_path=xtc_file_path)
    pdb2first_frame(input_file=original_pdb_path, output_file=pdb_file_path)


@app.task()
def execute_output_analysis(project_id, user_id, path):
    if not os.path.isfile(os.path.join(path, 'scriptchain.txt')):
        return

    print("Running analysis scripts for project: " + project_id)

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


