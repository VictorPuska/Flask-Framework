"""
Identification
    Module:     views.py
    Author:     Victor Puska
    Written:    Jan 19, 2018
    Copyright:  (c) 2018 by VICTOR PUSKA.
    License:    LICENSE_NAME, see LICENSE_FILE for more details.

Description
    Authentication and authority management for the application.
"""
import sys
import urllib

from flask import render_template, redirect, flash, url_for, current_app
from flask_login import current_user, login_user, logout_user, login_required
from flask_wtf import FlaskForm

from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

from . database import User, session, db
from . import blueprint


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


@blueprint.route("/")
def index():
    output = []
    for rule in current_app.url_map.iter_rules():
        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)
        obj = {
            'endpoint': rule.endpoint,
            'methods': ','.join(rule.methods),
            'url': urllib.parse.unquote(url_for(rule.endpoint, **options))
        }
        output.append(obj)
    users = []
    for u in session.query(User).all():
        current = current_user
        if current.is_authenticated:
            u.is_current = (current.id == u.id)
        else:
            u.is_current = False
        users.append(u)
    return render_template('index.html ', pypath=sys.path, urlmap=output, users=users, user=current)

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(code=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('.login'))
        if current_user.is_authenticated:
            logout_user()
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('.index'))
    else:
        return render_template('login.html', title='Sign In', form=form)

@blueprint.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for(".logged_out"))

@blueprint.route("/loggedout")
def logged_out():
    return render_template('logout.html')

@blueprint.route("/diagnostics")
def diagnostics():
    output = []
    for rule in current_app.url_map.iter_rules():
        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)
        obj = {
            'endpoint': rule.endpoint,
            'methods': ','.join(rule.methods),
            'url': urllib.parse.unquote(url_for(rule.endpoint, **options))
        }
        output.append(obj)
    return render_template('diagnostics.html', urlmap=output, user=current_user)