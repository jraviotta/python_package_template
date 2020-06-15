from fluve.utils import build_dataframe_row, build_plot_row


def create_layout(app):
    subtitle = "Quality Assurance"
    rows = []
    rows.append(
        build_plot_row(
            title="Swab quality by team",
            plotMethod=app.plots.plot_enrollment_ctXteam(),
            caption="""
                    <p>This chart shows the quality of specimens collected by
                    team. The protocol states that specimens with a Ct value
                    <40 are considered valid, however, when the CDC lab does
                    repeat testing for inconclusive specimens, a
                    cut-off of Ct 37 is typically used.</p>
                    <l>
                    <li>("Unacceptable Ct > 37"),</li>
                    <li>("Marginal Ct 30-37"),</li>
                    <li>("Ideal Ct < 30"),</li>
                    </l>""",
            colClass="twelve columns",
        ))
    rows.append(
        build_plot_row(
            title="Swab quality of enrollments by RA",
            plotMethod=app.plots.plot_enrollment_ctXra(),
            caption="""
                        This chart shows the proportion of enrollments in each
                        category of CT quality.""",
            colClass="twelve columns",
        ))

    return (subtitle, rows)
