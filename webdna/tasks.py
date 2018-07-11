from __future__ import absolute_import

import os
import subprocess
import shutil
import runpy
import sys
from webdna.models import *
from webdna_django_server.celery import app
import webdna.messages as messages
import webdna.util.oxdna as oxdna
import webdna.util.server as server
import webdna.util.project as project_util
import webdna.util.file as file_util
from webdna.defaults import ProjectFile, AnalysisFile


@app.task()
def generate_initial_configuration(project_id, generation, log_file_path):
    project_folder_path = server.get_project_folder_path(project_id)

    if generation['method'] == 'generate-sa':
        if not server.project_file_exists(project_id, ProjectFile.SEQUENCE):
            return messages.MISSING_PROJECT_FILES

        if not oxdna.generate_sa(project_folder_path, generation, log_file_path):
            return messages.INTERNAL_ERROR
        else:
            return messages.GENERATED_FILES
    elif generation['method'] == 'generate-folded':
        if not server.project_file_exists(project_id, ProjectFile.SEQUENCE):
            return messages.MISSING_PROJECT_FILES

        if not oxdna.generate_folded(project_folder_path, generation, log_file_path):
            return messages.INTERNAL_ERROR
        else:
            return messages.GENERATED_FILES
    elif generation['method'] == 'cadnano-interface':
        if not server.project_file_exists(project_id, ProjectFile.CADNANO):
            return messages.MISSING_PROJECT_FILES

        if not oxdna.generate_cadnano_interface(project_folder_path, generation, log_file_path):
            return messages.INTERNAL_ERROR
        else:
            return messages.GENERATED_FILES
    else:
        return messages.INTERNAL_ERROR


@app.task()
def execute_sim(job_id, project_id, user_id, should_regenerate, generation, fresh_execution=True):
    job = Job(
        id=job_id, process_name=execute_sim.request.id, start_time=timezone.now(), finish_time=None, terminated=False)
    job.save(update_fields=['process_name', 'start_time', 'finish_time', 'terminated'])

    # Clean the previous execution files
    if should_regenerate or fresh_execution:
        server.clean_project(project_id)

    project_folder_path = server.get_project_folder_path(project_id)
    stdout_file_path = server.get_project_file(project_id, ProjectFile.STDOUT)

    if should_regenerate:
        print("Regenerating topology for project: " + project_id)
        input_data = file_util.parse_input_file(project_id)
        box_size = input_data['box_size']
        generate_initial_configuration(project_id, generation, stdout_file_path)

    print("Received new execution for project: " + project_id)

    stdout_log_file = open(file=stdout_file_path, mode='w')

    process = subprocess.Popen(['oxDNA', 'input.txt'], cwd=project_folder_path, stdout=stdout_log_file)
    process.wait()

    stdout_log_file.close()

    print("Simulation completed, generating pdb file for project: " + project_id)

    if not project_util.generate_sim_files(project_id):
        print('Unable to convert simulation to visualizer output.')

    execute_output_analysis(project_id, user_id)

    job = Job(id=job_id, finish_time=timezone.now(), process_name=None)
    job.save(update_fields=['process_name', 'finish_time'])


@app.task()
def execute_output_analysis(project_id, user_id):
    script_chain_file_path = server.get_project_file(project_id, ProjectFile.SCRIPT_CHAIN)
    if not os.path.isfile(script_chain_file_path):
        return

    print("Running analysis scripts for project: " + project_id)

    with open(script_chain_file_path, mode='r') as script_chain:
        script_string = script_chain.readline()

    if len(script_string) == 0:
        return

    scripts = [x.strip() for x in script_string.split(',')]

    analysis_folder_path = server.get_analysis_folder_path(project_id)

    for script in scripts:
        script_file_path = server.get_user_script(user_id, script)
        shutil.copy2(script_file_path, analysis_folder_path)

    analysis_log_file_path = server.get_analysis_file_path(project_id, AnalysisFile.LOG)

    file_globals = {}
    stdout = sys.stdout
    sys.stdout = open(analysis_log_file_path, 'w')

    try:
        # Execute the scripts in order
        for script in scripts:
            script_file_path = server.get_analysis_script_file_path(project_id, script)
            file_globals = runpy.run_path(script_file_path, init_globals=file_globals)
    except Exception as e:
        print("Error caught in user script: " + str(e))

    sys.stdout.close()
    sys.stdout = stdout

    print('Analysis scripts finished for project: ' + str(project_id))
