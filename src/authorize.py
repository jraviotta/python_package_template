# Define authorization flows here
import json
import logging
import pickle
from pathlib import Path

# after v0.13
from authlib.integrations.requests_client import AssertionSession
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from gspread import Client

import src.config

logger = logging.getLogger(__name__)

credentialsPath = src.config.credentialsPath
client_secrets_file = Path(credentialsPath, "client_secret.json")


def google_auth(scopes: list) -> object:
    """Authorizes google api with existing token or oauth

    Args:
        scopes (list): authorize permission for these scopes
            Example - ['https://www.googleapis.com/auth/contacts']
        client_secrets_file (str): path to secrets file
    Returns:
        creds (object): authorization token
    """

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    tokenFile = Path(credentialsPath, "token.pickle")
    if Path.exists(tokenFile):
        with open(tokenFile, "rb") as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, scopes
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(tokenFile, "wb") as token:
            pickle.dump(creds, token)
    return creds


def build_gspread_client(conf_file):
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    def create_assertion_session(conf_file, scopes, subject=None):
        with open(conf_file, "r") as f:
            conf = json.load(f)

        token_url = conf["token_uri"]
        token_endpoint = conf["token_uri"]
        issuer = conf["client_email"]
        key = conf["private_key"]
        key_id = conf.get("private_key_id")

        header = {"alg": "RS256"}
        if key_id:
            header["kid"] = key_id

        # Google puts scope in payload
        claims = {"scope": " ".join(scopes)}
        return AssertionSession(
            token_endpoint=token_endpoint,
            grant_type=AssertionSession.JWT_BEARER_GRANT_TYPE,
            token_url=token_url,
            issuer=issuer,
            audience=token_url,
            claims=claims,
            subject=subject,
            key=key,
            header=header,
        )

    session = create_assertion_session(conf_file=conf_file, scopes=scopes)
    return Client(None, session=session)


# # Define utility functions here
# import logging
# import pickle
# import typing
# from pathlib import Path

# from google.auth.transport.requests import Request
# from google_auth_oauthlib.flow import InstalledAppFlow

# from src.loggers import setup_logging

# setup_logging()
# logger = logging.getLogger(__name__)

# # def google_auth(scopes: list, client_secrets_file: str) -> object:
# #     """Authorizes google api with existing token or oauth

# #     Args:
# #         scopes (list): authorize permission for these scopes
# #             Example - ['https://www.googleapis.com/auth/contacts']
# #         client_secrets_file (str): path to secrets file
# #     Returns:
# #         creds (object): authorization token
# #     """

# #     creds = None
# #     token = Path('token.pickle')
# #     if Path.exists(token):
# #         pass
# #     elif Path.exists(Path(Path.cwd().parent, token)):
# #         token = Path(Path.cwd().parent, token)
# #     try:
# #         with open(token, 'rb') as token:
# #             creds = pickle.load(token)
# #     except FileNotFoundError:
# #         pass
# #     # If there are no (valid) credentials available, let the user log in.
# #     if not creds or not creds.valid:
# #         if creds and creds.expired and creds.refresh_token:
# #             creds.refresh(Request())
# #         else:
# #             flow = InstalledAppFlow.from_client_secrets_file(
# #                 client_secrets_file, scopes)
# #             creds = flow.run_local_server(port=0)
# #         # Save the credentials for the next run
# #         token = Path('token.pickle')
# #         with open(token, 'wb') as token:
# #             pickle.dump(creds, token)
# #     return creds
