import copy
import logging

import click
import pandas as pd  # NOQA (F401)
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot

logger = logging.getLogger(__name__)


def build_plots(proj=None):
    if proj is None:
        proj = build_fluve_project()
    plots = FluPlots(proj)
    return plots


@click.command('build-plots')
def build_plots_command():
    """Calculates and saves plots."""
    build_plots()


class FluPlots():
    def __init__(self, fluProject):
        self.data = copy.copy(fluProject.records)
        self.margins = dict(l=5, r=5, b=5, t=5, pad=4)  # NOQA (E741)
        # remove unused categories
        for col in self.data.select_dtypes(include=['category']):
            self.data[col].cat.remove_unused_categories(inplace=True)
        # make booleans integers
        for col in self.data.select_dtypes(include=['boolean']):
            self.data[col] = self.data[col].fillna(False)
            self.data[col] = self.data[col].fillna(False).replace({
                True: 1,
                False: 0
            })

    def enrollmentTable(self, **kwargs):
        if not kwargs:
            kwargs = {}
            kwargs['group'] = 'ra'

        if kwargs['group'] == 'ra':
            kwargs['group'] = 'scrnby'
            group = 'ra'
        else:
            group = kwargs['group']
        tbl = self._build_table(**kwargs)[[
            kwargs['group'], 'screened', 'agree', 'eligible', 'enrolled',
            'withdrew', 'agreePct', 'enrollPct', 'conversionPct', 'withdrewPct'
        ]]
        return tbl.rename(columns={'scrnby': 'ra'}).set_index(group)

    def swabTable(self, **kwargs):
        if not kwargs:
            kwargs = {}
            kwargs['group'] = 'ra'

        if kwargs['group'] == 'ra':
            kwargs['group'] = 'coll_by'
            group = 'ra'
        else:
            group = kwargs['group']

        tbl = self._build_table(**kwargs)[[
            kwargs['group'], 'enrolled', 'gt30Ct', 'highCt', 'avgCt',
            'highCtPct', 'gt30CtPct', 'fluApos', 'h3pos', 'pdmApos',
            'pdmH1pos', 'fluBpos', 'bVicPos', 'bYamPos'
        ]]
        return tbl.rename(columns={
            'coll_by': 'ra',
            'enrolled': 'swabbed'
        }).set_index(group)

    def plot_enrollment_demographics(self,
                                     enrolled: bool = True,
                                     demo: str = None,
                                     color: str = None,
                                     barmode: str = 'stack',
                                     showlegend: bool = True):
        plotData = self.data[[
            'id', 'scrndt_tm', 'clinic', 'scrnby', 'consent', 'sex', 'agegrp',
            'hispanic', 'race', 'education', 'fluvx', 'p_zip', 'team',
            'enrolled', 'withdrew'
        ]].rename(columns={'scrnby': 'ra'})
        if enrolled:
            plotData = plotData.dropna()
            plotData = plotData[(plotData['enrolled'] == 1)
                                & (plotData['withdrew'] == 0)]
        else:
            plotData = plotData[(plotData['enrolled'] == 0)]
            plotData = plotData.dropna(subset=['consent', 'sex', 'agegrp'])
        # remove unused categories
        for col in plotData.select_dtypes(include=['category']):
            plotData[col].cat.remove_unused_categories(inplace=True)
        fig = px.histogram(data_frame=plotData, x=demo, color=color)
        if color:
            fig.for_each_trace(lambda t: t.update(name=t.name.replace(
                "1", color).replace("0", "Not " + color)))

        try:
            if plotData[demo].dtype == 'category':
                fig.update_layout(
                    xaxis={
                        'categoryorder': 'array',
                        'categoryarray': plotData[demo].cat.categories,
                        'tickangle': 30,
                    })
        except TypeError:
            pass
        if showlegend is False:
            fig.update_layout(showlegend=False)
        fig.update_yaxes(title_text=None, automargin=True)
        fig.update_xaxes(title_text=None, automargin=True)
        fig.update_layout(margin=self.margins, barmode=barmode)

        return plot(
            fig,
            show_link=False,
            output_type='div',
            include_plotlyjs=False,
        )

    def plot_flu_results_by_clinic(self, color=None):
        plotData = self.data[[
            'id', 'scrndt_tm', 'clinic', 'scrnby', 'sex', 'agegrp', 'team',
            'fluvx', 'avgCt', 'fluApos', 'h3pos', 'pdmApos', 'pdmH1pos',
            'fluBpos', 'bVicPos', 'bYamPos'
        ]].rename(columns={'scrnby': 'ra'})
        strains = ['fluApos', 'fluBpos']
        plotData[strains] = plotData[strains].fillna(False).replace({
            True: 1,
            False: 0
        })
        plotData = plotData.melt(id_vars=[
            'id', 'scrndt_tm', 'clinic', 'ra', 'sex', 'agegrp', 'team', 'fluvx'
        ],
                                 value_vars=strains)
        # Filter for positives
        plotData = plotData.query("value==1").dropna()
        fig = px.histogram(data_frame=plotData,
                           x='clinic',
                           y='value',
                           labels={
                               'variable': 'Strain',
                               'value': ""
                           },
                           color='variable',
                           barmode='group')
        fig.update_yaxes(title_text=None, automargin=True)
        fig.update_xaxes(automargin=True)
        fig.update_layout(margin=self.margins)
        return plot(
            fig,
            show_link=False,
            output_type='div',
            include_plotlyjs=False,
        )

    def plot_flu_results_by_strain(self, color=None):
        plotData = self.data[[
            'id', 'scrndt_tm', 'clinic', 'scrnby', 'sex', 'agegrp', 'team',
            'fluvx', 'avgCt', 'fluApos', 'h3pos', 'pdmApos', 'pdmH1pos',
            'fluBpos', 'bVicPos', 'bYamPos'
        ]].rename(columns={'scrnby': 'ra'})
        strains = [
            'fluApos', 'fluBpos', 'h3pos', 'pdmApos', 'pdmH1pos', 'bVicPos',
            'bYamPos'
        ]
        plotData[strains] = plotData[strains].fillna(False).replace({
            True: 1,
            False: 0
        })
        plotData = plotData.melt(id_vars=[
            'id', 'scrndt_tm', 'clinic', 'ra', 'sex', 'agegrp', 'team', 'fluvx'
        ],
                                 value_vars=strains)
        # Filter for positives
        plotData = plotData.query("value==1").dropna()
        fig = px.histogram(
            data_frame=plotData,
            x='variable',
            y='value',
            labels={
                'variable': 'Strain',
                'value': ""
            },
            color=color,
        )
        fig.update_layout(margin=self.margins)
        return plot(
            fig,
            show_link=False,
            output_type='div',
            include_plotlyjs=False,
        )

    def plot_enrollment_ctXteam(self):
        plotData = self.data[['team', 'coll_by', 'avgCt',
                              'swabs']].dropna().sort_values(['team', 'avgCt'])

        df = plotData[plotData['swabs'] != "None"]
        df['swabs'].cat.remove_unused_categories()
        fig = px.box(
            df,
            x='team',
            y='avgCt',
            # color="swabs",
            boxmode="group",
        )
        fig.update_layout(margin=self.margins)
        return plot(
            fig,
            show_link=False,
            output_type='div',
            include_plotlyjs=False,
        )

    def plot_enrollment_ctXra(self):
        group = 'ra'
        plotData = self.swabTable(group=group).reset_index()[[
            group, 'swabbed', 'gt30Ct', 'highCt', 'gt30CtPct'
        ]].sort_values(by=['swabbed', 'gt30CtPct'], ascending=False)
        order = plotData[group]

        fig = go.Figure(data=[
            go.Bar(name='CT < 30',
                   x=order,
                   y=plotData['swabbed'],
                   marker_color='green'),
            go.Bar(name='CT 30-37',
                   x=order,
                   y=plotData['gt30Ct'],
                   marker_color='yellow'),
            go.Bar(name='CT > 37',
                   x=order,
                   y=plotData['highCt'],
                   marker_color='red')
        ])

        fig.update_layout(
            barmode='stack',
            margin=self.margins,
        )
        return plot(
            fig,
            show_link=False,
            output_type='div',
            include_plotlyjs=False,
        )

    def plot_enrollment_conversions(self, group=None):
        if group is None:
            group = 'ra'
        plotData = self.enrollmentTable(group=group).reset_index()[[
            group, 'screened', 'agree', 'eligible', 'enrolled'
        ]].sort_values(by=['screened'], ascending=False)
        order = plotData[group]

        fig = go.Figure(data=[
            go.Bar(
                name='Screened',
                x=order,
                y=plotData['screened'],
            ),
            go.Bar(
                name='Agree',
                x=order,
                y=plotData['agree'],
            ),
            go.Bar(
                name='Eligible',
                x=order,
                y=plotData['eligible'],
            ),
            go.Bar(
                name='Enrolled',
                x=order,
                y=plotData['enrolled'],
            )
        ])

        fig.update_layout(
            barmode='group',
            margin=self.margins,
        )

        return plot(
            fig,
            show_link=False,
            output_type='div',
            include_plotlyjs=False,
        )

    def plot_enrollment_by_time(self, cumulative=False):
        plotData = self.data[[
            'scrndt_tm', 'screened', 'agree', 'eligible', 'enrolled',
            'fluApos', 'fluBpos'
        ]]
        plotData[[
            'screened', 'agree', 'eligible', 'enrolled', 'fluApos', 'fluBpos'
        ]] = plotData[[
            'screened', 'agree', 'eligible', 'enrolled', 'fluApos', 'fluBpos'
        ]].fillna(False).replace({
            True: 1,
            False: 0
        })
        if cumulative:
            plotData = plotData.set_index('scrndt_tm').resample('D').sum()
            plotData[['sumFluA', 'sumFluB']] = plotData[['fluApos',
                                                         'fluBpos']].cumsum()
            plotData.reset_index(inplace=True)
            fig = px.histogram(
                data_frame=plotData.melt(id_vars=['scrndt_tm'],
                                         value_vars=[
                                             'screened',
                                             'agree',
                                             'eligible',
                                             'enrolled',
                                         ]).dropna(),
                x='scrndt_tm',
                y='value',
                color='variable',
                cumulative=True,
                histfunc='sum',
                barmode='overlay',
            )
            plotData['target'] = 1500

            fig.add_trace(
                go.Scatter(y=plotData['target'],
                           x=plotData['scrndt_tm'],
                           mode='lines',
                           name='Target enrollment'))
            fig.add_trace(
                go.Scatter(y=plotData['sumFluA'],
                           x=plotData['scrndt_tm'],
                           mode='lines',
                           name='Flu A cases'))
            fig.add_trace(
                go.Scatter(y=plotData['sumFluB'],
                           x=plotData['scrndt_tm'],
                           mode='lines',
                           name='Flu B cases'))

        else:
            plotData = plotData.set_index('scrndt_tm').resample(
                'W').sum().reset_index()
            plotData = plotData.melt(
                id_vars=['scrndt_tm'],
                value_vars=['screened', 'enrolled', 'fluApos', 'fluBpos'])
            fig = px.line(data_frame=plotData,
                          x='scrndt_tm',
                          y='value',
                          color='variable')

        fig.update_yaxes(title_text=None, automargin=True)
        fig.update_xaxes(title_text=None, automargin=True)
        fig.update_layout(margin=self.margins)
        return plot(
            fig,
            show_link=False,
            output_type='div',
            include_plotlyjs=False,
        )

    def _append_totals(self, df, aggfunc):
        if aggfunc == 'sum':
            func = df.sum().round(2)
        elif aggfunc == 'mean':
            func = df.mean().round(2)
        try:
            df.loc['Total'] = func
        except TypeError:
            df.index = df.index.add_categories('Total')
            df.loc['Total'] = func
        return df

    def _build_table(  # NOQA (C901)
            self,
            group: str,
            data: pd.DataFrame = None,
            margins: bool = False,
            **kwargs):
        if not data:
            data = copy.copy(self.data)

        logger.info(f"Aggregating enrolment by: {group}")
        aggfuncs = {
            'screened': 'sum',
            'agree': 'sum',
            'eligible': 'sum',
            'enrolled': 'sum',
            'withdrew': 'sum',
            'highCt': 'sum',
            'gt30Ct': 'sum',
            'fluApos': 'sum',
            'h3pos': 'sum',
            'pdmApos': 'sum',
            'pdmH1pos': 'sum',
            'fluBpos': 'sum',
            'bVicPos': 'sum',
            'bYamPos': 'sum',
            'avgCt': 'mean'
        }

        # agg chokes on pd.NA. must set missing value here
        for c in list(data.select_dtypes(include='boolean')):
            data[c].fillna(False, inplace=True)
        tbl = data.groupby(group).agg(aggfuncs)
        tbl['agreePct'] = (tbl['agree'] / tbl['screened'] * 100).round(2)
        tbl['enrollPct'] = (tbl['enrolled'] / tbl['eligible'] * 100).round(2)
        tbl['conversionPct'] = tbl[['agreePct',
                                    'enrollPct']].mean(axis=1).round(2)
        tbl['withdrewPct'] = (tbl['withdrew'] / tbl['enrolled'] * 100).round(2)
        tbl['gt30CtPct'] = (tbl['gt30Ct'] / tbl['enrolled'] * 100).round(2)
        tbl['highCtPct'] = (tbl['highCt'] / tbl['enrolled'] * 100).round(2)
        tbl['avgCt'] = tbl['avgCt'].round(2)
        tbl = tbl.reset_index()

        if margins:
            tbl = tbl.set_index(group)
            try:
                tbl.index = tbl.index.add_categories('Total')
            except AttributeError:
                pass
            mask = [c for c in list(tbl) if (not c.endswith('Pct'))]
            for c in ['ra', 'avgCt', 'team']:
                try:
                    mask.remove(c)
                except ValueError:
                    pass

            tbl.loc['Total', mask] = tbl.sum()
            try:
                mask = [c for c in list(tbl) if c.endswith('Pct')] + ['avgCt']
                tbl.loc['Total', mask] = tbl.mean().round(2)

            except KeyError:
                mask = [c for c in list(tbl) if c.endswith('Pct')]
                tbl.loc['Total', mask] = tbl.mean().round(2)

        return tbl.reset_index()
