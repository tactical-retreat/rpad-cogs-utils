from datetime import datetime, date
import decimal

# Copied this from the processor; easier than fixing paths

# This could maybe move to a class method on SqlItem?
# Fix usage in load_x_object in db_util.


def process_col_mappings(obj_type, d, reverse=False):
    if hasattr(obj_type, 'COL_MAPPINGS'):
        mappings = obj_type.COL_MAPPINGS
        if reverse:
            mappings = {v: k for k, v in mappings.items()}

        for k, v in mappings.items():
            d[v] = d[k]
            d.pop(k)
    return d


def object_to_sql_params(obj):
    d = obj if type(obj) == dict else obj.__dict__
    # Defensive copy since we're updating this dict
    d = dict(d)
    d = process_col_mappings(type(obj), d, reverse=True)
    new_d = {}
    for k, v in d.items():
        new_val = value_to_sql_param(v)
        if new_val is not None:
            new_d[k] = new_val
    return new_d


def value_to_sql_param(v):
    if v is None:
        return 'NULL'
    elif type(v) == str:
        clean_v = v.replace("'", r"''")
        return "'{}'".format(clean_v)
    elif type(v) in (int, float, decimal.Decimal):
        return '{}'.format(v)
    elif type(v) in [date]:
        return "'{}'".format(v.isoformat())
    elif type(v) in [datetime]:
        return "'{}'".format(v.replace(tzinfo=None).isoformat())
    elif type(v) in [bool]:
        return str(v)
    else:
        return None


def _col_value_ref(col):
    return '{' + col + '}'


def _col_name_ref(col):
    return '`' + col + '`'


def _tbl_name_ref(table_name):
    return '`' + table_name + '`'


def generate_insert_sql(table_name, cols, item):
    sql = 'INSERT INTO {}'.format(_tbl_name_ref(table_name))
    sql += ' (' + ', '.join(map(_col_name_ref, cols)) + ')'
    sql += ' VALUES (' + ', '.join(map(_col_value_ref, cols)) + ')'
    return sql.format(**object_to_sql_params(item))
