import logging

import pandas as pd

logger = logging.getLogger(__name__)

# place sensitive global variables in .env or ~/.credentials/.env

# TODO move to .env
# Set some paths
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
credentialsPath = Path(Path.home(), ".credentials")
O365_client_id = os.environ.get("O365_CLIENT_ID")
O365_client_secret = os.environ.get("O365_CLIENT_SECRET")
O365_address = os.environ.get("O365_ADDRESS")
O365_scopes = os.environ.get("O365_SCOPES")

# Configure logging
noisyLibs = [
    "googleapiclient.discovery",
    "requests_oauthlib.oauth2_session",
    "matplotlib.font_manager",
    "urllib3.connectionpool",
]

# Configure pandas
try:
    logger.info("Setting pandas display options")
    pd.options.display.width = 20
    pd.options.display.max_rows = 100
    pd.options.display.min_rows = 20
    pd.options.display.max_columns = 20
    pd.options.display.max_colwidth = 200
    pd.options.display.float_format = '{:.5f}'.format
except ModuleNotFoundError:
    pass
