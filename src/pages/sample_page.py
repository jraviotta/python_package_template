from src.utils import build_plot_row, build_dataframe_row


def create_layout(app):
    subtitle = "Demographics"
    rows = []
    rows.append(
        build_plot_row(
            title="Participants by sex",
            caption=None,
            plotMethod=app.plots.plot_enrollment_demographics(demo='sex'),
            colClass='four columns'))
    rows.append(
        build_dataframe_row(title='Other resons for refusal',
                            caption=None,
                            df=app.plots.data[['consent_spec']].dropna(),
                            colClass='six columns'))
    return (subtitle, rows)
