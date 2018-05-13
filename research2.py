"""
Identification
    Module:     research2
    Author:     Victor Puska
    Written:    Mar 20, 2018
    Copyright:  (c) 2018 by VICTOR PUSKA.
    License:    LICENSE_NAME, see LICENSE_FILE for more details.

Description
    Authentication and authority management for the application.
"""

import datetime
from dateutil import parser

from w2ui.definitions import *
from core.database import User, Items

s = '11/03/2018 2:00 pm'
d = datetime.datetime.strptime(s, "%d/%m/%Y %I:%M %p")
print(d)
