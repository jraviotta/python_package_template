import logging
from pathlib import Path  # NOQA F401

import click
import pandas as pd  # NOQA F401

from fluve.data import build_project_command
from fluve.db import init_db_command
from fluve.email.email import (authenticate_o365_command,
                               render_and_email_command, start_server_command,
                               render_report_command)
from fluve.loggers import setup_logging
from fluve.visualize import build_plots_command

logger = logging.getLogger(__name__)


@click.group()
@click.option('--verbose', '-v', count=True, help="-v for INFO, -vv for DEBUG")
@click.pass_context
def cli(ctx, verbose):
    setup_logging(verbose)


cli.add_command(build_project_command)
cli.add_command(authenticate_o365_command)
cli.add_command(render_and_email_command)
cli.add_command(render_report_command)
cli.add_command(start_server_command)
cli.add_command(init_db_command)
