import os
from WebDNA.messages import *

def generate_input_file(project_id, data):
    # will assume sequence.txt exists
    project_path = os.path.join('server-data', 'server-projects', str(project_id))
    top_path = os.path.join(project_path, 'generated.top')
    dat_path = os.path.join(project_path, 'generated.dat')
    sequence_path = os.path.join(project_path, 'sequence.txt')
    input_path = os.path.join(project_path, 'input.txt')

    if not os.path.exists(project_path):
        os.makedirs(project_path)

    if not (os.path.isfile(top_path) and os.path.isfile(dat_path) and os.path.isfile(sequence_path)):
        return MISSING_PROJECT_FILES

    input_file = open(file=input_path, mode='w')
    for key, value in data.items():
        if key == 'project_id' or key == 'box_size':
            continue
        if key == 'T':
            value = value + ' K'
        input_file.write(key + ' = ' + str(value) + '\n')
    input_file.close()

    return INPUT_GENERATED


def get_input_file_as_serializer_data(project_id):
    project_path = os.path.join('server-data', 'server-projects', str(project_id))
    input_path = os.path.join(project_path, 'input.txt')

    if not os.path.isfile(input_path):
        return MISSING_PROJECT_FILES

    input_file = open(file=input_path, mode='r')
    input_dictionary = {}
    for line in input_file.readlines():
        if line[len(line) - 1] == '\n':
            line = line[:-1]
        key_and_value = line.split(' = ')
        input_dictionary[key_and_value[0]] = key_and_value[1]

    return input_dictionary


def get_energy_file(project_id):
    project_path = os.path.join('server-data', 'server-projects', str(project_id))
    energy_path = os.path.join(project_path, 'energy.dat')

    if not os.path.isfile(energy_path):
        return MISSING_PROJECT_FILES

    energy_file = open(file=energy_path, mode='r')
    energy_string = ''
    for line in energy_file.readlines():
        energy_string = energy_string + line

    return energy_string
