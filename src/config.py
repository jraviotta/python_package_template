# Define configuration logic here
import logging
import os
from pathlib import Path
import pandas as pd
from dotenv import find_dotenv, load_dotenv
from IPython import get_ipython
from IPython.core.error import UsageError

logger = logging.getLogger(__name__)
datetime_is_numeric = True

# place sensitive global variables in .env or ~/.credentials/.env
# Read .env files
files = [find_dotenv(), Path(Path.home() / ".credentials", ".env")]
for f in files:
    load_dotenv(f)
    logger.info(f"loading: {f}")

# Set some paths
projectRoot = Path(__file__).parent.parent.absolute()
credentialsPath = Path(Path.home(), ".credentials")
O365_client_id = os.environ.get("O365_CLIENT_ID")
O365_client_secret = os.environ.get("O365_CLIENT_SECRET")
O365_address = os.environ.get("O365_ADDRESS")
O365_scopes = os.environ.get("O365_SCOPES")

logger.info(f"Changing dir to {projectRoot}")
os.chdir(projectRoot)

rawData = os.environ.get("RAW_DATA")
if not rawData:
    rawData = Path(projectRoot / "data" / "raw")
    if not Path.exists(rawData):
        os.mkdir(rawData)

processedData = os.environ.get("PROCESSED_DATA")
if not processedData:
    processedData = Path(projectRoot / "data" / "processed")
    if not Path.exists(processedData):
        os.mkdir(processedData)

documents = os.environ.get("DOCUMENTS")
if not documents:
    if documents is None:
        documents = Path(projectRoot / "documents")
        if not Path.exists(documents):
            os.mkdir(documents)

figures = os.environ.get("FIGURES")
if not figures:
    if figures is None:
        figures = Path(projectRoot / "figures")
        if not Path.exists(figures):
            os.mkdir(figures)

# Configure logging
VERBOSITY = "INFO"
noisyLibs = [
    "googleapiclient.discovery",
    "requests_oauthlib.oauth2_session",
    "matplotlib.font_manager",
    "urllib3.connectionpool",
]

# Configure pandas
try:
    logger.info("Setting pandas display options")
    pd.options.display.width = None
    pd.options.display.max_rows = 200
    pd.options.display.min_rows = 100
    pd.options.display.max_columns = 50
    pd.options.display.max_colwidth = 200
    pd.options.display.float_format = '{:.5f}'.format

except ModuleNotFoundError:
    pass

# Configure matplotlib
try:
    import matplotlib

    logger.info("Setting matplotlib display options")
    # matplotlib.use('Agg')
except Exception as e:
    print(e)
