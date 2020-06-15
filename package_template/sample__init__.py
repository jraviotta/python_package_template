import logging
import os
from pathlib import Path
import datetime
import plotly.graph_objects as go
from dotenv import find_dotenv, load_dotenv
from flask import Flask, current_app, render_template
from plotly.offline import plot

import fluve.config as config
from fluve import cli
from fluve.data import build_fluve_project
from fluve.loggers import setup_logging
from fluve.visualize import build_plots

# place sensitive global variables in .env or ~/.credentials/.env
# Read .env files
files = [find_dotenv(), Path(Path.home() / ".credentials", '.env')]
for f in files:
    load_dotenv(f)

logger = logging.getLogger(__name__)
setup_logging()


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__,
                instance_relative_config=True,
                static_folder='static')
    app.config.from_mapping(SECRET_KEY='dev',
                            DATABASE=Path(app.instance_path, 'fluve.sqlite'),
                            SERVER_NAME="localhost:5000")
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Build data objects
    app.proj = build_fluve_project()
    app.plots = build_plots(app.proj)

    # Initialize database
    from . import db
    db.init_app(app)

    # Render base template without content
    @app.route('/')
    def script_output():
        return render_template('base.html')

    with app.app_context():

        @app.context_processor
        def inject_now():
            return {'now': datetime.datetime.now()}

        from .blueprints.bp_plots import bp_plots
        current_app.register_blueprint(bp_plots)

    return app
