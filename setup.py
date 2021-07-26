from setuptools import find_packages, setup

setup(
    name="package_template",  # update
    version="0.1.5",  # update
    description="",  # update
    author="jraviotta",  # update
    license="MIT",  # update
    packages=find_packages(),
    install_requires=[
        "pip",
        "Click",
        "ipython",
        "setuptools",
        "python-dotenv",
        "flake8",
        "yapf",
        "ipykernel",
        "termcolor",
        "nbformat",
        "nbconvert",
        "jupyter_contrib_nbextensions",
        "authlib",
        "google_auth",
        "gspread",
        "statsmodels",
        "sklearn",
        "imbalanced-learn",
        "openpyxl",
        "numpy",
        "pandas>=1",
        "seaborn",
    ],
    dependency_links=[],
    entry_points=dict(console_scripts=['package_template=src.cli:cli']  #update
                      ))
