from __future__ import absolute_import
from webdna_server.celery import app


# ==========TASKS==========
# TODO: Define tasks here


@app.task
def test():
    print("Test task received from WebDNA server!")
