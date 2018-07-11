import os
import json
import subprocess
from webdna.defaults import ProjectFile
import webdna.util.server as server
from zipfile import ZipFile


class Payload(object):
    def __init__(self, file):
        self.__dict__ = json.load(file)


class Generation:
    def __init__(self, method=None, arguments=None, orig=None, dictionary=None):
        if orig is None:
            if dictionary is None:
                self.method = method
                self.arguments = arguments
                self.files = None
                if method == 'generate-sa' or method == 'generate-folded':
                    self.files = 'sequence.txt'
                    self.arguments.append(self.files)
                    self.arguments.insert(0, method + '.py')
                elif method == 'cadnano-interface':
                    self.files = 'cadnano-project.json'
                    self.arguments.insert(0, self.files)
                    self.arguments.insert(0, self.method + '.py')

                if self.files is None:
                    raise ValueError('Value of method argument not valid')
            else:
                self.load(dictionary)
        else:
            self.copy(orig)

    def copy(self, orig):
        self.method = orig.method
        self.files = orig.files
        self.arguments = orig.arguments

    def load(self, dictionary):
        self.method = dictionary['method']
        self.files = dictionary['files']
        self.arguments = dictionary['arguments']

    def serializable(self):
        return {
            'method': self.method,
            'files': self.files,
            'arguments': self.arguments
        }


class ProjectSettings:
    def __init__(self, project_name, generation):
        self.name = project_name
        self.gen = Generation(orig=generation)

    def serializable(self):
        return {
            'name': self.name,
            'gen': self.gen.serializable()
        }


def is_executable(project_id, regenerate, generation_settings):
    input_file = server.get_project_file(project_id, ProjectFile.INPUT)

    if not os.path.isfile(input_file):
        return False

    if generation_settings.method == 'generate-sa' or 'generate-folded':
        if regenerate:
            sequence_file = server.get_project_file(project_id, ProjectFile.SEQUENCE)
            if os.path.isfile(sequence_file):
                return True
            else:
                return False
        else:
            generated_top = server.get_project_file(project_id, ProjectFile.GENERATED_TOP)
            generated_dat = server.get_project_file(project_id, ProjectFile.GENERATED_DAT)
            if os.path.isfile(generated_dat) and os.path.isfile(generated_top):
                return True
            else:
                return False
    elif generation_settings.method == 'cadnano-interface':
        if regenerate:
            cadnano_project_file = server.get_project_file(project_id, ProjectFile.CADNANO)
            if os.path.isfile(cadnano_project_file):
                return True
            else:
                return False
        else:
            generated_top = server.get_project_file(project_id, ProjectFile.GENERATED_TOP)
            generated_dat = server.get_project_file(project_id, ProjectFile.GENERATED_DAT)
            if os.path.isfile(generated_dat) and os.path.isfile(generated_top):
                return True
            else:
                return False
    else:
        return False



def zip_simulation(project_id):
    project_zip_path = server.get_project_file(project_id, ProjectFile.SIMULATION_ZIP)
    if server.simulation_files_exist(project_id):
        (pdb_file_path, xtc_file_path) = server.get_simulation_file_paths(project_id)

        with ZipFile(project_zip_path, 'w') as archive:
            archive.write(pdb_file_path, 'trajectory.pdb')
            archive.write(xtc_file_path, 'trajectory.xtc')
        return project_zip_path
    return None


def zip_project(project_id):
    project_folder_path = server.get_project_folder_path(project_id)
    project_zip_path = server.get_project_file(project_id, ProjectFile.PROJECT_ZIP)

    if server.project_folder_exists(project_id):
        if os.path.exists(project_zip_path):
            os.remove(project_zip_path)

        with ZipFile(project_zip_path, 'w') as archive:
            for (dir_path, dir_names, file_names) in os.walk(project_folder_path):
                file_names_len = len(file_names)
                for i in range(0, file_names_len):
                    if '.zip' in file_names[i]:
                        continue
                    archive.write(os.path.join(dir_path, file_names[i]), file_names[i])
        return project_zip_path
    return None


def convert_dat_to_pdb(project_id):
    if not server.project_file_exists(project_id, ProjectFile.TRAJECTORY_DAT) \
            or not server.project_file_exists(project_id, ProjectFile.GENERATED_TOP):
        return False

    project_folder_path = server.get_project_folder_path(project_id)
    process = subprocess.Popen(["traj2pdb.py", "trajectory.dat", "generated.top", "trajectory.pdb"],
                               cwd=project_folder_path)
    process.wait()
    return True


def convert_pdb_to_xtc(input_file_path, output_file_path):
    print('gmx trjconv -f {} -o {}'.format(input_file_path, output_file_path))
    process = subprocess.Popen(["gmx", "trjconv", "-f", input_file_path, "-o", output_file_path],
                               cwd=os.getcwd(), stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    process.wait()


def convert_pdb_to_single_frame(input_file_path, output_file_path):
    output_file = open(output_file_path, 'w')

    try:
        with open(input_file_path) as infile:
            for line in infile:
                if 'ENDMDL' not in line:
                    output_file.write(line)
                else:
                    output_file.write('ENDMDL')
                    break
    except FileNotFoundError:
        pass

    output_file.close()


def generate_sim_files(project_id):
    # Firstly, convert the 'trajectory.dat' file to 'trajectory.pdb'
    if not convert_dat_to_pdb(project_id):
        return False

    # If the 'server-sims' directory doesn't exist, make it here
    os.makedirs(server.get_simulation_folder_path(), exist_ok=True)

    # Get the file paths for the output simulation PDB and XTC files
    (pdb_file_path, xtc_file_path) = server.get_simulation_file_paths(project_id)

    # The original 'trajectory.pdb' that will be converted to simulation files
    original_pdb_path = server.get_project_file(project_id, ProjectFile.TRAJECTORY_PDB)

    try:
        os.remove(pdb_file_path)
        os.remove(xtc_file_path)
    except OSError:
        pass

    convert_pdb_to_xtc(input_file_path=original_pdb_path, output_file_path=xtc_file_path)
    convert_pdb_to_single_frame(input_file_path=original_pdb_path, output_file_path=pdb_file_path)
    return True
