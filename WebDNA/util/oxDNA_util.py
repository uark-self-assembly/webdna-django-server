import os


def generate_input_file(project_id, data):
    # will assume sequence.txt exists
    util_path = os.path.dirname(os.path.realpath(__file__))
    project_path = util_path + '/../../server-data/server-projects/' + project_id

    if not os.path.exists(project_path):
        os.makedirs(project_path)

    os.path.isfile(project_path + '/generated.top')
    os.path.isfile(project_path + '/generated.dat')
    os.path.isfile(project_path + '/sequence.txt')

    input_file = open(project_path + '/input.txt', 'w')
    for key, value in data.items():
        input_file.write(key + ' = ' + value + '\n')
    input_file.close()


def get_input_file_as_serializer_data(project_id):
    pass