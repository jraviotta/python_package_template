import logging
from pathlib import Path  # NOQA F401

import click

from src.data import build_project_command
from src.loggers import setup_logging

logger = logging.getLogger(__name__)


@click.group()
@click.option('--verbose', '-v', count=True, help="-v for INFO, -vv for DEBUG")
@click.pass_context
def cli(ctx, verbose):
    setup_logging(verbose)


cli.add_command(build_project_command)
