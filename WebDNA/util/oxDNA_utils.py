import os
import subprocess
from WebDNA.responses import *

################################
# These utilities assumes WebDNA/data/community_scripts, WebDNA/data/user_projects and WebDNA/oxDNA
# sequence.txt not associated with options, but Box Sides is
# options will also have default options (i.e. "topology" : ['topology', 'generated.top'])
# options = {
#               "Box Sides" : ['box sides', 'formatted input'],
#               "sim_type" : ['sim_type', 'MD'],
#               "backend" : ['backend', 'CPU'],
#               "steps" : ['steps', '1e6'],
#               "newtonian_steps" : ['newtonian_steps', '103'],
#               .
#               .
#               .
# }
# sequence = [
#               ["AAGT", 4],
#               ["TTTT", 3],
#               ["CGAA", 2],
#               .
#               .
#               .
# ]

# SAMPLE FILE SYSTEM (this file assumes linux machine)
# /community_scripts
# |  /scriptName_"UUID1"
# |  |  scriptName.py
# |  |  README.txt
# |  /scriptName_"UUID2"
#
# /user_projects
# |  /user_"UUID1"
# |  |  /user_scripts
# |  |  |  /scriptName_"UUID1"
# |  |  |  |  scriptName.py
# |  |  |  |  README.txt
# |  |  |  /scriptName_"UUID2"
# |  |  /project_"UUID1"
# |  |  |  /input
# |  |  |  |  input.txt
# |  |  |  |  others.txt
# |  |  |  /output
# |  |  |  |  others.JSON
# |  |  |  |  others.others
# |  |  /project_"UUID2"
# |  /user_"UUID2"
################################


def ensure_path(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path


# assumes current working directory hasn't been changed (os.chdir() not used)
def ensure_user_path(user_UUID):
    user_path = os.path.dirname(os.path.realpath(__file__)) + r'/../data/user_projects/' + user_UUID
    return ensure_path(user_path)


def ensure_user_script_path(user_UUID, script_UUID):
    user_path = ensure_user_path(user_UUID)
    user_scripts_path = user_path + r'/user_scripts'
    ensure_path(user_scripts_path)
    script_path = user_scripts_path + r'/' + script_UUID
    return ensure_path(script_path)


def ensure_community_script_path(script_UUID):
    community_scripts_path = os.path.dirname(os.path.realpath(__file__)) + r'/../data/community_scripts'
    community_script_path = ensure_path(community_scripts_path) + r'/' + script_UUID
    return ensure_path(community_script_path)


def ensure_project_path(user_UUID, project_UUID):
    user_path = ensure_user_path(user_UUID)
    project_path = user_path + r'/' + project_UUID
    input_path = project_path + r'/input'
    output_path = project_path + r'/output'
    ensure_path(input_path)
    ensure_path(output_path)
    return project_path


def ensure_file_does_not_exist(file_path):
    try:
        os.remove(file_path)
    except OSError:
        pass


def generate_input(options, user_UUID, project_UUID):
    project_path = ensure_project_path(user_UUID, project_UUID)
    sequence_file_path = project_path + r'/input/sequence.txt'
    existing_generated_dat_file_path = project_path + r'/input/generated.dat'
    existing_generated_top_file_path = project_path + r'/input/generated.top'
    input_file_path = project_path + r'/input/input.txt'

    if not os.path.exists(sequence_file_path):
        return "Error. Must generate sequence.txt first"
        # raise error
    ensure_file_does_not_exist(existing_generated_dat_file_path)
    ensure_file_does_not_exist(existing_generated_top_file_path)
    ensure_file_does_not_exist(input_file_path)

    # generate-sa.py, generate-RNA.py, generate.py? depending on options?
    # with box sides i.e. 'python generate-sa.py 9 sequence.txt'
    original_working_directory = os.getcwd()
    current_file_directory = os.path.dirname(os.path.realpath(__file__))
    project_input_directory = current_file_directory + r'/../data/user_projects/' + user_UUID + r'/' + project_UUID + r'/input'
    os.chdir(project_input_directory)
    bash_command = 'python ../../../../../oxDNA/UTILS/generate-sa.py ' + options["Box Sides"][1] + ' sequence.txt'
    subprocess.call(bash_command, shell=True)

    # create input file based on options dictionary
    input_file = open(input_file_path, 'w')
    for value in options.itervalues():
        input_file.write(value[0] + ' = ' + value[1] + '\n')
    input_file.close()

    # go back to original working directory
    os.chdir(original_working_directory)


# return string of sequence?
# currently only accepts array input
def generate_sequence(sequence_input, user_UUID, project_UUID):
    # sequence_input should check for just whole file or array
    project_path = ensure_project_path(user_UUID, project_UUID)
    sequence_file_path = project_path + r'/input/sequence.txt'
    ensure_file_does_not_exist(sequence_file_path)

    # write to sequence.txt as if sequence_input = [["AAT", 9], ["TTG", 4], ["CGT", 3]]
    sequence_file = open(sequence_file_path, 'w')
    for i in range(len(sequence_input)):
        for j in range(len(sequence_input[i][1])):
            sequence_file.write(sequence_input[i][0] + '\n')
    sequence_file.close()


# return shell output? return output files as files or strings?
def run_oxDNA(user_UUID, project_UUID):
    original_working_directory = os.getcwd()
    current_file_directory = os.path.dirname(os.path.realpath(__file__))
    project_input_directory = current_file_directory + r'/../data/user_projects/' + user_UUID + r'/' + project_UUID + r'/input'
    energy_output_path = project_input_directory + r'/../output/energy.dat'
    last_conf_output_path = project_input_directory + r'/../output/last_conf.dat'
    log_output_path = project_input_directory + r'/../output/log.dat'
    trajectory_output_path = project_input_directory + r'/../output/trajectory.dat'
    # change working directory so that output files will land somewhere appropriate
    os.chdir(project_input_directory)

    if not os.path.exists(project_input_directory + r'/input.txt'):  # or only input without .txt?
        os.chdir(original_working_directory)
        return "Error. Input file missing"
        # raise error
    # make sure no copies are made with each execution
    ensure_file_does_not_exist(energy_output_path)
    ensure_file_does_not_exist(last_conf_output_path)
    ensure_file_does_not_exist(log_output_path)
    ensure_file_does_not_exist(trajectory_output_path)

    subprocess.call('../../../../../oxDNA/build/bin/oxDNA input.txt', shell=True)
    # are these the only possible output files?
    os.rename(project_input_directory + r'/energy.dat', energy_output_path)
    os.rename(project_input_directory + r'/last_conf.dat', last_conf_output_path)
    os.rename(project_input_directory + r'/log.dat', log_output_path)
    os.rename(project_input_directory + r'/trajectory.dat', trajectory_output_path)
    # go back to original working directory
    os.chdir(original_working_directory)
