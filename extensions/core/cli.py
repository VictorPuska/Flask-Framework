"""
Identification
    Module:     cli
    Author:     Victor Puska
    Written:    Jan 28, 2018
    Copyright:  (c) 2018 by VICTOR PUSKA.
    License:    LICENSE_NAME, see LICENSE_FILE for more details.

Description
    Authentication and authority management for the application.
"""

import click
from flask import current_app, url_for, Flask
from flask.cli import FlaskGroup
from . database import db, User, session
from . util import get_routes


core_cli: FlaskGroup = FlaskGroup()


@core_cli.group("core")
def core_cli_group():
    """Basic core commands"""
    pass


@core_cli_group.command()
@click.argument("usercode")
@click.argument("name")
@click.password_option("--password")
def adduser(usercode, name, password):
    """Create the initial superuser"""
    try:
        u = User(code=usercode, name=name, active=True, type='SUPER')
        u.set_password(password)
        session.add(u)
        session.commit()
        click.echo("Super user created.")
    except Exception as e:
        click.echo("{0}".format(e.args[0]))
        session.rollback()

@core_cli_group.command()
@click.confirmation_option("--noprompt",
                           prompt="Are you sure you want to initialise the database?",
                           help="Suppresses confirmation prompt")
def initdb():
    """Initialise the database, create empty tables"""
    db.drop_all()
    db.create_all()
    click.echo("Database initialised.")


@core_cli_group.command()
def routes():
    """Show application routes."""
    rules = get_routes(current_app)
    w_endpoint = w_methods = w_url = 10
    for endpoint, methods, url in rules:
        w_endpoint = max(w_endpoint, len(endpoint))
        w_methods = max(w_methods, len(methods))
        w_url = max(w_url, len(url))
    widths = {'x': w_endpoint, 'y': w_methods, 'z': w_url }
    dashes = ("-" * w_endpoint, "-" * w_methods, "-" * w_url )
    print(" -{0:{x}}---{1:{y}}---{2:{z}}- ".format(*dashes, **widths))
    print("| {0:{x}} | {1:{y}} | {2:{z}} |".format(" ENDPOINT", " METHODS", " URL", **widths))
    print("|-{0:{x}}-|-{1:{y}}-|-{2:{z}}-|".format(*dashes, **widths))
    for rule in rules:
        print("| {0:{x}} | {1:{y}} | {2:{z}} |".format(*rule, **widths))
    print(" -{0:{x}}---{1:{y}}---{2:{z}}- ".format(*dashes, **widths))


@core_cli_group.command()
def listusers():
    app: Flask = current_app
    with app.app_context():
        print(User.query.all())