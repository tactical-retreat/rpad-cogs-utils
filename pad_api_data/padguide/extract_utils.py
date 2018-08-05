from datetime import datetime
from decimal import Decimal

# Tables that use 1/0 instead of Y/N?
_ALT_YN_TABLES = [
    'dungeon_list',
]

# Tables that use full datetimes
_ALT_DATETIME_TABLES = [
    'egg_title_list',
    'monster_list',
]

# Hour/Minute fields that shouldn't be zformat(2)
_ALT_HR_MIN_COLS = [
    'SERVER_OPEN_HOUR',
]


def fix_table_name(table_name):
    parts = table_name.split('_')
    return ''.join([parts[0]] + [p.capitalize() for p in parts[1:]])


def _copy_override(row_data, override_suffix):
    override_columns = list(filter(lambda x: x.endswith(override_suffix), row_data.keys()))
    for oc in override_columns:
        value = row_data[oc]
        del row_data[oc]
        if not value:
            continue
        base_name = oc[:-len(override_suffix)]
        if base_name not in row_data:
            print('error: base column missing:', base_name)
        else:
            row_data[base_name] = value


def fix_row(table_name, row):
    row_data = {}
    for col in row:
        fixed_col = col.upper()
        if fixed_col.startswith('_'):
            fixed_col = fixed_col[1:]
        data = row[col]
        if data is None:
            fixed_data = ''
        elif '_YN' in fixed_col:
            if table_name in _ALT_YN_TABLES:
                fixed_data = '1' if data else '0'
            else:
                fixed_data = 'Y' if data else 'N'
        elif type(data) is Decimal:
            first = '{}'.format(float(data))
            second = '{:.1f}'.format(float(data))
            fixed_data = max((first, second), key=len)
        elif type(data) is datetime:
            if table_name in _ALT_DATETIME_TABLES:
                fixed_data = data.isoformat(' ')
            else:
                fixed_data = data.date().isoformat()
        elif 'HOUR' in fixed_col or 'MINUTE' in fixed_col:
            if fixed_col in _ALT_HR_MIN_COLS:
                fixed_data = str(data)
            else:
                fixed_data = str(data).zfill(2)
        else:
            fixed_data = str(data)

        row_data[fixed_col] = fixed_data

    _copy_override(row_data, '_CALCULATED')
    _copy_override(row_data, '_OVERRIDE')
    return row_data


def dump_table(table_name, cursor):
    result_json = {'items': []}
    for row in cursor:
        result_json['items'].append(fix_row(table_name, row))

    return result_json
