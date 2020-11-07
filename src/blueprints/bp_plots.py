import logging
from flask import Blueprint
from flask import current_app as app
from flask import render_template

# from src.pages import demographics, enrollment, flu_status, quality, tables
# logger = logging.getLogger(__name__)

# bp_plots = Blueprint('bp_plots', __name__)

# @bp_plots.route('/<page>')
# @bp_plots.route('/<page>/<mail>')
# def show_plot_pages(page):
#     """"Renders content for plot pages"""
#     pages = []
#     fullViewPages = [
#         enrollment.create_layout(app),
#         flu_status.create_layout(app),
#         demographics.create_layout(app),
#         quality.create_layout(app),
#         tables.create_layout(app),
#     ]
#     if page == "email":
#         return render_template('content.html', pages=fullViewPages)
#     else:
#         if page == 'enrollment':
#             pages.append(enrollment.create_layout(app))
#         elif page == "flu-status":
#             pages.append(flu_status.create_layout(app))
#         elif page == "demographics":
#             pages.append(demographics.create_layout(app))
#         elif page == "quality":
#             pages.append(quality.create_layout(app))
#         elif page == 'tables':
#             pages.append(tables.create_layout(app))
#         elif page == "full-view":
#             pages = fullViewPages
#         return render_template('web.html', pages=pages)
