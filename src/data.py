import copy
import logging
from collections import OrderedDict
from io import StringIO
from pathlib import Path

import click
import numpy as np

import pandas as pd
import src.config as config
from bs4 import BeautifulSoup
from redcap import Project, RedcapError
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class RedcapProject(Project):
    def __init__(self,
                 url,
                 token,
                 name='',
                 md_fields=None,
                 md_forms=None,
                 event_filters=None,
                 df_kwargs={},
                 dtype_refinements=None,
                 bool_converters=None,
                 datetime_converters=None,
                 bool_checkboxes=None,
                 cat_checkboxes=None,
                 list_checkboxes=None,
                 recode_checkboxes=None,
                 update_categories=None,
                 drop_cases=None,
                 validation_cases=None):
        super().__init__(url, token, name, verify_ssl=False, lazy=True)
        self.md_fields = md_fields
        self.md_forms = md_forms
        self.event_filters = event_filters
        self.format = None
        self.df_kwargs = df_kwargs
        self.dtype_refinements = dtype_refinements
        self.bool_converters = bool_converters
        self.datetime_converters = datetime_converters
        self.bool_checkboxes = bool_checkboxes
        self.cat_checkboxes = cat_checkboxes
        self.list_checkboxes = list_checkboxes
        self.recode_checkboxes = recode_checkboxes
        self.drop_cases = drop_cases
        self.validation_cases = validation_cases
        self.update_categories = update_categories
        self.metadata = None
        self.allMetadata = None
        self.redcap_version = None
        self.field_names = None
        # We'll use the first field as the default id for each row
        self.def_field = None
        self.field_labels = None
        self.forms = None
        self.events = None
        self.arm_nums = None
        self.arm_names = None
        self.records = None
        self.data = None
        self.staffing = None
        self.teams = None
        self.errors = None

        try:
            self.metadata = self.export_metadata(fields=self.md_fields,
                                                 forms=self.md_forms,
                                                 format='json',
                                                 df_kwargs=None)
            self.allMetadata = copy.copy(super().export_metadata(format='df'))
        except RequestException:
            raise RedcapError(
                "Exporting metadata failed. Check your URL and token.")
        try:
            self.redcap_version = self._Project__rcv()
        except RequestException:
            raise RedcapError("Determination of REDCap version failed")
        self.field_names = self.filter_metadata('field_name')
        # we'll use the first field as the default id for each row
        self.def_field = self.field_names[0]
        self.field_labels = self.filter_metadata('field_label')
        self.forms = tuple(set(c['form_name'] for c in self.metadata))
        # determine whether longitudinal
        ev_data = self._call_api(self._Project__basepl('event'),
                                 'exp_event')[0]
        arm_data = self._call_api(self._Project__basepl('arm'), 'exp_arm')[0]
        if isinstance(ev_data, dict) and ('error' in ev_data.keys()):
            events = tuple([])
        else:
            events = ev_data

        if isinstance(arm_data, dict) and ('error' in arm_data.keys()):
            arm_nums = tuple([])
            arm_names = tuple([])
        else:
            arm_nums = tuple([a['arm_num'] for a in arm_data])
            arm_names = tuple([a['name'] for a in arm_data])
        self.events = events
        self.arm_nums = arm_nums
        self.arm_names = arm_names
        self.metadata = self.__strip_html(self.metadata)
        self.allMetadata = self.__strip_html(self.allMetadata)
        # Convert metadata to pd.DataFrame here
        self.metadata = self.__assign_field_dtype()
        self.__update_dtypes_for_df_kwargs()
        self.data_dictionary = self.data_dictionary()
        self.records = self.__get_records()
        self.records = self.__drop_records()
        self.records = self.__recode_matrix()
        self.records = self.__coerce_bools()
        self.records = self.__recode_checkboxes_to_cat()
        self.records = self.__convert_checkboxes_to_bool()
        self.records = self.__convert_checkboxes_to_list()
        self.records = self.__coerce_datetimes()
        self.records = self.__update_categories()

        self.configured = True

    def export_metadata(  # NOQA C901
            self,
            fields=None,
            forms=None,
            format='json',
            df_kwargs=None):
        """
            Export the project's metadata

            Parameters
            ----------
            fields : list
                Limit exported metadata to these fields
            forms : list
                Limit exported metadata to these forms
            format : (``'json'``), ``'csv'``, ``'xml'``, ``'df'``
                Return the metadata in native objects, csv or xml.
                ``'df'`` will return a ``pandas.DataFrame``.
            df_kwargs : dict
                Passed to ``pandas.read_csv`` to control construction of
                returned DataFrame.
                by default ``{'index_col': 'field_name'}``

            Returns
            -------
            metadata : list, str, ``pandas.DataFrame``
                metadata sttructure for the project.
            """
        ret_format = format
        if format == 'df':
            from pandas import read_csv
            ret_format = 'csv'
        pl = self._Project__basepl('metadata', format=ret_format)
        to_add = [fields, forms]
        str_add = ['fields', 'forms']
        for key, data in zip(str_add, to_add):
            if data:
                pl[key] = ','.join(data)
        response, _ = self._call_api(pl, 'metadata')
        filters = []
        if not forms:
            forms = []
        if not fields:
            fields = []
        for d in response:
            if (d['form_name'] in forms) | (d['field_name'] in fields):
                filters.append(d)
        response = filters
        if format in ('json', 'csv', 'xml'):
            return response
        elif format == 'df':
            if not df_kwargs:
                df_kwargs = {'index_col': 'field_name'}
            return read_csv(StringIO(response), **df_kwargs)

    def data_dictionary(self):
        return self.metadata[[
            'field_name',
            'field_label',
            'select_choices_or_calculations',
            'field_type',
            'dtype',
            'branching_logic',
            'text_validation_type_or_show_slider_number',
            'form_name',
        ]].set_index('field_name')

    def show_choices(self,
                     field: str,
                     metadata: pd.DataFrame = None,
                     sort: bool = False):
        """Prints select choice or calculations for a REDCap field"""
        if metadata is None:
            metadata = self.allMetadata
        if sort:
            options = sorted(
                metadata.loc[field,
                             'select_choices_or_calculations'].split(' | '))
            print(*options, sep=', \n')
        else:
            print(*metadata.loc[field,
                                'select_choices_or_calculations'].split(' | '),
                  sep=', \n')

    def __get_records(self):
        records = self.export_records(fields=self.field_names,
                                      raw_or_label='label',
                                      format='df',
                                      export_survey_fields=False,
                                      export_data_access_groups=False,
                                      df_kwargs=self.df_kwargs,
                                      export_checkbox_labels=False)

        filtered_records = pd.DataFrame()
        if 'redcap_event_name' in records.columns:
            for event in self.event_filters:
                filtered_records = filtered_records.append(
                    records.query(f"redcap_event_name == '{event}'"),
                    ignore_index=True)
        else:
            filtered_records = records
        return filtered_records

    def __drop_records(self):
        if self.drop_cases:
            for case in self.drop_cases:
                if len(self.records.query(case)) > 0:
                    self.records.drop(self.records.query(case).index,
                                      axis=0,
                                      inplace=True)
        return self.records

    def __assign_field_dtype(self):
        self.metadata = pd.DataFrame(self.metadata)
        self.metadata['dtype'] = np.nan
        self.metadata.loc[self.metadata['field_type'] == 'dropdown',
                          'dtype'] = 'string'
        self.metadata.loc[self.metadata['field_type'] == 'yesno',
                          'dtype'] = 'boolean'
        self.metadata.loc[self.metadata['field_type'] == 'radio',
                          'dtype'] = 'category'
        self.metadata.loc[self.metadata['field_type'] == 'notes',
                          'dtype'] = 'string'
        self.metadata.loc[self.metadata['field_type'] == 'text',
                          'dtype'] = 'string'
        self.metadata.loc[self.metadata['field_type'] == 'descriptive',
                          'dtype'] = 'string'
        self.metadata.loc[self.metadata['field_type'] == 'calc',
                          'dtype'] = 'string'
        self.metadata.loc[self.metadata['field_type'] == 'checkbox',
                          'dtype'] = 'category'
        # Refine text fields
        self.metadata.loc[
            self.metadata['text_validation_type_or_show_slider_number'] ==
            'integer', 'dtype'] = 'Int64'

        return self.metadata

    def __update_dtypes_for_df_kwargs(self):
        d = self.metadata[['field_name', 'dtype']].set_index('field_name')
        # datetime and bool need extra handling in pd.read_csv
        d = d.loc[d['dtype'] != 'datetime64[ns]']
        d = d.loc[d['dtype'] != 'boolean']
        d = d.to_dict(orient='dict')['dtype']
        self.df_kwargs.update({'dtype': d})
        self.df_kwargs['dtype'].update(self.dtype_refinements)

    def __strip_html(self, obj):
        if type(obj) == pd.core.frame.DataFrame:
            for c in obj.columns:
                try:
                    obj[c] = [
                        BeautifulSoup(text, features="html.parser").get_text()
                        for text in obj[c]
                    ]
                except TypeError:
                    pass
        else:
            for d in obj:
                for field in d.keys():
                    d[field] = BeautifulSoup(
                        d[field], features="html.parser").get_text()
        return obj

    def __coerce_bools(self):
        if self.bool_converters:
            self.records = self.records.replace(self.bool_converters)
            for k, _ in self.bool_converters.items():
                self.records[k] = self.records[k].astype('boolean')
        return self.records

    def __coerce_datetimes(self):
        if self.datetime_converters:
            for col, fmt in self.datetime_converters.items():
                self.records[col] = pd.to_datetime(self.records[col],
                                                   format=fmt,
                                                   errors='coerce')
        return self.records

    def __convert_checkboxes_to_bool(self):
        if self.bool_checkboxes:
            for targetCol, cols in self.bool_checkboxes.items():
                for c in cols:
                    self.records[c].replace(
                        {
                            'Checked': True,
                            'Unchecked': False
                        }, inplace=True)
                self.records[targetCol] = pd.NA
                self.records[targetCol] = self.records[cols].any(
                    axis='columns')
                self.records[targetCol] = self.records[targetCol].astype(
                    'boolean')
                for c in cols:
                    if c in self.records.columns.values:
                        self.records.drop(c, axis=1, inplace=True)
        return self.records

    def __convert_checkboxes_to_list(self):
        if self.list_checkboxes:
            for targetCol, cols in self.list_checkboxes.items():
                for c in cols:
                    self.records[c].replace(
                        {
                            'Checked': c.rsplit('___')[1],
                            'Unchecked': ""
                        },
                        inplace=True)
                self.records[targetCol] = pd.NA
                self.records.loc[
                    self.records['id'].notna(),
                    [targetCol]] = self.records.apply(
                        lambda x: self.records[cols].values.tolist())
                self.records.loc[
                    self.records[targetCol].notna(),
                    [targetCol]] = self.records[self.records[targetCol].notna(
                    )][targetCol].apply(lambda x: [i for i in x if i])
                for col in cols:
                    self.records.drop(col, axis=1, inplace=True)
        return self.records

    def __recode_checkboxes_to_cat(self):
        if self.recode_checkboxes:
            for targetCol, mapping in self.recode_checkboxes.items():
                for cat, cols in mapping.items():
                    for c in cols:
                        if c in self.records.columns.values:
                            self.records[c].replace(
                                {
                                    'Checked': True,
                                    'Unchecked': False
                                },
                                inplace=True)
                    self.records.loc[self.records[cols].any(axis="columns"),
                                     targetCol] = cat
                    for c in cols:
                        if c in self.records.columns.values:
                            self.records.drop(c, axis=1, inplace=True)
                # self.records.loc[self.records[targetCol].isna(),
                #                  [targetCol]] = pd.NA
                self.records[targetCol].replace(np.nan, pd.NA, inplace=True)
                self.records[targetCol] = self.records[targetCol].astype(
                    'category')
        return self.records

    def __update_categories(self):
        if self.update_categories:
            for targetCol, collection in self.update_categories.items():
                self.records[targetCol] = self.records[targetCol].astype(
                    'category')
                if type(collection) is tuple:
                    # make ordered categories
                    self.records[targetCol].cat.reorder_categories(
                        collection, ordered=True, inplace=True)
                elif type(collection) is dict:
                    # rename categories
                    self.records[targetCol].cat.rename_categories(collection,
                                                                  inplace=True)
                elif type(collection) is OrderedDict:
                    # rename and reorder categories
                    self.records[targetCol].cat.rename_categories(
                        dict(collection), inplace=True)
                    self.records[targetCol].cat.reorder_categories(
                        tuple(collection.values()), ordered=True, inplace=True)

        return self.records

    def __recode_matrix(self):
        mxNames = self.metadata['matrix_group_name'].replace(
            "", pd.NA).dropna().unique()
        if len(mxNames) > 0:
            for mxName in mxNames:
                for col in self.metadata[self.metadata['matrix_group_name'] ==
                                         mxName]['field_name'].unique():
                    if col in list(self.records):
                        self.records.rename(columns={col: f"{mxName}__{col}"},
                                            inplace=True)
        return self.records


class FluveProject():
    def __init__(
        self,
        name='',
        staffingProject: object = None,
        enrollmentProject: object = None,
    ):
        self.staffingProject = staffingProject
        self.staffingData = copy.copy(self.staffingProject.records)
        self.enrollmentProject = enrollmentProject
        self.enrollmentData = copy.copy(self.enrollmentProject.records)
        self.labData = self.__build_lab_data()
        self.records = None
        self.errors = None

        self.def_field = 'redcap_id'
        self.enrollmentData = self.__assign_teams()
        self.records = self.__merge_lab_data()

        # create_indicators
        self.records['screened'] = True
        self.records['screened'] = self.records['screened'].astype('boolean')
        self.records['eligible'] = pd.NA
        self.records['eligible'] = self.records['eligible'].astype('boolean')
        self.records.loc[((self.records['tooyoung'].fillna(False) == False) &
                          (self.records['illness'].fillna(False) == True) &
                          (self.records['days'].fillna(20) <= 7) &
                          (self.records['prior'].fillna("Yes") != "Yes") &
                          (self.records['flu_meds'].fillna(True) == False)),
                         ['eligible']] = True  # NOQA E712
        self.records.loc[((self.records['tooyoung'].fillna(False) == True) |
                          (self.records['illness'].fillna(False) == False) |
                          (self.records['days'].fillna(20) > 7) |
                          (self.records['prior'].fillna("Yes") == "Yes") |
                          (self.records['flu_meds'].fillna(True) == True)),
                         ['eligible']] = False  # NOQA E712
        self.records['enrolled'] = pd.NA
        self.records['enrolled'] = self.records['enrolled'].astype('boolean')
        self.records.loc[self.records['consent'] == 'Yes - signed consent',
                         ['enrolled']] = True

        # Check results
        validation_cases = [
            ("Test data in records",
             self.records.query("id.str.strip().str.lower() == 'test'")[[
                 self.def_field, 'id'
             ]].set_index(self.def_field)),
            ("Duplicates in records", self.records.dropna(
                subset=['id']).loc[self.records['id'].duplicated(keep=False)][[
                    self.def_field, 'id', 'scrnby'
                ]].set_index(self.def_field)),
            ("coll_by_oth is empty",
             self.records[self.records['coll_by_oth'].notna()][[
                 self.def_field, 'coll_by_oth'
             ]].set_index(self.def_field)),
            ("scrnby_oth is empty",
             self.records[self.records['scrnby_oth'].notna()][[
                 self.def_field, 'scrnby_oth'
             ]].set_index(self.def_field)),
            ("Missing age group",
             self.records[(self.records['enrolled'] == 1)
                          & (self.records['agegrp'] == '')][[
                              self.def_field, 'id', 'scrnby', 'agegrp'
                          ]].set_index(self.def_field)),
            ("Missing sex", self.records[(self.records['enrolled'] == 1)
                                         & (self.records['sex'] == '')][[
                                             self.def_field, 'id', 'scrnby',
                                             'sex'
                                         ]].set_index(self.def_field)),
            ("Missing swab", self.records[(self.records['enrolled'] == 1)
                                          & (self.records['swabs'] == '')][[
                                              self.def_field, 'id', 'scrnby',
                                              'swabs'
                                          ]].set_index(self.def_field)),
            ("Missing education",
             self.records[(self.records['enrolled'] == 1)
                          & (self.records['education'] == '')][[
                              self.def_field, 'id', 'scrnby', 'education'
                          ]].set_index(self.def_field)),
            ("Wrong swabs", self.records.loc[
                (self.records['enrolled'].fillna(False) == True)
                & (self.records['scrndt_tm'] > '2020-03-15 00:00:00')
                & (self.records['swabs'] != 'Nasal only'),
                ['id', 'redcap_id', 'scrndt_tm', 'coll_by', 'swabs']].
             set_index(self.def_field)),
            ("Ineligible participants enrolled", self.records[
                (self.records['enrolled'].fillna(False) == True)
                & (self.records['eligible'].fillna(False) == False)
                & (~self.records[self.def_field].isin([1143, 1781, 1617]))][[
                    self.def_field, 'eligible', 'enrolled', 'clinic', 'scrnby'
                ]].set_index(self.def_field)),  # NOQA E712
            ("Additional REDCap events exist", self.records[
                self.records['redcap_event_name'] != 'Event 1'].set_index(
                    self.def_field)),
            ("Ids without prefix exist.",
             self.records.dropna(subset=['id']).loc[~self.records.dropna(
                 subset=['id'])['id'].str.startswith('PA')][[
                     self.def_field, 'id', 'scrnby'
                 ]].set_index(self.def_field)),
            ("Staff with expired certifications",
             self.staffingData[self.staffingData[[
                 'certification_blood', 'certification_privacy',
                 'certification_rcr', 'certification_human_subj'
             ]].lt(pd.Timestamp.today()).any(axis=1)][[
                 'name', 'certification_blood', 'certification_privacy',
                 'certification_rcr', 'certification_human_subj'
             ]].set_index('name')),
            ("Staff missing certifications",
             self.staffingData[self.staffingData[[
                 'certification_blood', 'certification_privacy',
                 'certification_rcr', 'certification_human_subj'
             ]].isna().any(axis=1)][[
                 'name', 'certification_blood', 'certification_privacy',
                 'certification_rcr', 'certification_human_subj'
             ]].set_index('name')),
        ]
        self.errors = self.validate_data(validation_cases=validation_cases)

        # Final cleanup
        self.records.drop([
            'redcap_event_name', 'consent_ser', 'scrnby_oth', 'bornprior',
            'tooyoung', 'days', 'flu_meds', 'prior', 'coll_by_oth'
        ],
                          axis=1,
                          inplace=True)

    def __build_lab_data(self):
        labDataSource = Path(config.rawData /
                             "2019-20 CDC Flu VE Results.xlsx")

        cols = [
            'Subject ID', 'RNP 1', 'RNP 1 Ct', 'RNP 2', 'RNP 2 Ct', 'RNP 3',
            'RNP 3 Ct', 'Flu A 1', 'Flu A 1 Ct', 'Flu A 2', 'Flu A 2 Ct',
            'Flu A 3', 'Flu A 3 Ct', 'H3', 'H3 Ct', 'pdmA', 'pdmA Ct', 'pdmH1',
            'pdmH1 Ct', 'Flu B 1', 'Flu B 1 Ct', 'Flu B 2', 'Flu B 2 Ct',
            'Flu B 3', 'Flu B 3 Ct', 'B VIC', 'B VIC Ct', 'B YAM', 'B YAM Ct',
            'Comments'
        ]
        df = pd.read_excel(
            labDataSource, usecols=cols, index_column=None,
            na_values=pd.NA).rename(columns={'Subject ID': 'id'})
        df = df[df['id'].notna()]
        # Check for duplicates
        condition = df[df.duplicated(subset='id')]
        assert len(
            condition) == 0, f"Duplicate id values \n {print(condition)}."

        # compute_lab_results
        ctCols = [c for c in list(df) if c.endswith('Ct')]

        df['gt30Ct'] = pd.NA
        mask = df[ctCols].gt(30).any(axis='columns')
        df.loc[mask, ['gt30Ct']] = True

        df['highCt'] = pd.NA
        mask = df[ctCols].gt(37).any(axis='columns')
        df.loc[mask, ['highCt']] = True

        df['avgCt'] = df[ctCols].mean(axis=1)
        # generate strain indicators
        strains = {
            'RNP 1': 'rnaPos',
            'Flu A 1': 'fluApos',
            'H3': 'h3pos',
            'pdmA': 'pdmApos',
            'pdmH1': 'pdmH1pos',
            'Flu B 1': 'fluBpos',
            'B VIC': 'bVicPos',
            'B YAM': 'bYamPos'
        }

        for k, v in strains.items():
            df[v] = df[k]
            df.loc[df[k] == 1, [v]] = True
            df.loc[df[k] == 0, [v]] = False
            df.loc[df[k].notna() & (df[k] != 1) & (df[k] != 0), [v]] = False
            df[v] = df[v].astype('boolean')

        cols = ['id', 'gt30Ct', 'highCt', 'avgCt'] + list(strains.values())
        df['id'] = df['id'].astype('string')
        df['gt30Ct'] = df['gt30Ct'].astype('boolean')
        df['highCt'] = df['highCt'].astype('boolean')
        df['avgCt'] = df['avgCt'].fillna(np.nan).astype('float')
        df = df[cols]
        return df

    def __merge_lab_data(self):
        self.labData = self.labData.set_index('id')
        for c in list(self.labData):
            from pandas.api.types import is_numeric_dtype
            if is_numeric_dtype(self.labData[c]):
                self.enrollmentData[c] = np.nan
            else:
                self.enrollmentData[c] = pd.NA
            self.enrollmentData[c] = self.enrollmentData[c].astype(
                self.labData[c].dtype)
        self.enrollmentData = self.enrollmentData.set_index('id')
        dtypes = dict(self.enrollmentData.dtypes)
        self.enrollmentData.update(self.labData)
        self.enrollmentData = self.enrollmentData.astype(dtypes)
        self.enrollmentData = self.enrollmentData.reset_index()
        self.enrollmentData['id'] = self.enrollmentData['id'].astype('string')
        return self.enrollmentData

    def __assign_teams(self):
        teams = self.staffingData[['name',
                                   'team']].set_index("name").sort_index()
        teams = teams.to_dict(orient='dict')['team']
        self.enrollmentData['team'] = self.enrollmentData['scrnby'].map(
            teams).astype('string')
        return self.enrollmentData

    def validate_data(self, validation_cases):
        errors = {}
        if not validation_cases:
            validation_cases = [
                ("Check for duplicates", self.records.dropna(
                    subset=['id']).loc[self.records['id'].duplicated(
                        keep=False)][[self.def_field,
                                      'id']].set_index(self.def_field)),
                ("Check for extra REDCap events",
                 self.records[~self.records['redcap_event_name'].
                              isin(self.event_filters)].set_index(
                                  self.def_field)),
            ],
            for tpl in validation_cases:
                for msg, case in tpl:
                    if len(case) > 0:
                        logger.warning(f"""Failed: {msg}\n\n{case}\n""")
                        errors[msg] = case
                    else:
                        logger.info(f"""Passed: {msg}""")
        else:
            for msg, case in validation_cases:
                if len(case) > 0:
                    logger.warning(f"""Failed: {msg}\n\n{case}\n""")
                    errors[msg] = case
                else:
                    logger.info(f"""Passed: {msg}""")

        return errors


def build_project():
    # TODO: This should become a json or yml config
    staffingProject = RedcapProject(
        url=config.redcapApiUrl,
        token=config.redcapApiFluVeStaffingKey,
        name='staffing',
        md_fields=[
            'record_id', 'active', 'name', 'email_new_hire', 'study',
            'study___1', 'study___2', 'team', 'start_date', 'end_date',
            'training_rsvp', 'phone_mobile', 'email_pitt', 'upmc_email',
            'upmc_sign_in', 'upmc_myapps', 'upmc_badge', 'vincent_training',
            'vincent_access', 'vincent_cards', 'redcap_access',
            'account_hsconnect', 'certification_blood',
            'certification_privacy', 'certification_rcr',
            'certification_human_subj', 'training_study', 'training_swab',
            'training_protocol', 'cert_warn'
        ],
        # md_forms=[],
        # event_filters=['Event 1'],
        dtype_refinements={
            'name': 'string',
            'email_new_hire': 'string',
            'study___1': 'string',
            'study___2': 'string',
            'team': 'string',
            'training_rsvp': 'category',
            'email_pitt': 'string',
            'upmc_email': 'string',
            'upmc_badge': 'string',
            'active': 'boolean',
            'phone_mobile': 'string',
        },
        df_kwargs={
            'na_values': pd.NA,

            # 'converters': {}
        },
        bool_converters={
            'upmc_sign_in': {
                'Yes': True,
                'No': False
            },
            'upmc_myapps': {
                'Yes': True,
                'No': False
            },
            'vincent_training': {
                'Yes': True,
                'No': False
            },
            'vincent_access': {
                'Yes': True,
                'No': False
            },
            'vincent_cards': {
                'Yes': True,
                'No': False
            },
            'redcap_access': {
                'Yes': True,
                'No': False
            },
            'account_hsconnect': {
                'Yes': True,
                'No': False
            },
            'training_protocol': {
                'Yes': True,
                'No': False
            },
            'cert_warn': {
                'Yes': True,
                'No': False
            },
        },
        datetime_converters={
            'start_date': '%Y-%m-%d',
            'end_date': '%Y-%m-%d',
            'certification_blood': '%Y-%m-%d',
            'certification_privacy': '%Y-%m-%d',
            'certification_rcr': '%Y-%m-%d',
            'certification_human_subj': '%Y-%m-%d',
            'training_study': '%Y-%m-%d',
            'training_swab': '%Y-%m-%d',
        },
        recode_checkboxes={
            'study': {
                "FluVE": ['study___1'],
                "HAIVEN": ['study___2']
            },
        },

        # drop_cases is inverted
        # drop_cases=["active == False"]
    )

    enrollmentProject = RedcapProject(
        url=config.redcapApiUrl,
        token=config.redcapApiFluVeEnrollmentKey,
        name='enrollment',
        md_fields=[
            'redcap_id', 'redcap_event_name', 'clinic', 'scrndt', 'scrntm',
            'scrnby', 'scrnby_oth', 'sex', 'agegrp', 'p_zip', 'fluvx',
            'education', 'race', 'hispanic', 'tooyoung', 'agree', 'illness',
            'days', 'bornprior', 'flu_meds', 'prior', 'consent',
            'consent_spec', 'consent_ser', 'id', 'coll_by', 'coll_by_oth',
            'swabs', 'withdraw', 'fevercov', 'chillscov', 'coughcov',
            'sore_throcov', 'sobcov', 'runny_nosecov', 'achescov',
            'abdompaincov', 'vom_nauscov', 'diarrheacov', 'headachecov'
        ],
        # md_forms=['screening_and_enroll'],
        event_filters=['Event 1'],
        dtype_refinements={
            'scrndt': 'object',
            'scrntm': 'object',
            'redcap_id': 'Int64',
            'days': 'Int64',
            'id': 'string',
            'fluvx': 'category',
        },
        drop_cases=[
            "id.str.strip().str.lower() == 'test'", "scrndt_tm == 'nan nan'"
        ],
        bool_converters={
            'hispanic': {
                "Don't know": pd.NA,
                'No': False,
                'Refused': pd.NA,
                'Yes': True
            },
            'tooyoung': {
                'Yes': True,
                'No': False
            },
            'illness': {
                'Yes': True,
                'No': False
            },
            'agree': {
                'Yes': True,
                'No': False
            },
            'flu_meds': {
                'Yes': True,
                'No': False
            },
            'bornprior': {
                'Yes': True,
                'No': False
            },
        },
        bool_checkboxes={
            'withdrew': [
                'withdraw___wdrwnospec', 'withdraw___wdrwinterest',
                'withdraw___wdrwtime', 'withdraw___wdrwrecd',
                'withdraw___wdrwother'
            ]
        },
        recode_checkboxes={
            'race': {
                "white": ['race___white'],
                "black": ['race___black'],
                "other": [
                    "race___amerind",
                    'race___asian',
                    'race___nativehi',
                    'race___raceoth',
                    'race___unk',
                    'race___raceref',
                ],
            },
        },
        update_categories={
            'agegrp':
            OrderedDict([('', '< 6 mo'), ('6 months to 4 years', '6 mo-4 y'),
                         ('5 to 9 years', '5-9 y'),
                         ('10 to 17 years', '10-17 y'),
                         ('18 to 49 years', '18-49 y'),
                         ('50 to 64 years', '50-64 y'),
                         ('65 years or older', '> 65 y')]),
            'education':
            OrderedDict([
                ('Less than high school graduate', 'Less than HS'),
                ('Graduated high school (or obtained GED)', 'Graduated HS'),
                ("Some college (including vocational training, associate's degree)",
                 "Some college"),
                ("Bachelor's degree", "Bachelor's degree"),
                ('Advanced degree', 'Advanced degree'),
                ("Don't know", "Don't know"),
                ('Refused', 'Refused'),
            ]),
        },
        datetime_converters={'scrndt_tm': None},
        df_kwargs={
            'parse_dates': {
                'scrndt_tm': ['scrndt', 'scrntm']
            },
            'converters': {
                'id':
                lambda x: pd.NA if (x == '') else x.upper(),
                'agegrp':
                lambda x: x.replace(
                    " <font color=blue> <i> (Birthdate before 03/01/2019) </i> </font>",  # NOQA E501
                    ''),
            }
        })

    fluveProject = FluveProject(staffingProject=staffingProject,
                                enrollmentProject=enrollmentProject)
    return fluveProject


@click.command('build-project')
def build_project_command():
    obj = build_project()
    click.echo(obj.data.head())
