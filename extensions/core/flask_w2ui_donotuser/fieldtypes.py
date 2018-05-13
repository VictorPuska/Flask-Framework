"""
Identification
    Module:     types
    Author:     Victor Puska
    Written:    Jul 19, 2017
    Copyright:  (c) 2017 by VICTOR PUSKA.
    License:    LICENSE_NAME, see LICENSE_FILE for more details.

Description
    Authentication and authority management for the application.
"""
from typing import Dict
from datetime import date, datetime, time

W2COLUMN_ATTRIBUTES = [
    'caption',  # '',     // column caption
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


class W2SearchCondition(object):
    """ W2SearchCondition is a record object describing a particular search clause.  It has three fields:
    - where_clause: A string defining a portion of a SQL where clause relevant to a single field.
                    Eg. "my_field > %s"
    - value1:       The search value
    - value2:       Second search value (only applicable to 'between' searches)

    A W2SearchCondition is returned by BaseType.search_condition_xxx methods.
    """
    def __init__(self, where_clause, value1, value2=None):
        self.where_clause: str = where_clause
        self.value1 = value1
        self.value2 = value2


class W2TableMetadata(object):

    def __init__(self, tablename, rect_id, columns):
        self.tablename = tablename
        self.rec_id = rect_id
        self.columns = columns


class W2ColumnMetadata(object):

    def __init__(self, **kwargs):
        self.column:        str = kwargs.get('COLUMN_NAME', None)
        self.data_type:     str = kwargs.get('DATA_TYPE', None)
        self.column_type:   str = kwargs.get('COLUMN_TYPE', None)
        self.max_char_len:  int = kwargs.get('CHARACTER_MAXIMUM_LENGTH', -1)
        self.precision:     int = kwargs.get('NUMERIC_PRECISION', -1)
        self.scale:         int = kwargs.get('NUMERIC_SCALE', -1)
        self.column_key:    str = kwargs.get('COLUMN_KEY', None)
        self.extra:         str = kwargs.get('EXTRA', None)

    def make_w2field(self) -> 'BaseType':
        if self.column_type == "tinyint(1)":
            field = W2BooleanField(self.column, self.column)
        elif self.data_type == 'varchar':
            field = W2TextField(self.column, self.column, size=self.max_char_len * 8)
        elif self.data_type == 'int':
            field = W2IntegerField(self.column, self.column)
        elif self.data_type == 'date':
            field = W2DateField(self.column, self.column)
        elif self.data_type == 'datetime':
            field = W2DateTimeField(self.column, self.column)
        else:
            field = W2Field(self.column, self.column)
        return field


class W2Field(object):
    def __init__(self, field: str, caption: str, **kwargs):
        self.w2_field = field
        self.w2_caption = caption
        for k, v in kwargs.items():
            setattr(self, "w2_" + k, v)

    def _options(self, valid_attributes, **kwargs) -> Dict[str, object]:
        opts = {}
        w2attr = filter(lambda x: x.startswith('w2_'), dir(self))
        for o in w2attr:
            w2o = o[3:]
            if w2o in valid_attributes:
                opts[W2ATTRIBUTE_MAP.get(w2o, w2o)] = getattr(self, o)
        for k, v in kwargs.items():
            opts[k] = v
        return opts

    def column_options(self, **kwargs) -> Dict[str, object]:
        return self._options(W2COLUMN_ATTRIBUTES, **kwargs)

    def search_options(self, **kwargs) -> Dict[str, object]:
        return self._options(W2SEARCH_ATTRIBUTES, **kwargs)

    def search_condition(self, **kwargs) -> W2SearchCondition:
        # Validate the search values first.  Some search conditions sent by w2ui might not work or apply
        # to the particular field type.
        try:
            value = kwargs['value']
            if isinstance(value, list):
                kwargs['value'] = [self.prepare_search_value(value[0]), self.prepare_search_value(value[1])]
            else:
                kwargs['value'] = self.prepare_search_value(value)
        except ValueError:
            return None
        # Values are valid, so build the search condition
        operator = kwargs['operator']
        operator_method_name = "search_condition_" + operator
        operator_method = getattr(self, operator_method_name, None)
        if operator_method:
            return operator_method(**kwargs)
        else:
            return None

    def prepare_search_value(self, value):
        return value

    def search_condition_is(self, **kwargs):
        return W2SearchCondition(
            "{0}=%s".format(self.w2_field),
            kwargs['value']
        )

    def search_condition_less(self, **kwargs):
        return W2SearchCondition(
            "{0}<%s".format(self.w2_field),
            kwargs['value']
        )

    def search_condition_more(self, **kwargs):
        return W2SearchCondition(
            "{0}>%s".format(self.w2_field),
            kwargs['value']
        )

    def search_condition_between(self, **kwargs):
        return W2SearchCondition(
            "{0} between %s and %s ".format(self.w2_field),
            kwargs['value'][0],
            kwargs['value'][1]
        )


class W2DateField(W2Field):
    def __init__(self, field: str, caption: str, **kwargs):
        self.w2_size = 100
        self.w2_type = 'date'
        super().__init__(field, caption, **kwargs)

    def column_options(self, **kwargs):
        opts = super().column_options(**kwargs)
        opts['editable'] = {'type': 'date'}
        # opts['render'] = 'date'
        return opts

    def prepare_search_value(self, value):
        return datetime.strptime(value, "%d/%m/%Y").date()


class W2DateTimeField(W2Field):
    def __init__(self, field: str, caption: str, **kwargs):
        self.w2_size = 150
        self.w2_type = 'datetime'
        super().__init__(field, caption, **kwargs)

    def column_options(self, **kwargs):
        opts = super().column_options(**kwargs)
        opts['editable'] = {'type': 'datetime'}
        # opts['render'] = 'datetime:dd/mm/yyyy|h12'
        return opts

    def search_options(self, **kwargs):
        return None


class W2TextField(W2Field):
    def __init__(self, field: str, caption: str, **kwargs):
        self.w2_size = 200
        self.w2_type = 'text'
        super().__init__(field, caption, **kwargs)

    def column_options(self, **kwargs):
        opts = super().column_options(**kwargs)
        opts['editable'] = {'type': 'text'}
        return opts

    def search_condition_begins(self, **kwargs):
        return W2SearchCondition(
            "{0} like %s ".format(self.w2_field),
            kwargs['value'] + "%"
        )

    def search_condition_ends(self, **kwargs):
        return W2SearchCondition(
            "{0} like %s ".format(self.w2_field),
            "%" + kwargs['value']
        )

    def search_condition_contains(self, **kwargs):
        return W2SearchCondition(
            "{0} like %s ".format(self.w2_field),
            "%" + kwargs['value'] + "%"
        )


class W2IntegerField(W2Field):
    def __init__(self, field: str, caption: str, **kwargs):
        self.w2_size = 100
        self.w2_type = 'int'
        super().__init__(field, caption, **kwargs)


class W2BooleanField(W2Field):
    def __init__(self, field: str, caption: str, **kwargs):
        self.w2_size = 100
        self.w2_type = 'enum'
        super().__init__(field, caption, **kwargs)

    def column_options(self, **kwargs):
        opts = super().column_options(**kwargs)
        opts['editable'] = {'type': 'checkbox'}
        return opts

    def search_options(self, **kwargs):
        opts = super().column_options(**kwargs)
        opts['type'] = 'enum'
        opts['options'] = {'items': [{'text': 'TRUE'}, {'text': 'FALSE'}]}
        return opts

    def search_condition_is(self, **kwargs):
        value = kwargs['value'].upper()
        if value in ['TRUE', 'FALSE']:
            return W2SearchCondition(
                "{0}=%s".format(self.w2_field),
                kwargs['value'] == 'TRUE'
            )
        else:
            return None
