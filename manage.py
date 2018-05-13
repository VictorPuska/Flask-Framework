"""
Identification
    Module:     manage.py
    Author:     Victor Puska
    Written:    Jan 22, 2018
    Copyright:  (c) 2018 by VICTOR PUSKA.
    License:    LICENSE_NAME, see LICENSE_FILE for more details.

Description
    Authentication and authority management for the application.
"""

import click
import flask.cli
from flask import Flask
from core import blueprint, db, User

app: Flask = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')
app.register_blueprint(blueprint)
db.init_app(app)



def create_my_app(info):
    return app


@click.group(cls=flask.cli.FlaskGroup, create_app=create_my_app)
def cli():
    """This is a management script for the Flask3 application."""
    pass


if __name__ == '__main__':
    cli()
