"""
Identification
    Module:     research.py
    Author:     Victor Puska
    Written:    Jan 09, 2018
    Copyright:  (c) 2018 by VICTOR PUSKA.
    License:    LICENSE_NAME, see LICENSE_FILE for more details.

Description
    Authentication and authority management for the application.
"""
from flask import Flask
from sqlalchemy import MetaData,or_
from sqlalchemy.sql.base import ImmutableColumnCollection
from sqlalchemy.sql.schema import Column
from core.database import User, session, UserBase, db, Items
from core import init_core
from sqlalchemy.sql.operators import eq, ilike_op, gt, ge, between_op, contains_op
from sqlalchemy.sql import select, table, Select
from sqlalchemy.util._collections import immutabledict
from sqlalchemy.schema import Column
app: Flask = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')
init_core(app)

def test1():

    with app.app_context():
        #m: MetaData = User.metadata
        cols: ImmutableColumnCollection = User.__table__.columns
        q = session.query(User, Items)
        #q = q.filter(ilike_op(cols['name'], "%puska"))
        #q = q.filter(between_op(cols['id'], 1, 5))
        f = []
        f.append(ilike_op(cols['name'], "%puska"))
        f.append(between_op(cols['id'], 1, 5))
        q = q.filter(or_(*f))
        print("STATEMENT=", q.statement)

        conn = db.engine.connect()
        print(conn)

        t = User.__table__
        s: Select = select([t])
        s = s.where(t.c["id"] > 0)
        s = s.where(ilike_op(t.c["code"], "v%"))
        result = conn.execute(s)
        for r in result:
            print(r)
        result.close()
        conn.close()


def test2(**kwargs):
    print(kwargs)
    fred = kwargs.pop('fred', None)
    kwargs['bill'] = "billy boy"
    print(kwargs)


def test3():
    with app.app_context():
        cols: ImmutableColumnCollection = User.__table__.columns

        q = session.query(Items)
        print(q.statement)
        for r in q.all():
            print(r)
            print(r.user.code)

def test4():
    with app.app_context():
        print(User.name.key)
        tbl = User.__table__
        stmt = tbl.update().where(User.id==3).values({User.code.key:"Fred2"})
        print(stmt)
        session.execute(stmt)
        session.commit()

def test5():
    with app.app_context():
        u = User()
        setattr(u, User.code.key, "Test3")
        u.name = "Test User"
        session.add(u)
        session.commit()
        print(getattr(u,"id"))

test5()