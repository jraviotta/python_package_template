from src.utils import build_dataframe_row


def create_layout(app):
    subtitle = 'Data Summary'
    rows = []
    rows.append(
        build_dataframe_row(title='Enrollment summary by Clnic',
                            caption=None,
                            df=app.plots.enrollmentTable(group='clinic',
                                                         margins=True),
                            colClass='twelve columns'))

    return (subtitle, rows)
