import subprocess
import sys
import logging
from venv import create
import os
from pathlib import Path

logger = logging.getLogger(__name__)

os_packages = [
    "pip",
    "setuptools",
    "wheel",
    "jupyter",
    "nbstripout",
    "entrypoints",
    "flake8",
    "yapf",
    "ipykernel",
]


def install(packages: list):
    logger.info(f"Installing system packages")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--user", "-U", *packages]
    )


def setup_venv():
    PROJECT_NAME = Path(os.getcwd()).name
    subprocess.check_call([sys.executable, "-m", "venv", ".venv"])
    cmd = f". .venv/bin/activate && pip install -e . && ipython kernel install --user --name={PROJECT_NAME}"
    subprocess.check_call(cmd, shell=True, executable="/bin/bash")


install(os_packages)
setup_venv()
