"""
Identification
    Module:     config.py
    Author:     Victor Puska
    Written:    Dec 31, 2017
    Copyright:  (c) 2017 by VICTOR PUSKA.
    License:    LICENSE_NAME, see LICENSE_FILE for more details.

Description
    Authentication and authority management for the application.
"""

DB_CONN_STRING = "c:/users/vjp/documents/programming/flask2/db/flask2.db"

DB_PARAMS = {'user': 'victor',
             'password': 'hamish',
             'host': 'palermo',
             'database': 'devdb',
             'raise_on_warnings': True, }

SECRET_KEY = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://victor:hamish@palermo/devdb"
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = False

SERVER_NAME = '127.0.0.1:5000'
