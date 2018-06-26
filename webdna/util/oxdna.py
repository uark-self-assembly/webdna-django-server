import os
import subprocess

import webdna.defaults as defaults
import webdna.util.server as server
from webdna.defaults import ProjectFile


def generate_sa(project_folder_path, box_size, log_file_path, sequence_file_name=defaults.DEFAULT_SEQUENCE_FILE_NAME):
    log = None
    if log_file_path is not None:
        log = open(file=log_file_path, mode='w')
        process = subprocess.Popen(
            [
                'generate-sa.py',
                str(box_size),
                sequence_file_name
            ],
            cwd=os.path.join(os.getcwd(), project_folder_path),
            stderr=log
        )
    else:
        process = subprocess.Popen(
            [
                'generate-sa.py',
                str(box_size),
                sequence_file_name
            ],
            cwd=os.path.join(os.getcwd(), project_folder_path)
        )

    process.wait()
    if log_file_path is not None:
        log.close()

    return True


def convert_dat_to_pdb(project_id):
    if not server.project_file_exists(project_id, ProjectFile.TRAJECTORY_DAT) \
            or not server.project_file_exists(project_id, ProjectFile.GENERATED_TOP):
        return False

    project_folder_path = server.get_project_folder_path(project_id)
    process = subprocess.Popen(
        [
            'traj2pdb.py',
            ProjectFile.TRAJECTORY_DAT.value,
            ProjectFile.GENERATED_TOP.value,
            ProjectFile.TRAJECTORY_PDB.value
        ],
        cwd=project_folder_path
    )
    process.wait()
    return True
