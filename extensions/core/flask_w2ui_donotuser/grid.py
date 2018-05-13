"""
Identification
    Module:     grid
    Author:     Victor Puska
    Written:    Jul 19, 2017
    Copyright:  (c) 2017 by VICTOR PUSKA.
    License:    LICENSE_NAME, see LICENSE_FILE for more details.

Description
    Authentication and authority management for the application.
"""

from threading import Lock
from typing import List, Dict
from flask import render_template, url_for, session, request, jsonify, g, Response, current_app, Flask
from flask.views import MethodView
from flask.json import JSONEncoder
import json
import flask_sql as sql
import calendar
from datetime import datetime, date
from .fieldtypes import *


_lock = Lock()


class W2JSONEncoder(JSONEncoder):

    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                if obj.utcoffset() is not None:
                    obj: datetime = obj - obj.utcoffset()
                millis = int(
                    calendar.timegm(obj.timetuple()) * 1000 +
                    obj.microsecond / 1000
                )
                #return millis
                return obj.strftime("%d/%m/%Y %I:%M %p" )
            if isinstance(obj, date):
                return obj.strftime("%d/%m/%Y")
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


class W2GridView(MethodView):

    def __init__(self, **kwargs):
        print(kwargs)
        if 'table' in kwargs:
            self.table = kwargs['table']
            self.metadata = self.get_sql_table_metadata(self.table)
            self.columns = self.metadata.columns
        self.editable = kwargs.get('editable', True)

    def get(self, **kwargs):
        print("GET")
        self.__init__(**kwargs)
        cols = []
        for f in self.columns.values():
            cols.append(f.column_options())
        if not self.editable:
            for c in cols:
                if 'editable' in c:
                    del c['editable']

        searches = []
        for f in self.columns.values():
            srch = f.search_options()
            if srch:
                searches.append(srch)

        toolbar = [
            {'type': 'break'},
            {'type': 'button', 'id': 'mybutton', 'caption': 'Add', 'img': 'icon-add'}
        ]

        return render_template("grid.html",
                               rec_id=self.metadata.rec_id,
                               url=request.url,
                               cols=cols,
                               searches=searches,
                               toolbar=toolbar,
                               table=self.table
                               )

    def post(self, **kwargs):
        self.__init__(**kwargs)
        w2req = json.loads(request.form['request'])
        w2cmd: str = w2req.get('cmd', None)
        if w2cmd == 'get':
            return self.list(w2req, w2cmd)
        elif w2cmd == 'save':
            return self.save(w2req, w2cmd)

    def delete(self, user_id):
        # delete a single user
        pass

    def put(self, user_id):
        # update a single user
        pass

    def save(self, w2req, w2cmd: str):
        w2changes: List = w2req.get('changes', None)
        print("Changes=", w2changes)
        return jsonify({"status": "success"})

    def list(self, w2req, w2cmd: str):
        w2selected: List = w2req.get('selected', None)
        w2limit: int = w2req.get('limit', None)
        w2offset: int = w2req.get('search', None)
        w2search: List[dict] = w2req.get('search', None)
        w2searchlogic: str = w2req.get('searchLogic', None)

        if w2search:
            print("= Search =")
            for item in w2search:
                print(item)

        where_str = ""
        where_args = []

        if w2search is not None:
            where_and_or = "WHERE"
            for srch in w2search:
                fldname = srch.get('field', None)
                column = self.columns[fldname]
                rslt = column.search_condition(**srch)
                if rslt:
                    where_str += " {0} {1}".format(where_and_or, rslt.where_clause)
                    where_args.append(rslt.value1)
                    where_and_or = w2searchlogic
                    if rslt.value2:
                        where_args.append(rslt.value2)

        where_args = tuple(where_args)
        stmt = "SELECT * FROM {0} {1}".format(self.table, where_str)
        cursor = sql.select(stmt, *where_args)
        print(cursor.statement)
        data = cursor.fetchall()
        response = {
            'status': 'success',
            'total': len(data),
            'records': data
        }
        app: Flask = current_app
        enc = app.json_encoder
        app.json_encoder = W2JSONEncoder
        resp: Response = jsonify(response)
        app.json_encoder = enc
        #print(resp.data)
        return resp

    def get_sql_table_metadata(self, tablename: str) -> W2TableMetadata:
        curs = sql.select("select * from information_schema.columns where table_name=%s", tablename)
        columns: Dict[str, W2Field] = {}
        rec_id = None
        for row in curs.fetchall():
            w2metadata = W2ColumnMetadata(**row)
            w2fieldobj = w2metadata.make_w2field()
            w2fieldobj.metadata = w2metadata
            columns[w2fieldobj.w2_field] = w2fieldobj
            if w2metadata.column_key == "PRI" and w2metadata.extra == "auto_increment":
                rec_id = w2metadata.column
        return W2TableMetadata(tablename, rec_id, columns)
