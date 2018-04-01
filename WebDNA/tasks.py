from __future__ import absolute_import
from webdna_server.celery import app
import subprocess
import os


# ==========TASKS==========
# TODO: Define tasks here

@app.task()
def execute_sim(proj_id, path):
    print("Received new execution for project: " + proj_id)
    p = subprocess.Popen(["oxDNA", os.getcwd() + "/" + path + "/input.txt"], cwd=os.getcwd() + "/" + path)


@app.task
def test():
    print("Test task received from WebDNA server!")
