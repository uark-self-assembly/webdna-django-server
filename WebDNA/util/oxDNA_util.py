import os
from WebDNA.messages import *

def generate_input_file(project_id, data):
    # will assume sequence.txt exists
    util_path = os.path.dirname(os.path.realpath(__file__))
    project_path = util_path + '/../../server-data/server-projects/' + str(project_id)

    if not os.path.exists(project_path):
        os.makedirs(project_path)

    if not (os.path.isfile(project_path + '/generated.top') and
            os.path.isfile(project_path + '/generated.dat') and
            os.path.isfile(project_path + '/sequence.txt')):
        return MISSING_PROJECT_FILES

    input_file = open(file=project_path + '/input.txt', mode='w')
    for key, value in data.items():
        if key == 'project_id' or key == 'box_size':
            continue

        if key == 'T':
            value = value + ' K'
        input_file.write(key + ' = ' + str(value) + '\n')
    input_file.close()
    return INPUT_GENERATED


def get_input_file_as_serializer_data(project_id):
    util_path = os.path.dirname(os.path.realpath(__file__))
    project_path = util_path + '/../../server-data/server-projects/' + str(project_id)
    if not os.path.isfile(project_path + '/input.txt'):
        return MISSING_PROJECT_FILES

    input_file = open(file=project_path + '/input.txt', mode='r')
    input_dictionary = {}
    for line in input_file.readlines():
        if line[len(line) - 1] == '\n':
            line = line[:-1]
        key_and_value = line.split(' = ')
        input_dictionary[key_and_value[0]] = key_and_value[1]
    return input_dictionary


def get_energy_file(project_id):
    util_path = os.path.dirname(os.path.realpath(__file__))
    project_path = util_path + '/../../server-data/server-projects/' + str(project_id)
    if not os.path.isfile(project_path + '/energy.dat'):
        return MISSING_PROJECT_FILES

    energy_file = open(file=project_path + '/energy.dat', mode='r')
    energy_string = ''
    for line in energy_file.readlines():
        energy_string = energy_string + line
    return energy_string
