import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def install():
    PROJECT_NAME = Path(os.getcwd()).name
    print("Installing src package")
    cmd = "python3 -m venv .venv"
    subprocess.check_call(cmd, shell=True, executable="/usr/bin/bash")

    logger.info("Installing IPython kernel")
    cmd = f". .venv/bin/activate && pip install -e . && ipython kernel install --user --name={PROJECT_NAME} --display-name={PROJECT_NAME}"
    subprocess.check_call(cmd, shell=True, executable="/usr/bin/bash")


install()
