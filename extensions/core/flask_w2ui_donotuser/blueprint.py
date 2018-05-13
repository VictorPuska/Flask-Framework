"""
Identification
    Module:     flask_w2ui.blueprint
    Author:     Victor Puska
    Written:    Jul 23, 2017
    Copyright:  (c) 2017 by VICTOR PUSKA.
    License:    LICENSE_NAME, see LICENSE_FILE for more details.

Description
    Authentication and authority management for the application.
"""
from flask import Blueprint, render_template, Flask
from .grid import W2GridView
from flask_sql import select


def register_static_files(application: Flask):
    bp = Blueprint('w2ui', __name__, template_folder='templates', static_folder='static' )
    application.register_blueprint(bp, url_prefix='/flask_w2ui')


def table_editor_blueprint(application: Flask, url_prefix='/tables'):
    table_view = W2GridView.as_view('edit', editable=True)
    bp = Blueprint('sql', __name__, template_folder='templates')
    bp.add_url_rule('/', view_func=show_tables, methods=['GET'])
    bp.add_url_rule('/<table>', view_func=table_view, methods=['GET','POST'])
    application.register_blueprint(bp, url_prefix=url_prefix)


def show_tables():
    tables = []
    for row in select("SHOW TABLES"):
        tables.append(list(row.values())[0])
    return render_template("tables.html", tables=tables)
