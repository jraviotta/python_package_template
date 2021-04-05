import logging
import os
from pathlib import Path
import datetime
from dotenv import find_dotenv, load_dotenv

import src.config as config
from src import cli
from src.loggers import setup_logging

# place sensitive global variables in .env or ~/.credentials/.env
# Read .env files
files = [find_dotenv(), Path(Path.home() / ".credentials", '.env')]
for f in files:
    load_dotenv(f)

logger = logging.getLogger(__name__)
setup_logging(verbose=config.VERBOSITY)
