import os
import subprocess
import redis

################################
# These utilities assumes WebDNA/data/community_scripts, WebDNA/data/user_projects and WebDNA/oxDNA.
#
# Sequence.txt not associated with options, but Box Sides is.
# Some options will not be available to change such as genertated.top, generated.dat, energy.dat, etc.
# options will also have default options (i.e. 'topology' : ['topology', 'generated.top'])
# options = {
#               'Box Sides' : ['box sides', 'formatted input'],
#               'sim_type' : ['sim_type', 'MD'],
#               'backend' : ['backend', 'CPU'],
#               'steps' : ['steps', '1e6'],
#               'newtonian_steps' : ['newtonian_steps', '103'],
#               .
#               .
#               .
# }
# sequence = [
#               ['', 'AAGT', 4],
#               ['DOUBLE', 'TTTT', 3],
#               ['', 'CGAA', 2],
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


def output_message(session_key, user, message):
    conn = redis.StrictRedis()
    ws_url = '{0}:{1}'.format(session_key, user)
    conn.publish(ws_url, message)


def ensure_path(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path


# assumes current working directory hasn't been changed (os.chdir() not used)
def ensure_user_path(user_UUID_str):
    user_path = os.path.dirname(os.path.realpath(__file__)) + r'/../data/user_projects/' + user_UUID_str
    return ensure_path(user_path)


def ensure_user_script_path(user_UUID_str, script_UUID_str):
    user_path = ensure_user_path(user_UUID_str)
    user_scripts_path = user_path + r'/user_scripts'
    ensure_path(user_scripts_path)
    script_path = user_scripts_path + r'/' + script_UUID_str
    return ensure_path(script_path)


def ensure_community_script_path(script_UUID_str):
    community_scripts_path = os.path.dirname(os.path.realpath(__file__)) + r'/../data/community_scripts'
    community_script_path = ensure_path(community_scripts_path) + r'/' + script_UUID_str
    return ensure_path(community_script_path)


def ensure_project_path(user_UUID_str, project_UUID_str):
    user_path = ensure_user_path(user_UUID_str)
    project_path = user_path + r'/' + project_UUID_str
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


def get_file_lines(file_path):
    try:
        file = open(file_path, 'r')
        lines = file.readlines()
        file.close()
        return lines
    except (IOError, OSError):
        return []


def list_files_lines(*file_paths):
    files_lines = []
    for file_path in file_paths:
        lines = get_file_lines(file_path)
        if len(lines) == 0:
            return []
        files_lines.append(lines)
    return files_lines


def execute(command, user_UUID_str):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # stdout=subprocess.PIPE for stdoutdata to be something other than None
    while True:
        next_line = process.stdout.readline()
        # if child process terminated .poll()=returncode else .poll()=None
        if next_line == '' and process.poll() is not None:
            break
        ######################################################
        # output_message('0', user_UUID_str, next_line) # should the token be on the session key?
        ######################################################
    output = process.communicate()[0]  # process.communicate()=(stdoutdata, stderr)
    exit_code = process.returncode  # exit status of child process

    if exit_code == 0:
        return output
    else:
        raise Exception(command, exit_code, output)


def generate_input(input_options, user_UUID_str, project_UUID_str):
    project_path = ensure_project_path(user_UUID_str, project_UUID_str)
    project_input_path = project_path + r'/input'
    sequence_file_path = project_input_path + r'/sequence.txt'
    generated_dat_file_path = project_input_path + r'/generated.dat'
    generated_top_file_path = project_input_path + r'/generated.top'
    input_file_path = project_input_path + r'/input.txt'

    if not os.path.exists(sequence_file_path):
        raise IOError
        # return 'Error. Must generate sequence.txt first'
    ensure_file_does_not_exist(generated_dat_file_path)
    ensure_file_does_not_exist(generated_top_file_path)
    ensure_file_does_not_exist(input_file_path)

    # generate-sa.py, generate-RNA.py, generate.py? depending on options?
    # with box sides i.e. 'python generate-sa.py 9 sequence.txt'
    original_working_directory = os.getcwd()
    os.chdir(project_input_path)
    bash_command = 'python ../../../../../oxDNA/UTILS/generate-sa.py ' + input_options['Box Sides'][1] + ' sequence.txt'
    execute(bash_command, user_UUID_str)

    input_file = open(input_file_path, 'w')
    try:
        for line in input_options.readlines():
            input_file.write(line)
        input_file.close()
        os.chdir(original_working_directory)
        return list_files_lines(input_file_path, sequence_file_path, generated_dat_file_path, generated_top_file_path)
    except (TypeError, IOError):
        pass

    try:
        # create input file based on options dictionary
        for value in input_options.itervalues():
            input_file.write(value[0] + ' = ' + value[1] + '\n')
        input_file.close()
        os.chdir(original_working_directory)
        return list_files_lines(input_file_path, sequence_file_path, generated_dat_file_path, generated_top_file_path)
    except TypeError:
        pass

    input_file.close()
    ensure_file_does_not_exist(input_file_path)
    os.chdir(original_working_directory)
    raise TypeError
    # return 'First argument expects to be a file object that can be read or a dictionary'


# return string of sequence?
# currently only accepts array input
def generate_sequence(sequence_input, user_UUID_str, project_UUID_str):
    # sequence_input should check for just whole file or array
    project_path = ensure_project_path(user_UUID_str, project_UUID_str)
    sequence_file_path = project_path + r'/input/sequence.txt'
    ensure_file_does_not_exist(sequence_file_path)
    sequence_file = open(sequence_file_path, 'w')

    try:
        for line in sequence_input.readlines():
            sequence_file.write(line)
        sequence_file.close()
        return
    except (TypeError, IOError):
        pass

    try:
        # write to sequence.txt as if sequence_input = [['DOUBLE', 'AAT', 9], ['', 'TTG', 4], ['', 'CGT', 3]]
        for i in range(len(sequence_input)):
            for j in range(len(sequence_input[i][2])):
                if sequence_input[i][0] == 'DOUBLE':
                    line = sequence_input[i][0] + ' ' + sequence_input[i][1] + '\n'
                else:
                    line = sequence_input[i][1] + '\n'
                sequence_file.write(line)
        sequence_file.close()
        return
    except TypeError:
        pass

    sequence_file.close()
    ensure_file_does_not_exist(sequence_file_path)
    raise TypeError
    # return 'First argument expects to be a file object that can be read or a list'


def generate_complete_input(user_UUID_str, project_UUID_str, input_options, sequence_input, *otherfiles):
    pass


# return shell output? return output files as files or strings?
def run_oxDNA(user_UUID_str, project_UUID_str):
    original_working_directory = os.getcwd()
    project_input_path = ensure_project_path(user_UUID_str, project_UUID_str) + r'/input'
    energy_output_path = project_input_path + r'/../output/energy.dat'
    last_conf_output_path = project_input_path + r'/../output/last_conf.dat'
    log_output_path = project_input_path + r'/../output/log.dat'
    trajectory_output_path = project_input_path + r'/../output/trajectory.dat'
    # change working directory so that output files will land somewhere appropriate
    os.chdir(project_input_path)

    if not os.path.exists(project_input_path + r'/input.txt'):  # or only input without .txt?
        os.chdir(original_working_directory)
        raise IOError
        # return 'Error. Input file missing'
    # make sure no copies are made with each execution
    ensure_file_does_not_exist(energy_output_path)
    ensure_file_does_not_exist(last_conf_output_path)
    ensure_file_does_not_exist(log_output_path)
    ensure_file_does_not_exist(trajectory_output_path)

    bash_command = '../../../../../oxDNA/build/bin/oxDNA input.txt'
    execute(bash_command, user_UUID_str)
    # are these the only possible output files?
    os.rename(project_input_path + r'/energy.dat', energy_output_path)
    os.rename(project_input_path + r'/last_conf.dat', last_conf_output_path)
    os.rename(project_input_path + r'/log.dat', log_output_path)
    os.rename(project_input_path + r'/trajectory.dat', trajectory_output_path)
    # back to original working directory
    os.chdir(original_working_directory)
    return list_files_lines(energy_output_path, trajectory_output_path, last_conf_output_path, log_output_path)
