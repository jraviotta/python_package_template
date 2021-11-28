import logging
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
import os
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)
datetime_is_numeric = True

# place sensitive global variables in .env or ~/.credentials/.env
# Read .env files
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
os.environ['PROJECT_ROOT'] = str(PROJECT_ROOT)
logger.info(f"Changing dir to {PROJECT_ROOT}")
os.chdir(PROJECT_ROOT)
files = [find_dotenv(), Path(Path.home() / ".credentials", '.env')]
for f in files:
    logger.info(f"loading: {f}")

    load_dotenv(f)

# DB_ENGINE = create_engine(os.getenv("DB_URL"), pool_pre_ping=True)
