# %% # noqa: E902
# vscode-fold=2
"""Data processing classes and functions.

Example:
    Examples can be given using either the ``Example`` or ``Examples``
    sections. Sections support any reStructuredText formatting, including
    literal blocks::

        $ python example_google.py

Section breaks are created by resuming unindented text. Section breaks
are also implicitly created anytime a new section starts.

Attributes:
    module_level_variable1 (int): Module level variables may be documented in
        either the ``Attributes`` section of the module docstring, or in an
        inline docstring immediately following the variable.

        Either form is acceptable, but the two should not be mixed. Choose
        one convention to document module level variables and be consistent
        with it.

Todo:
    * For module TODOs
    * You have to also use ``sphinx.ext.todo`` extension

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import click
import numpy as np
import pandas as pd
from IPython.display import display
from pandas.core.frame import DataFrame
from traitlets.traitlets import Bool

from src import DB_ENGINE
from src.loggers import logging
from src.utils import quality_control

logger = logging.getLogger(__name__)


def display_quality_control(show: bool, df: pd.DataFrame, subset: list = None):
    if show is True:
        try:
            quality_control(df, subset)
        except AttributeError as e:
            print(e)


def build_project():
    # stuff here
    pass


@click.command("build-project")
def build_project_command():
    obj = build_project()
    click.echo(obj.data.head())


class Data:
    """A generic class to represent project data"""
    def __init__(self,
                 categoricals: dict = None,
                 ages: dict = None,
                 display_labels: dict = None,
                 schema: str = None,
                 show_quality_control: bool = False,
                 table_dicts: dict = None,
                 cached: bool = False,
                 first_study_date: datetime = None,
                 last_study_date: datetime = None,
                 *args: Any,
                 **kwargs: Any) -> object:
        """
        Creates a Data object

        Args:

        """
        logger.info(f"Instantiating {type(self)} object")
        # Non protected attributes for read/write data
        self.categoricals = categoricals
        self.ages = ages
        self.display_labels = display_labels
        self.show_qc = show_quality_control
        self.schema = schema
        self.table_dicts = table_dicts
        self.cached = cached
        self.first_study_date = first_study_date
        self.last_study_date = last_study_date
        # Protected attributes to store read-only data
        self.tables = self._get_tables(
            table_dicts=self.table_dicts,
            cached=self.cached,
        )
        self._data = self._build_data(*args, **kwargs)
        self._data = self._recode_categoricals(df=self._data,
                                               categoricals=self.categoricals)
        self._data = self._categorize_age(df=self._data, ages=self.ages)

        display_quality_control(self.show_qc, self._data, subset=['person_id'])
        self._long_data = self._melt_wide_data(self._data, *args, **kwargs)
        logger.debug("__init__ complete")

    # Use @property on a method whose name is exactly the name of the
    # restricted attribute but return the internal attribute instead
    @property
    def data(self):
        return self._data

    @property
    def long_data(self):
        return self._long_data

    def _get_tables(self, table_dicts: dict, cached: bool) -> pd.DataFrame:

        logger.info("Getting data tables")

        tables = {}
        # Create dict of tables
        for table, d in table_dicts.items():
            p = Path(os.getenv("PROCESSED_DATA"), table + '.pkl')
            if (cached is True) & (p.exists()):
                logger.info(f"Using cached tables for {table}")
                df = pd.read_pickle(p)
            else:
                logger.info(f"Using database table for {table}")
                column_dict = d.get('cols')
                logger.debug(f"column_dict: {column_dict}")
                dtype = d.get('dtype')
                logger.debug(f"dtype: {dtype}")
                df = self._read_sql_table(
                    table=table,
                    column_dict=column_dict,
                )
                df = df.rename(column_dict, axis=1)
                try:
                    df = df.astype(dtype=dtype)
                except (KeyError, TypeError):
                    pass
                df.to_pickle(p)
            tables.update({table: df})
        return tables

    def _build_data(self, *args, **kwargs) -> pd.DataFrame:
        logger.info('Building data')
        # Override in children to customize (most work done here)
        pass

    def _read_sql_table(self, table: str, column_dict: dict) -> DataFrame:
        logger.debug(f"Reading {self.schema}.{table}")
        columns = [k for k, _ in column_dict.items()]
        df = pd.read_sql_table(table_name=table,
                               schema=self.schema,
                               con=DB_ENGINE,
                               columns=columns)
        df = df.rename(column_dict, axis=1)
        return df

    def _recode_categoricals(self, df: pd.DataFrame,
                             categoricals: dict) -> pd.DataFrame:
        """Recodes category columns using a dict

        Args:
            df (pd.DataFrame): Pandas DataFrame with columns of category dtype
            categoricals (dict): Dictionary in the form
                                {<column_name_string>: {
                                    "unknowns": <unknown_category_string>,
                                    "others": <other_category_string>,
                                    "recodes": {<old_category>:<new_category>}
                                    }
                                }

        Returns:
            pd.DataFrame: DataFrame with specified category columns recoded
        """
        logger.info("Recoding categorical variables")
        if categoricals is None:
            return df
        else:
            for col, cats in categoricals.items():
                if col in list(df):
                    logger.debug(f"Recoding {col}")
                    logger.debug(f"Missing in {col}: {df[col].isna().sum()}")
                    logger.debug(f"Code for {col}:\n{cats}")
                    try:
                        df[col] = df[col].cat.add_categories(
                            [cats.get("unknowns")])
                    except (ValueError):
                        pass
                    try:
                        df[col] = df[col].cat.add_categories(
                            [cats.get("others")])
                    except (ValueError):
                        pass
                    df[col] = df[col].fillna(cats.get("unknowns"))
                    df[col] = df[col].replace(
                        cats.get("recodes")).astype("category")
                    df[col] = df[col].cat.remove_unused_categories()
                    logger.debug(f"Missing in {col}: {df[col].isna().sum()}")
                    logger.debug(
                        f"Categories in {col}: {list(df[col].cat.categories)}")
            return df

    def _categorize_age(self, df: pd.DataFrame, ages: dict) -> pd.DataFrame:
        """Bin age column into "age_group" column

        Args:
            df (pd.DataFrame): DataFrame with col to recode
            col (str): Name of age column

        Returns:
            pd.DataFrame: DataFrame with age_group column
        """
        age_col = ages.get('age_col')
        age_bins = ages.get("age_bins")
        age_labels = ages.get('age_labels')
        if age_col is None:
            return df
        else:
            logger.debug("Categorizing age into bins")
            df["age_group"] = pd.cut(df[age_col],
                                     bins=age_bins,
                                     labels=age_labels)
            return df

    def _melt_wide_data(self, df, *args, **kwargs):
        logger.info('Restructuring to long format')
        # Override in children to customize transformation to long data
        pass


class YourData(Data):
    """"Constructor specifically for YourData."""
    def __init__(self, *args: Any, **kwargs: Any) -> object:
        Data.__init__(self, *args, **kwargs)

    def _build_data(self, **kwargs) -> pd.DataFrame:
        logger.info('Building data')
        # Do stuff here
        pass
