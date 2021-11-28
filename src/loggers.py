import cgitb
import logging
import os
import site
import sys
import warnings
from datetime import datetime
from os.path import abspath, join
from traceback import extract_tb, format_exception_only, format_list
from typing import List

import urllib3
from IPython import get_ipython
from termcolor import colored

import src.config as config

LOGGER = logging.getLogger(__name__)
IPYTHON = get_ipython()


def _set_lib_loggers(level: str, noisyLibs: list) -> None:
    """
    Set the logging level for third party libraries
    :return: None
    """

    for lib in noisyLibs:
        logging.getLogger(lib).setLevel(level=level)

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)

    def _check_file(name):
        return name and not name.startswith("hide")

    def _print(type, value, tb):
        show = (fs for fs in extract_tb(tb) if _check_file(fs.filename))
        fmt = format_list(show) + format_exception_only(type, value)
        print("".join(fmt), end="", file=sys.stderr)

    return _print


def set_cli_errors(level: str, logger: logging.Logger = LOGGER) -> None:
    def shadow(*hide):
        """Return a function to be set as new sys.excepthook.
        It will HIDE traceback entries for files from these directories."""
        hide = tuple(join(abspath(p), "") for p in hide)

        def _check_file(name):
            return name and not name.startswith(hide)

        def _print(type, value, tb):
            show = (fs for fs in extract_tb(tb) if _check_file(fs.filename))
            fmt = format_list(show) + format_exception_only(type, value)
            print("".join(fmt), end="", file=sys.stderr)

        return _print

    def exception_handler(exception_type,
                          exception,
                          tb,
                          debug_hook=sys.excepthook):

        logger.error(f"""{colored(exception_type.__name__, 'red')}: \n
            {colored(exception, 'yellow')}""")

    if level == "DEBUG":
        cgitb.enable(True, None, 5, "text")
    elif level == "INFO":
        sys.excepthook = shadow(*site.getsitepackages())
    else:
        sys.excepthook = exception_handler


def setup_logging(verbose=None, logger=LOGGER) -> object:
    # Read verbosity
    if verbose == 2 or verbose == "DEBUG":
        level = "DEBUG"
        os.environ["VERBOSITY"] = level
    elif verbose == 1 or verbose == "INFO":
        level = "INFO"
        os.environ["VERBOSITY"] = level
    elif verbose == 0 or verbose == "WARNING":
        level = "WARNING"
        os.environ["VERBOSITY"] = level
    elif not verbose and os.environ.get("VERBOSITY"):
        verbose = os.environ.get("VERBOSITY")
        level = os.environ.get("VERBOSITY")
    else:
        level = "WARNING"

    # Silence logs from noisy libraries
    _set_lib_loggers(level="WARNING", noisyLibs=config.noisyLibs)

    # Log to stderr
    log_handlers: List[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    FORMAT = "%(asctime)s %(levelname)s %(module)s:%(lineno)s %(funcName)s() - %(message)s"  # noqa 501
    logging.basicConfig(level=level,
                        format=FORMAT,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        handlers=log_handlers)
    logger.setLevel(level)
    logger.info(
        f"logging set to: {logging.getLevelName(logger.getEffectiveLevel())}:\
            {logger.getEffectiveLevel()}")

    # Configure ipython error handling
    if IPYTHON:
        logger.debug(f"ipython level: {level}")
        if level == "INFO":
            IPYTHON.magic("xmode Minimal")
        # elif level == "DEBUG":
        #     IPYTHON.magic("xmode Context")
        elif level == "DEBUG":
            IPYTHON.magic("xmode Plain")
        else:
            IPYTHON.magic("xmode Minimal")
    else:
        set_cli_errors(level=level)
    logger.info(f"verbose: {verbose}")
    logger.debug(f"log level: {level}")
    now = datetime.now().replace(second=0, microsecond=0)
    print(f"Output produced: {now}")
    return logger
