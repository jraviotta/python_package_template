import logging

import click
from IPython import get_ipython

from src.data import build_project_command
from src.loggers import setup_logging
from src.utils import convert_py_to_html_command

if get_ipython():
    logger = setup_logging("DEBUG")
else:
    logger = logging.getLogger(__name__)


@click.group()
@click.option("--debug", "-d", count=True, help="-d for INFO, -dd for DEBUG")
@click.pass_context
def cli(ctx, debug):
    setup_logging(debug)


cli.add_command(build_project_command)
cli.add_command(convert_py_to_html_command)
