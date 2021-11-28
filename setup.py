# vscode-fold=0
import os
from pathlib import Path

from setuptools import find_packages, setup

PROJECT_NAME = Path(os.getcwd()).name

setup(
    name=PROJECT_NAME,
    version="2.0",  # update
    description="",  # update
    author="",  # update
    license="MIT",  # update
    packages=find_packages(),
    python_requires='>=3.1',
    install_requires=[
        # python stuff
        "pip",
        "setuptools",
        "wheel",
        # jupyter stuff
        "ipython",
        "ipykernel",
        "jupyter",
        "nbformat",
        "nbconvert",
        "nbstripout",
        "jupyter_contrib_nbextensions",
        "jupytext",
        # Dev stuff
        "Click",
        "entrypoints",
        "flake8",
        "yapf",
        "pylint",
        "paramiko",
        # Utils
        "python-dotenv",
        "termcolor",
        "authlib",
        "google_auth",
        "gspread",
        "openpyxl",
        "typing_extensions>=3.10.0",
        "pyparsing<3,>=2.0.2",
        # Database
        "psycopg2",
        'sqlalchemy',
        # Analytic
        "statsmodels",
        "sklearn",
        "imbalanced-learn",
        "numpy",
        "pandas>=1",
        "seaborn",
        # Dev
        # TODO Make dev install profile
    ],
    dependency_links=[],
    entry_points=dict(console_scripts=[f"{PROJECT_NAME}=src.cli:cli"]),
)
