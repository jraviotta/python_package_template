import logging
import os
import pickle
import shlex
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import IO, Any

import click
import jupytext
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from IPython.display import display


logger = logging.getLogger(__name__)


class ScriptException(Exception):
    def __init__(self, returncode, stdout, stderr, script):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        Exception().__init__('Error in script')


def plot_validation_score(
    model: object,
    X: pd.DataFrame,
    y: pd.Series,
    scorer: str,
    param: str,
    param_range: list,
):

    train_scores, test_scores = validation_curve(model,
                                                 X,
                                                 y,
                                                 param_name=param,
                                                 param_range=param_range,
                                                 scoring=scorer,
                                                 n_jobs=1)
    train_scores_mean = np.mean(train_scores, axis=1)
    train_scores_std = np.std(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    test_scores_std = np.std(test_scores, axis=1)

    plt.title(f"Validation Curve\n{model}\n{param}")
    plt.xlabel(param)
    plt.ylabel(scorer)
    lw = 2
    plt.semilogx(
        param_range,
        train_scores_mean,
        label=f"Training {scorer}",
        color="darkorange",
        lw=lw,
    )
    plt.fill_between(
        param_range,
        train_scores_mean - train_scores_std,
        train_scores_mean + train_scores_std,
        alpha=0.2,
        color="darkorange",
        lw=lw,
    )
    plt.semilogx(
        param_range,
        test_scores_mean,
        label=f"Cross-validation {scorer}",
        color="navy",
        lw=lw,
    )
    plt.fill_between(
        param_range,
        test_scores_mean - test_scores_std,
        test_scores_mean + test_scores_std,
        alpha=0.2,
        color="navy",
        lw=lw,
    )
    plt.legend(loc="best")
    plt.show()


def plot_roc_det_curves(X: pd.DataFrame, y: pd.Series, classifiers: dict):
    """Plots ROC & DET curves

    Args:
        X (pd.DataFrame): Feature dataset
        y (pd.Series): labels
        classifiers (dict): {Classifier name: classifier}
    """
    X_train, X_test, y_train, y_test = train_test_split(X,
                                                        y,
                                                        test_size=0.3,
                                                        random_state=0)

    # prepare plots
    fig, [ax_roc, ax_det] = plt.subplots(1, 2, figsize=(11, 5))

    for name, clf in classifiers.items():
        clf.fit(X_train, y_train)

        plot_roc_curve(clf, X_test, y_test, ax=ax_roc, name=name)
        plot_det_curve(clf, X_test, y_test, ax=ax_det, name=name)

    ax_roc.set_title("Receiver Operating Characteristic (ROC) curves")
    ax_det.set_title("Detection Error Tradeoff (DET) curves")

    ax_roc.grid(linestyle="--")
    ax_det.grid(linestyle="--")

    plt.legend()
    plt.show()


def pickle_for_later(file_path: Path, object: object) -> None:
    """Pickles an object to specified file

    Args:
        file_path (Path): Path to save pickle
        object (object): Any object
    """
    if not file_path.suffix == ".pkl":
        file_path = Path(str(file_path) + ".pkl")
    logger.info(f"Pickeling {file_path}")
    with open(file_path, "wb") as file:
        pickle.dump(object, file)


def load_pickle(pickle_path: IO) -> Any:

    with open(pickle_path, "rb") as file:
        item = pickle.load(file)
    logger.info(f"{pickle_path.name} loaded")
    return item


def update_legend(g: sns.FacetGrid,
                  title: str = None,
                  labels: list = None,
                  ax_scale: float = 1):
    """Alters a sns.FacetGrid legend title, values, and/or position.

    Args:
        g (sns.FacetGrid): seborn FacetGrid object
        title (str, optional): Legend title. Defaults to None.
        labels (list, optional): Legend labels. Defaults to None.
        ax_scale (float, optional): Value to re-scale axes to make room for
                                    legend labels. Defaults to 1.
    """
    # check axes and find which have legend
    for ax in g.axes.flat:
        leg = g.axes.flat[0].get_legend()
        # Scale ax to make room for legend
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * ax_scale, box.height])
        if leg is not None:
            break
    # or legend may be on a figure
    if leg is None:
        leg = g._legend

    # change legend texts
    leg.set_title(title)
    if labels is not None:
        for t, l in zip(leg.texts, labels):
            t.set_text(l)


def quality_control(df: pd.DataFrame, subset: list = None) -> None:
    """Produces logger.info messages for troubleshooting DataFrame values.

    Args:
        df (pd.DataFrame): A pandas DataFrame
        subset (list, optional): Columns passed to df.duplicated.
                                Defaults to None.
    """
    display("Sample data:")
    display(df.head())
    display("df.info:")
    display(df.info(show_counts=True, verbose=True))
    # display("Count of missing data by column:")
    # display(df.isna().sum())
    display("df.describe:")
    display(df.describe(include='all', datetime_is_numeric=True))
    display(f"Count of duplicate rows using subset={subset}:")
    display(df.duplicated(subset=subset, keep='first').sum())


def run_script(script, stdin=None):
    """Returns (stdout, stderr), raises error on non-zero return code"""
    import subprocess

    # Note: by using a list here (['bash', ...]) you avoid quoting issues, as
    # the arguments are passed in exactly this order (spaces, quotes, and
    # newlines won't cause problems):
    proc = subprocess.Popen(['bash', '-c', script],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            stdin=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    if proc.returncode:
        raise ScriptException(proc.returncode, stdout, stderr, script)
    return stdout, stderr


def wait_for_file(file_path: Path,
                  time_to_wait: int = 5,
                  time_limit: int = 200) -> None:
    """
    Pauses application until a specified file exists or a time limit is reached.

    Args:
        file_path (Path): Path to check for existence
        time_to_wait (int, optional): Time in seconds to wait before checking
            again. Defaults to 5.
        time_limit (int, optional): Time in seconds to continue checking.
        Defaults to 200.

    Raises:
        FileExistsError: File does not exist
    """
    logger.info(f"Waiting for {file_path}")
    counter = 0
    while (not file_path.exists) and (counter < time_limit):
        time.sleep(time_to_wait)
        counter += time_to_wait
        if counter == time_limit:
            print("Time limit reached. Aborting")
            break
    if file_path.exists:
        logger.info(f"{file_path} exists.")
    else:
        raise FileExistsError


def convert_py_to_html(script_name: str,
                       output_name: str = None,
                       output_path: Path = None) -> IO:

    if output_path is None:
        output_path = Path(script_name).resolve()

    if output_name is None:
        output_name_stem = Path(script_name).stem

    logger.debug(f"output_path : {output_path}")
    logger.debug(f"output_name_stem : {output_name_stem}")

    notebook_ipynb = Path(output_path, Path(str(output_name_stem) + ".ipynb"))
    if Path(script_name).suffix == "":
        script_name = script_name + ".py"

    logger.debug("deleting old notebook")
    try:
        os.remove(notebook_ipynb)
        logger.debug(f"deleted {notebook_ipynb}")
    except FileNotFoundError:
        logger.debug(f"{notebook_ipynb} does not exist. Moving on.")

    logger.info("Converting .py to .ipynb")
    nb = jupytext.read(open(Path(os.getenv('PROJECT_ROOT'), script_name), 'r'))
    jupytext.write(nb, open(notebook_ipynb, 'w'), fmt='ipynb')

    logger.info("Executing and converting notebook to .html")
    cmd = f"{os.getenv('PROJECT_ROOT')}/.venv/bin/jupyter nbconvert {notebook_ipynb} --to html --execute --template classic"  # noqa ES01
    logger.debug("get_ipython(): Got IPython")
    logger.debug(f"cmd: {cmd}")
    process = subprocess.run(shlex.split(cmd),
                             stdout=subprocess.PIPE,
                             text=True)

    while True:
        output = process.stdout
        # print(output.strip())
        # Do something else
        return_code = process.returncode
        if return_code is not None:
            logger.debug(f'RETURN CODE : {return_code}')
            # Process has finished, read rest of the output
            for output in process.stdout:
                print(output.strip())

            if Path(output_path,
                    Path(str(output_name_stem) + ".html")).exists():
                print(
                    f"Converted {notebook_ipynb} to html: {datetime.now().replace(second=0, microsecond=0)}"  # noqa E501
                )
            break


@click.command("convert-to-html")
@click.option('-s',
              '--script-name',
              help='Name of .py script to convert',
              required=True)
@click.option('-on',
              '--output-name',
              help='Name of output files (no extension)')
@click.option('-op', '--output-path', help='Path to output destination')
def convert_py_to_html_command(script_name, output_name, output_path):
    convert_py_to_html(script_name, output_name, output_path)
