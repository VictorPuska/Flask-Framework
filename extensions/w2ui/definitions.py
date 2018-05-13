"""
Identification
    Module:     definitions.py
    Author:     Victor Puska
    Written:    Mar 20, 2018
    Copyright:  (c) 2018 by VICTOR PUSKA.
    License:    LICENSE_NAME, see LICENSE_FILE for more details.

Description
    Authentication and authority management for the application.
"""
import datetime
from typing import Dict, Type
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.sqltypes import Integer, String, DateTime, Boolean
from sqlalchemy.schema import Column
from sqlalchemy.sql.operators import eq, gt, lt, between_op, startswith_op, endswith_op, contains_op


class W2TypeHandler(object):

    #column_defaults = {}
    #search_defaults = {}

    @staticmethod
    def for_model(model_column: Column) -> Type['W2GenericHandler']:
        T = type(model_column.type)
        if T is String:
            return W2StringHandler
        elif T is Integer:
            return W2IntegerHandler
        elif T is DateTime:
            return W2DateTimeHandler
        elif T is Boolean:
            return W2BooleanHandler
        else:
            return W2GenericHandler

    @classmethod
    def prepare_search_value(cls, value):
        return value

    @classmethod
    def search_operator_is(cls, model_column: Column, value):
        return eq(model_column, value)

    @classmethod
    def search_operator_less(cls, model_column: Column, value):
        return lt(model_column, value)

    @classmethod
    def search_operator_more(cls, model_column: Column, value):
        return gt(model_column, value)

    @classmethod
    def search_operator_between(cls, model_column: Column, value):
        return between_op(model_column, value[0], value[1])

    @classmethod
    def to_json(cls, value):
        return value

    @classmethod
    def from_json(cls, value):
        return value

    @classmethod
    def edit_options(cls):
        return {}


class W2GenericHandler(W2TypeHandler):

    @classmethod
    def column_defaults(cls, model_column: Column):
        return dict(size=50, caption=model_column.name)


class W2StringHandler(W2GenericHandler):

    @classmethod
    def column_defaults(cls, model_column: Column):
        return dict(size=model_column.type.length * 4, caption=model_column.name, type='text')

    @classmethod
    def search_operator_begins(cls, model_column: Column, value):
        return startswith_op(model_column, value)

    @classmethod
    def search_operator_ends(cls, model_column: Column, value):
        return endswith_op(model_column, value)

    @classmethod
    def search_operator_contains(cls, model_column: Column, value):
        return contains_op(model_column, value)

    @classmethod
    def edit_options(cls):
        return dict(type='text')


class W2IntegerHandler(W2GenericHandler):

    @classmethod
    def column_defaults(cls, model_column: Column):
        return dict(size=32, caption=model_column.name)


class W2DateTimeHandler(W2GenericHandler):

    @classmethod
    def column_defaults(cls, model_column: Column):
        return dict(size=50, caption=model_column.name)

    @classmethod
    def to_json(cls, value):
        return value.strftime("%d/%m/%Y %I:%M %p") if value is not None else None

    @classmethod
    def from_json(cls, value):
        return datetime.datetime.strptime(value, "%d/%m/%Y %I:%M %p")

    @classmethod
    def edit_options(cls):
        return dict(type='datetime')


class W2BooleanHandler(W2GenericHandler):

    @classmethod
    def column_defaults(cls, model_column: Column):
        return dict(size=50, caption=model_column.name)

    @classmethod
    def edit_options(cls):
        return dict(type='checkbox')


class W2Definition(object):

    def __init__(self):
        self._specifications = {}               # Stored specifications
        self._model: Column = None              # SqlAlchemy Column
        self._handler: W2TypeHandler = None     # Handler for column type
        self._field = None                      # Field name
        self._nosearch = False                  # Do not suppress search parameters

    def set_options(self, **kwargs):
        for k, v in kwargs.items():
            assert hasattr(self, k), "Invalid attribute (keyword argument):" + k
            setattr(self, k, v)

    def _output_key(self, d: Dict, key, outkey=None):
        """Internal helper method to output the column/search specifications.  If the specification named
        by 'key' exists, then append that to dictionary 'd'.  'outkey' will overwrite the specifications
        key.  """
        if outkey is None:
            outkey = key
        if key in self._specifications:
            d[outkey] = self._specifications[key]


class W2Column(W2Definition):
    """A W2Column represents a `W2UI <http://www.w2ui.com/>`_ column in a
    `w2grid <http://w2ui.com/web/docs/1.5/grid/>`_ object.  A W2Column object stores the column and search
    specifications for the column and will generate the appropriate dictionary objects that will be converted
    to javascript/json constructs in the template.

    A W2Column object is constructed by passing passing a SQLAlchemy model column along with keyword arguments
    specifying the column and search attributes.  The constructor will also apply certain defaults depending
    on the SQL column type.

    A default W2Column object can be set for a particular SQL model column by using the `set_defaults` method.
    """

    def __init__(self, field, **kwargs):
        W2Definition.__init__(self)

        if type(field) is InstrumentedAttribute:
            # Field is a SQLAlchemy model column..
            self._model = field
            self._field = field.name
            # Check if a default column definition has been stored with the field.
            # Note: We do not flag any search specs from handler has explicit!
            if "W2Column" in field.info:
                default: W2Column = field.info["W2Column"]
                self._handler = default.handler
                self._has_search_spec = default.has_search_specs
                self.set_options(**default.specifications)
            else:
                self._handler = W2TypeHandler.for_model(field)
                self.set_options(**self._handler.column_defaults(self.model_column))
                self._has_search_spec = False
        else:
            self._field = field
            self._handler = W2GenericHandler
            self.set_options(**self._handler.column_defaults(self.model_column))
            self._has_search_spec = False

        self.set_options(**kwargs)

    @staticmethod
    def set_defaults(model_column: Column, **kwargs):
        """Saves a W2Column in a model column's info attribute.  This definition will be used to
        set default column/search specifications for any W2Column based on this model column."""
        w2c = W2Column(model_column, **kwargs)
        model_column.info['W2Column'] = w2c

    def filter(self, operator, value):
        search_method_name = "search_operator_" + operator
        search_method = getattr(self.handler, search_method_name, None)
        return search_method(self.model_column, value)

    def column_spec(self, field: str) -> Dict:
        """Returns a dictionary representing the w2ui column specification."""
        d = dict(field=field)
        self._output_key(d, 'caption')
        self._output_key(d, 'size')
        self._output_key(d, 'min')
        self._output_key(d, 'max')
        self._output_key(d, 'gridMinWidth')
        self._output_key(d, 'hidden')
        self._output_key(d, 'sortable')
        self._output_key(d, 'searchable')
        self._output_key(d, 'resizable')
        self._output_key(d, 'hideable')
        self._output_key(d, 'attr')
        self._output_key(d, 'style')
        self._output_key(d, 'render')
        self._output_key(d, 'title')
        self._output_key(d, 'editable')
        self._output_key(d, 'frozen')
        self._output_key(d, 'info')
        return d

    def search_spec(self, field: str) -> Dict:
        """Returns a dictionary representing the w2ui search specification."""
        d = dict(field=field)
        if 'search_caption' in self._specifications:
            self._output_key(d, 'search_caption', 'caption')
        else:
            self._output_key(d, 'caption')
        self._output_key(d, 'type')
        self._output_key(d, 'inTag')
        self._output_key(d, 'outTag')
        self._output_key(d, 'search_hidden', 'hidden')
        self._output_key(d, 'options')
        self._output_key(d, 'operator')
        return d


    #############################################################################################
    # PUBLIC GETABLE OBJECT PROPERTIES                                                          #
    # PUBLIC GETABLE OBJECT PROPERTIES                                                          #
    # PUBLIC GETABLE OBJECT PROPERTIES                                                          #
    #############################################################################################
    @property
    def specifications(self) -> Dict:
        """Returns a shallow copy of the specifications dictionary.  Note this excludes the field setting."""
        return dict(self._specifications)

    @property
    def has_search_specs(self) -> bool:
        """Return true if there has been explicit settings made for search.  The flag can be used by applications
        to suppress outputting search settings if no settings have been made"""
        return False if self.nosearch else self._has_search_spec


    #############################################################################################
    # PUBLIC SETABLE/GETABLE OBJECT PROPERTIES                                                  #
    # PUBLIC SETABLE/GETABLE OBJECT PROPERTIES                                                  #
    # PUBLIC SETABLE/GETABLE OBJECT PROPERTIES                                                  #
    #############################################################################################
    @property
    def handler(self) -> Type[W2TypeHandler]:
        # Handler for column type
        return self._handler

    @handler.setter
    def handler(self, h: W2TypeHandler):
        self._handler = h

    @property
    def field(self):
        """Field name to map to a column record.  Field may be a sqlalchemy Column, where the field value is retrieved
        from the columnb name"""
        return self._field

    @field.setter
    def field(self, obj):
        self._field = obj

    @property
    def model_column(self):
        return self._model

    @property
    def nosearch(self):
        """Suppress generation of search parameters for grid"""
        return self._nosearch

    @nosearch.setter
    def nosearch(self, flag):
        self._nosearch = flag

    @property
    def caption(self):
        """Column caption"""
        return self._specifications.get('caption', None)

    @caption.setter
    def caption(self, text):
        self._specifications['caption'] = text

    @property
    def size(self):
        """Size of a column in px or %."""
        size = self._specifications.get('size', None)
    
    @size.setter
    def size(self, size):
        self._specifications['size'] = size
    
    @property
    def min(self):
        """Minimum column width"""
        return self._specifications.get('min', None)
    
    @min.setter
    def min(self, min):
        self._specifications['min'] = min

    @property
    def max(self):
        """Maximum column width"""
        return self._specifications.get('max', None)

    @max.setter
    def max(self, max):
        self._specifications['max'] = max

    @property
    def gridMinWidth(self):
        """Minimum width of grid when column is visible"""
        return self._specifications.get('gridMinWidth', None)

    @gridMinWidth.setter
    def gridMinWidth(self, gridMinWidth):
        self._specifications['gridMinWidth'] = gridMinWidth

    @property
    def hidden(self):
        """Indicates if a column is hidden"""
        return self._specifications.get('hidden', None)

    @hidden.setter
    def hidden(self, hidden):
        self._specifications['hidden'] = hidden

    @property
    def sortable(self):
        """Indicates if a column is sortable"""
        return self._specifications.get('sortable', None)

    @sortable.setter
    def sortable(self, sortable):
        self._specifications['sortable'] = sortable

    @property
    def searchable(self):
        """Indicates if a column is searchable"""
        return self._specifications.get('searchable', None)

    @searchable.setter
    def searchable(self, searchable):
        self._specifications['searchable'] = searchable

    @property
    def resizable(self):
        """Indicates if a column is resizable"""
        return self._specifications.get('resizable', None)

    @resizable.setter
    def resizable(self, resizable):
        self._specifications['resizable'] = resizable

    @property
    def hideable(self):
        """Indicates if a column is hideable"""
        return self._specifications.get('hideable', None)

    @hideable.setter
    def hideable(self, hideable):
        self._specifications['hideable'] = hideable

    @property
    def attr(self):
        """String that will be inside the <td ... attr> tag"""
        return self._specifications.get('attr', None)

    @attr.setter
    def attr(self, attr):
        self._specifications['attr'] = attr

    @property
    def style(self):
        """Additional style for the td tag"""
        return self._specifications.get('style', None)

    @style.setter
    def style(self, style):
        self._specifications['style'] = style

    @property
    def render(self):
        """String or render function"""
        return self._specifications.get('render', None)

    @render.setter
    def render(self, render):
        self._specifications['render'] = render

    @property
    def title(self):
        """String for the title property for the column cells"""
        return self._specifications.get('title', None)

    @title.setter
    def title(self, title):
        self._specifications['title'] = title

    @property
    def editable(self):
        """Indicates if a column is editable"""
        return self._specifications.get('editable', None)

    @editable.setter
    def editable(self, editable):
        if editable == True:
            self._specifications['editable'] = self.handler.edit_options()
        else:
            self._specifications['editable'] = editable

    @property
    def frozen(self):
        """Indicates if a column is fixed to the left"""
        return self._specifications.get('frozen', None)

    @frozen.setter
    def frozen(self, frozen):
        self._specifications['frozen'] = frozen

    @property
    def info(self):
        """Infor bubble, can be bool/object"""
        return self._specifications.get('info', None)

    @info.setter
    def info(self, info):
        self._specifications['info'] = info

    # SEARCH ATTRIBUTES ====
    @property
    def type(self):
        """Type of field for search"""
        return self._specifications.get('type', None)

    @type.setter
    def type(self, type):
        self._specifications['type'] = type
        self._has_search_spec = True

    @property
    def search_caption(self):
        """Caption for search field"""
        return self._specifications.get('search_caption', None)

    @search_caption.setter
    def search_caption(self, text):
        self._specifications['search_caption'] = text
        self._has_search_spec = True

    @property
    def inTag(self):
        """Text that will be inside <input ...> tag"""
        return self._specifications.get('inTag', None)

    @inTag.setter
    def inTag(self, inTag):
        self._specifications['inTag'] = inTag
        self._has_search_spec = True

    @property
    def outTag(self):
        """Text that will be outside <input ...> tag"""
        return self._specifications.get('outTag', None)

    @outTag.setter
    def outTag(self, outTag):
        self._specifications['outTag'] = outTag
        self._has_search_spec = True

    @property
    def search_hidden(self):
        """Indicates if the search is shown or hidden."""
        return self._specifications.get('search_hidden', None)

    @search_hidden.setter
    def search_hidden(self, hidden):
        self._specifications['search_hidden'] = hidden
        self._has_search_spec = True

    @property
    def options(self):
        """Options for search's w2field object."""
        return self._specifications.get('options', None)

    @options.setter
    def options(self, options):
        self._specifications['options'] = options
        self._has_search_spec = True

    @property
    def operator(self):
        return self._specifications.get('operator', None)

    @operator.setter
    def operator(self, operator):
        self._specifications['operator'] = operator
        self._has_search_spec = True
