from setuptools import find_packages, setup

setup(
    name="package_template",  # update
    packages=find_packages(),
    version="0.1.0",
    description="",
    author="jraviotta",
    license="MIT",
    install_requires=[
        "Click",
        "python-dotenv",
        "numpy",
        "pandas>=1",
        "flake8",
        "black",
        "ipykernel",
        "termcolor",
        "nbformat",
        "seaborn",
        "nbconvert",
        "jupyter_contrib_nbextensions",
        "sklearn",
    ],
    dependency_links=[],
    entry_points="""
        [console_scripts]
        package_template=src.cli:cli 
    """,  # update
)
