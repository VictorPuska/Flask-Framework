"""
Identification
    Module:     grid.py
    Author:     Victor Puska
    Written:    Feb 13, 2018
    Copyright:  (c) 2018 by VICTOR PUSKA.
    License:    LICENSE_NAME, see LICENSE_FILE for more details.

Description
    Authentication and authority management for the application.
"""

import json

from typing import List, Dict

from flask import render_template, url_for, session, request, jsonify, g, Response, current_app, Flask
from flask.views import MethodView

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.operators import eq, ilike_op, gt, ge, between_op, or_, and_, contains_op

from . database import session, User
from . core import blueprint
from w2ui.definitions import W2Column


class UserView:
    edits = dict(type='combo', filter=False, items=[' ', 'ADMIN', 'SUPER'])

    id = W2Column(User.id, type='int')
    code = W2Column(User.code, editable=True, operator='contains')
    name = W2Column(User.name, editable=True, operator='contains')
    email = W2Column(User.email, editable=True, operator='contains', size=100)
    active = W2Column(User.active, editable=True, caption="Active")
    type = W2Column(User.type, editable=edits, searchable=True, operator='is')
    created = W2Column(User.created, editable={'type': 'datetime'})
    lastaccess = W2Column(User.lastaccess, editable=True, render='datetime')

    __tablename__ = "Users"


class W2GridView(MethodView):

    def __init__(self, **kwargs):
        self.view = kwargs.pop('view')
        self.editable = kwargs.pop('editable', False)
        assert len(kwargs) == 0, "Unrecognized params to W2GridView: %s" % ", ".join(kwargs.keys())
        self.w2columns = {}     # W2Column's for view
        self.primarycol = None  # W2Column of primary column
        self.model = None       # The primary database table model
        self.query = None       # Database query
        self.colspec = []       # w2ui grid column parameter
        self.searchspec = []    # w2ui grid search paramter
        self.recid = None       # w2ui grid rec_id field
        # Copy W2Column attributes from view class into our W2GridView object instance...
        for attr in self.view.__dict__:
            obj = getattr(self.view, attr)
            if isinstance(obj, W2Column):
                self.w2columns[attr] = obj
                if self.primarycol is None:
                    self.primarycol = obj
                    self.model = obj.model_column.class_
                    self.recid = attr
        # build the query
        qry_fields = []
        for c in self.w2columns.values():
            if c.model_column is not None:
                qry_fields.append(c.model_column)
        self.query = session.query(*qry_fields)
        # Buile w2ui grid column and search parameters...
        for field, w2col in self.w2columns.items():
            self.colspec.append(w2col.column_spec(field))
            if w2col.has_search_specs:
               self.searchspec.append(w2col.search_spec(field))

    def get(self):

        return render_template("grid.html",
                               rec_id=self.recid,
                               url=request.url,
                               cols=self.colspec,
                               searches=self.searchspec,
                               table=self.view.__tablename__
                               )

    def post(self):
        w2req = json.loads(request.form['request'])
        w2cmd: str = w2req.get('cmd', None)
        if w2cmd == 'get':
            return self.list(w2req)
        elif w2cmd == 'save':
            return self.save(w2req)
        elif w2cmd == 'delete':
            return self.delete(w2req)

    def delete(self, w2req):
        rowids = w2req.get('selected', None)
        try:
            for rowid in rowids:
                if rowid > 0:
                    dbrec = session.query(self.model).filter(self.primarycol.model_column == rowid).first()
                    if dbrec is not None:
                        session.delete(dbrec)
            session.commit()
            return jsonify(dict(status="success"))
        except SQLAlchemyError as e:
            session.rollback()
            return jsonify(dict(status="error", message=str(e)))

    def save(self, w2req):
        w2changes: List = w2req.get('changes', None)
        pkey = self.primarycol.model_column
        model = self.primarycol.model_column.class_
        updates = []
        try:
            for row in w2changes:
                recid = row['recid']
                if recid < 0:
                    record = model()
                else:
                    record = session.query(model).filter(pkey == recid).first()
                for k, v in row.items():
                    if k != 'recid':
                        w2c = self.w2columns[k]
                        setattr(record, w2c.model_column.key, v)
                if recid < 0:
                    session.add(record)
                    session.flush()
                    newid = getattr(record, pkey.key)
                    updated_row = self.query.filter(pkey == newid).first()
                else:
                    updated_row = self.query.filter(pkey == recid).first()
                updates.append(dict(recid=recid, record=self.row_as_dict(updated_row)))
            session.commit()
            return jsonify(dict(status="success", updates=updates))
        except SQLAlchemyError as e:
            session.rollback()
            return jsonify(dict(status="error", message=str(e)))

    def list(self, w2req):
        w2selected: List = w2req.get('selected', None)
        w2limit: int = w2req.get('limit', None)
        w2offset: int = w2req.get('search', None)
        w2search: List[dict] = w2req.get('search', None)
        w2searchlogic = and_ if w2req.get('searchLogic', None) == "AND" else or_

        qry_fields = []
        for c in self.w2columns.values():
            if c.model_column is not None:
                qry_fields.append(c.model_column)

        q = self.query
        if w2search is not None:
            fltr = None
            for d in w2search:
                column = self.w2columns[d['field']]
                condition = column.filter(d['operator'], d['value'])
                fltr = condition if fltr is None else w2searchlogic(fltr, condition)
            q = q.filter(fltr)

        rows = []
        for datarow in q.all():
            rows.append(self.row_as_dict(datarow))

        return jsonify(dict(status='success', total=len(rows), records=rows))

    def row_as_dict(self, query_row):
        # Convert a row in a query result to a dictionary
        row = {}
        j = 0
        for fieldname, w2col in self.w2columns.items():
            row[fieldname] = w2col.handler.to_json(query_row[j])
            j += 1
        return row

blueprint.add_url_rule('/users',
                       view_func=W2GridView.as_view('edit', view=UserView, editable=True),
                       methods=['GET','POST'])
