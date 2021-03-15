import logging

import click
import numpy as np
import pandas as pd

import src.config as config

logger = logging.getLogger(__name__)


def build_project():
    project = # stuff here
    
    return project


@click.command('build-project')
def build_project_command():
    obj = build_project()
    click.echo(obj.data.head())
