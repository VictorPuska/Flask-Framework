"""
Identification
    Module:     utils
    Author:     Victor Puska
    Written:    Feb 09, 2018
    Copyright:  (c) 2018 by VICTOR PUSKA.
    License:    LICENSE_NAME, see LICENSE_FILE for more details.

Description
    Authentication and authority management for the application.
"""

import urllib
from flask import Flask, url_for


def get_routes(app: Flask):
    """Return an array of tuples (endpoint, methods and url) listing the application routes"""
    rules = []
    args = {}
    for rule in app.url_map.iter_rules():
        for arg in rule.arguments:
            args[arg] = "[{0}]".format(arg)
        entry = (
            rule.endpoint, #endpoint
            ",".join(rule.methods), #methods
            urllib.parse.unquote(url_for(rule.endpoint,**args)) #url
        )
        rules.append(entry)
    return rules


def get_datetime_format():
    return ()