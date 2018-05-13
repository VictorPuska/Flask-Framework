"""
Identification
    Module:     models
    Author:     Victor Puska
    Written:    Jan 10, 2018
    Copyright:  (c) 2018 by VICTOR PUSKA.
    License:    LICENSE_NAME, see LICENSE_FILE for more details.

Description
    Authentication and authority management for the application.
"""

import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Session, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from werkzeug.local import LocalProxy
from sqlalchemy import inspect
from w2ui.definitions import W2Column


db = SQLAlchemy()


def sess():
    return db.session


session: Session = LocalProxy(sess)


class UserBase(db.Model, UserMixin):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    code = Column(String(20), unique=True, nullable=False)
    password = Column(String(128))
    email = Column(String(100))
    active = Column(Boolean, default=True)
    type = Column(String(8), default="User")
    created = Column(DateTime, default=datetime.datetime.now())
    lastaccess = Column(DateTime)

    def is_superuser(self):
        return self.type == "SUPER"

    def is_adminuser(self):
        return (self.type == "SUPER") or (self.type == "ADMIN")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        if self.password is None:
            return password == "hamish"
        else:
            return check_password_hash(self.password, password)


W2Column.set_defaults(UserBase.name, caption="User Name", size=155)
W2Column.set_defaults(UserBase.email, caption="Email Address", search_caption="Email")


class MyUserClass(UserBase):
    __tablename__ = UserBase.__tablename__
    __table_args__ = {'extend_existing': True}

    items = relationship("Items", back_populates="user")


User = MyUserClass


class Items(db.Model):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    userid = Column(Integer, ForeignKey('user.id'))

    user = relationship("MyUserClass", back_populates="items")

