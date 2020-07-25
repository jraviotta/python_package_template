import pandas as pd
from flask import Markup


def Header(app):
    return html.Div([get_header(app), html.Br([]), get_menu()])


def get_header(app):
    header = html.Div(
        [
            html.Div(
                [
                    html.Img(
                        src=app.get_asset_url("PittVax-Logo.png"),
                        className="logo",
                    ),
                    html.A(
                        html.Button("Learn More", id="learn-more-button"),
                        href="http://pittvax.pitt.edu/",
                    ),
                ],
                className="row",
            ),
            html.Div(
                [
                    html.Div(
                        [html.H5("US FluVE Network - Pittsburgh")],
                        className="seven columns main-title",
                    ),
                    html.Div(
                        [
                            dcc.Link(
                                "Full View",
                                href="/fluve/full-view",
                                className="full-view-link",
                            )
                        ],
                        className="five columns",
                    ),
                ],
                className="twelve columns",
                style={"padding-left": "0"},
            ),
        ],
        className="row",
    )
    return header


def get_menu():
    menu = html.Div(
        [
            dcc.Link(
                "Overview",
                href="/fluve/overview",
                className="tab first",
            ),
            dcc.Link(
                "Demographics",
                href='/fluve/demographics',
                className='tab',
            ),
            dcc.Link(
                "QA",
                href="/fluve/quality",
                className="tab",
            ),
            dcc.Link(
                "Tables",
                href="/fluve/tables",
                className="tab",
            ),
        ],
        className="row all-tabs",
    )
    return menu


def build_dataframe_row(title: str,
                        caption: str = None,
                        df: pd.DataFrame = None,
                        colClass: str = 'twelve columns'):
    if caption is not None:
        caption = Markup(caption)
    return (title, caption, Markup(df.to_html()), colClass)


def build_plot_row(title: str,
                   caption: str = None,
                   plotMethod=None,
                   colClass: str = 'twelve columns'):
    if caption is not None:
        caption = Markup(caption)
    return (title, caption, Markup(plotMethod), colClass)
