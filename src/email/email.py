import logging
import os
from pathlib import Path
import shlex
import subprocess
import plotly.io as pio
import click
import O365
from flask import render_template
from flask.cli import with_appcontext
import src
import src.config as config
from src.blueprints.bp_plots import show_plot_pages
logger = logging.getLogger(__name__)


def authenticate_o365(O365_client_id: str = config.O365_client_id,
                      O365_client_secret: str = config.O365_client_secret,
                      scopes: list = config.O365_scopes):
    credentials = (O365_client_id, O365_client_secret)

    account = O365.Account(credentials)

    if not account.is_authenticated:
        logger.info('Need to authenticate')
        # ask for a login
        print(account.authenticate(scopes=scopes))

    else:
        print('Account authenticated.')
    return account


def send_O365_message(address: str = None,
                      subject: str = None,
                      body: str = None,
                      attachments: list = None):
    """Sends a message using O365 account."""
    account = authenticate_o365()

    m = account.new_message()
    m.to.add(address)
    m.subject = subject
    if attachments is not None:
        idx = 0
        for i in attachments:
            m.attachments.add(i)
            # att = m.attachments[idx]
            # att.is_inline = True
            # att.content_id = i
            # idx += 1
    m.body = body
    logger.info("sending message")
    m.send()


@click.command('auth-o365')
def authenticate_o365_command():
    click.echo('Authenticating with O365')
    scopes = ['basic', 'message_all']
    authenticate_o365(O365_client_id=config.O365_client_id,
                      O365_client_secret=config.O365_client_secret,
                      scopes=scopes)


def render_report():
    start_server()
    app = src.create_app()
    logger.info('rendering html')
    with app.app_context():
        handle = str(Path(config.documents / 'plots.html').resolve())

        with open(handle, "w") as f:
            f.write(show_plot_pages(page="email"))
    return handle


def render_and_email(to: list = None, subject=None, **kwargs):
    start_server()
    if not to:
        to = [os.environ.get('O365_ADDRESS')]
    if not subject:
        subject = 'TEST'
    handle = render_report()
    for address in to:
        logger.info(f'sending email to: {address}')
        send_O365_message(address=address,
                          subject=subject,
                          body='Update attached.',
                          attachments=[handle])


def check_server():
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 5000))
    if result != 0:
        logger.info(f'Webserver offline run start-server')
    return result


def start_server():
    """Starts flask webserver on 127.0.0.1:5000"""
    logger.info('Checking webserver')
    if check_server() != 0:

        def run_command(command):
            process = subprocess.Popen(shlex.split(command),
                                       stdout=subprocess.PIPE)
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())

            rc = process.poll()
            return rc

        logger.info('Starting webserver')
        run_command(command='python -m flask run')
    print("Webserver running at 127.0.0.1:5000")


@click.command('start-server')
def start_server_command():
    """Starts flask webserver on 127.0.0.1:5000"""
    start_server()


@click.command('render-report')
@with_appcontext
def render_report_command():
    """Save report"""
    render_report()


@click.command('render-and-email')
@click.option("--to",
              type=click.STRING,
              help="Recipient's email address",
              multiple=True)
@click.option("--subject",
              "-s",
              "subject",
              type=click.STRING,
              help="Message subject",
              default='TEST')
@with_appcontext
def render_and_email_command(to, subject):
    """Send an email"""
    render_and_email(to, subject)
