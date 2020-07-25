from setuptools import find_packages, setup

setup(
    name='package_template',
    packages=find_packages(),
    version='0.1.0',
    description='',
    author='jraviotta',
    license='MIT',
    install_requires=[
        'Click', 'O365', 'python-dotenv', 'numpy', 'pandas>=1', 'xlrd',
        'flask', 'flake8', 'ipykernel', 'python-dotenv',
        'termcolor', 'PyCap', 'flask', 'plotly', 'nbformat'
    ],
    dependency_links=[
        'http://github.com/redcap-tools/PyCap/tarball/master#egg=package-1.0'
    ],
    entry_points='''
        [console_scripts]
        package_template=src.cli:cli
    ''',
)
