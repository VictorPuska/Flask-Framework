"""
Identification
    Module:     core.py
    Author:     Victor Puska
    Written:    Feb 06, 2018
    Copyright:  (c) 2018 by VICTOR PUSKA.
    License:    LICENSE_NAME, see LICENSE_FILE for more details.

Description
    Authentication and authority management for the application.
"""
from flask import Flask, Blueprint
from flask_login import LoginManager
from flask_migrate import Migrate
from . database import db, User


login_manager = LoginManager()
blueprint = Blueprint('core', __name__,
                      template_folder="templates",
                      static_url_path="/static/core",
                      static_folder="static")



@login_manager.user_loader
def load_user(id):
    return User.query.get(id)

def init_core(app: Flask):
    app.register_blueprint(blueprint)
    db.init_app(app)
    Migrate(app, db)
    login_manager.init_app(app)



