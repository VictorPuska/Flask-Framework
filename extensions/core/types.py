"""
Identification
    Module:     types
    Author:     Victor Puska
    Written:    Feb 26, 2018
    Copyright:  (c) 2018 by VICTOR PUSKA.
    License:    LICENSE_NAME, see LICENSE_FILE for more details.

Description
    Authentication and authority management for the application.
"""


from typing import Dict
from datetime import date, datetime, time
from sqlalchemy.sql.base import ImmutableColumnCollection
from sqlalchemy.sql.sqltypes import Integer, String, DateTime
from sqlalchemy.sql.operators import eq, ilike_op, gt, ge, between_op, or_, and_
from sqlalchemy.schema import Column
from sqlalchemy.orm import Query


W2COLUMN_ATTRIBUTES = [
    'caption',  # '',
    'field',  # '',     // field name to map column to a record
    'size',  # null,   // size of column in px or %
    'min',  # 15,     // minimum width of column in px
    'max',  # null,   // maximum width of column in px
    'gridMinWidth',  # null,   // minimum width of the grid when column is visible
    'sizeCorrected',  # null,   // read only, corrected size (see explanation below)
    'sizeCalculated',  # null,   // read only, size in px (see explanation below)
    'hidden',  # false,  // indicates if column is hidden
    'sortable',  # false,  // indicates if column is sortable
    'searchable',  # false,  // indicates if column is searchable, bool/string# int,float,date,...
    'resizable',  # true,   // indicates if column is resizable
    'hideable',  # true,   // indicates if column can be hidden
    'attr',  # '',     // string that will be inside the <td ... attr> tag
    'style',  # '',     // additional style for the td tag
    'render',  # null,   // string or render function
    'title',  # null,   // string or function for the title property for the column cells
    'editable',  # {},     // editable object if column fields are editable
    'frozen',  # false,  // indicates if the column is fixed to the left
    'info',  # null    // info bubble, can be bool/object
]

W2SEARCH_ATTRIBUTES = [
    'type',  # 'text',    // type of the search (see below)
    'field',  # '',        // field name to submit to server
    'caption',  # '',        // caption of the search
    'inTag',  # '',        // text that will be inside <input ...> tag
    'outTag',  # '',        // text that will be outside <input ...> tag
    # 'hidden',        # false,     // indicates if search is show or hidden
    'nosearch'  # replacement for 'hidden' so it can be independent of column attribute
    'options',  # {}         // options for w2field object
]

W2ATTRIBUTE_MAP = {
    'nosearch': 'hidden',
}


class W2Field(object):

    def __init__(self, field, **kwargs):
        self.field = field                             # field name to map column to a record
        self.options = dict(caption=field)
        kwargs.setdefault('size', 40)
        self.set_options(**kwargs)

    def set_options(self, **kwargs):
        """
        self.caption        = kwargs.pop('caption', self.field) # column caption
        self.size           = kwargs.pop('size', 20)            # size of column in px or %
        self.min            = kwargs.pop('min', 15)             # minimum width of column in px
        self.max            = kwargs.pop('max', None)           # maximum width of column in px
        self.gridMinWidth   = kwargs.pop('gridMinWidth', None)  # minimum width of the grid when column is visible
        self.hidden         = kwargs.pop('hidden', False)       # indicates if column is hidden
        self.sortable       = kwargs.pop('sortable', False)     # indicates if column is sortable
        self.searchable     = kwargs.pop('searchable', False)   # indicates if column is searchable,
                                                                # bool/string# int,float,date,...
        self.resizable      = kwargs.pop('resizable', True)     # indicates if column is resizable
        self.hideable       = kwargs.pop('hideable', True)      # indicates if column can be hidden
        self.attr           = kwargs.pop('attr', '')            # string that will be inside the <td ... attr> tag
        self.style          = kwargs.pop('style', '')           # additional style for the td tag
        self.render         = kwargs.pop('render', None)        # string or render function
        self.title          = kwargs.pop('title', None)         # string or function for the title property
                                                                # for the column cells
        self.editable       = kwargs.pop('editable', {})        # editable object if column fields are editable
        self.frozen         = kwargs.pop('frozen', False)       # if the column is fixed to the left
        self.info           = kwargs.pop('info', None)          # info bubble, can be bool/object
        self.nosearch       = kwargs.pop('nosearch', False)     # not searchable flag
        """
        for k, v in kwargs.items():
            assert k in W2COLUMN_ATTRIBUTES + W2SEARCH_ATTRIBUTES, "Invalid keyword parameter:" + k
            self.options[k] = v

    @staticmethod
    def get_from_model_column(model_column: Column, **kwargs) -> 'W2Field':
        """For a given model column, return a W2Field object.  If there is a W2Field object saved
        in the column's info attribute, that object will be returned, otherwise a new W2Field object
        will be created.

            :param model_column:    The SQLAlchecmy model column
            :param kwargs:          W2Field options to override the default
        """
        w2f = model_column.info.get("w2", W2Field.model_column_default(model_column))
        w2f.set_options(**kwargs)

    @staticmethod
    def set_defaults(model_column: Column, **kwargs):
        # validate keyword arguments
        valid_keys = W2COLUMN_ATTRIBUTES + W2SEARCH_ATTRIBUTES
        for k in kwargs.keys():
            assert k in valid_keys, "Invalid keyword parameter:" + k
        model_column.info['w2'] = kwargs

    @staticmethod
    def for_model_column(model_column: Column, **kwargs) -> 'W2Field':
        """For a given model column, return a W2Field object.

            :param model_column:    The SQLAlchecmy model column
            :param kwargs:          W2Field options to override the default
        """
        t = model_column.type
        f = model_column.name
        default = model_column.info.get('w2', {})
        if type(t) is Integer:
            w2field = W2Integer(f, **default)
        elif type(t) is String:
            default.setdefault('size', min(t.length * 4, 150))
            w2field = W2String(f, **default)
        elif type(t) is DateTime:
            w2field = W2DateTime(f, **default)
        else:
            w2field = W2Field(f, **default)
        w2field.set_options(**kwargs)
        return w2field

    def grid_column_option(self, **kwargs):
        opts = dict(field=self.field)
        for (k, v) in self.options.items():
            if k in W2COLUMN_ATTRIBUTES:
                opts[k] = v
        for (k, v) in kwargs.items():
            assert k in W2COLUMN_ATTRIBUTES, "Invalid keyword parameter:" + k
            opts[k] = v
        return opts

class W2Integer(W2Field):

    def __init__(self, field, **kwargs):
        kwargs.setdefault('size', 8)
        W2Field.__init__(self, field, **kwargs)


class W2String(W2Field):

    def __init__(self, field, **kwargs):
        kwargs.setdefault('size', 150)
        W2Field.__init__(self, field, **kwargs)


class W2DateTime(W2Field):

    def __init__(self, field, **kwargs):
        kwargs.setdefault('size', 150)
        W2Field.__init__(self, field, **kwargs)


def w2makeoptions(model_column: Column, **kwargs):
    t = model_column.type
    if type(t) is Integer:
        w2field = W2Integer(model_column, **kwargs)
    elif type(t) is String:
        w2field = W2String(model_column, **kwargs)
    elif type(t) is DateTime:
        w2field = W2DateTime(model_column, **kwargs)
    else:
        w2field = W2Field(model_column, **kwargs)
    return w2field



def w2getoptions(model_column: Column) -> W2Field:
    return model_column.info.get('w2', w2makeoptions(model_column))



