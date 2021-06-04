from setuptools import find_packages, setup

setup(
    name="package_template",  # update
    version="0.1.0",  # update
    description="",  # update
    author="jraviotta",  # update
    license="MIT",  # update
    packages=find_packages(),
    install_requires=[
        "Click",
        "setuptools",
        "python-dotenv",
        "flake8",
        "black",
        "ipykernel",
        "termcolor",
        "nbformat",
        "nbconvert",
        "jupyter_contrib_nbextensions",
        "numpy",
        "pandas>=1",
        "seaborn",
    ],
    dependency_links=[],
    entry_points=dict(
        console_scripts=[
            'package_template=src.cli:cli']  #update
        )
)
