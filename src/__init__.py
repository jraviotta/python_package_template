import logging
from pathlib import Path
from dotenv import find_dotenv, load_dotenv

# place sensitive global variables in .env or ~/.credentials/.env
# Read .env files
files = [find_dotenv(), Path(Path.home() / ".credentials", '.env')]
for f in files:
    load_dotenv(f)

logger = logging.getLogger(__name__)
