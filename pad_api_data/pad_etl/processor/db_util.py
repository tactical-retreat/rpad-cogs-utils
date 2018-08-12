from datetime import datetime, date
import decimal
import logging

import pymysql


logger = logging.getLogger('database')
logger.setLevel(logging.ERROR)


def object_to_sql_params(obj):
    d = obj if type(obj) == dict else obj.__dict__
    new_d = {}
    for k, v in d.items():
        if v is None:
            new_d[k] = 'NULL'
        elif type(v) == str:
            clean_v = v.replace("'", r"''")
            new_d[k] = "'{}'".format(clean_v)
        elif type(v) in (int, float, decimal.Decimal):
            new_d[k] = '{}'.format(v)
        elif type(v) in [datetime, date]:
            new_d[k] = "'{}'".format(v.isoformat())
    return new_d


def _col_compare(col):
    return col + ' = ' + _col_value_ref(col)


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


class DbWrapper(object):
    def __init__(self, dry_run: bool=True):
        self.dry_run = dry_run
        self.connection = None

    def connect(self, db_config):
        logger.debug('DB Connecting')
        self.connection = pymysql.connect(host=db_config['host'],
                                          user=db_config['user'],
                                          password=db_config['password'],
                                          db=db_config['db'],
                                          charset=db_config['charset'],
                                          cursorclass=pymysql.cursors.DictCursor,
                                          autocommit=True)
        logger.info('DB Connected')

    def execute(self, cursor, sql):
        logger.debug('Executing: %s', sql)
        return cursor.execute(sql)

    def fetch_data(self, sql):
        with self.connection.cursor() as cursor:
            self.execute(cursor, sql)
        return list(cursor.fetchall())

    def load_to_key_value(self, key_name, value_name, table_name):
        with self.connection.cursor() as cursor:
            sql = 'SELECT {} AS k, {} AS v FROM {}'.format(key_name, value_name, table_name)
            self.execute(cursor, sql)
            data = list(cursor.fetchall())
            return {row['k']: row['v'] for row in data}

    def get_single_or_no_row(self, sql):
        with self.connection.cursor() as cursor:
            self.execute(cursor, sql)
            data = list(cursor.fetchall())
            num_rows = len(data)
            if num_rows > 1:
                raise ValueError('got too many results:', num_rows, sql)
            if num_rows == 0:
                return None
            else:
                return data[0]

    def get_single_value(self, sql, op=str):
        with self.connection.cursor() as cursor:
            self.execute(cursor, sql)
            data = list(cursor.fetchall())
            num_rows = len(data)
            if num_rows == 0:
                if self.dry_run:
                    return None
                raise ValueError('got zero results:', sql)
            if num_rows > 1:
                raise ValueError('got too many results:', num_rows, sql)
            row = data[0]
            if len(row.values()) > 1:
                raise ValueError('too many columns in result:', sql)
            return op(list(row.values())[0])

    def check_existing(self, sql):
        with self.connection.cursor() as cursor:
            num_rows = self.execute(cursor, sql)
            if num_rows > 1:
                raise ValueError('got too many results:', num_rows, sql)
            return bool(num_rows)

    def check_existing_value(self, sql):
        with self.connection.cursor() as cursor:
            num_rows = self.execute(cursor, sql)
            if num_rows > 1:
                raise ValueError('got too many results:', num_rows, sql)
            elif num_rows == 0:
                return None
            else:
                row_values = list(cursor.fetchone().values())
                if len(row_values) > 1:
                    return row_values
                else:
                    return row_values[0]

    def insert_item(self, sql):
        with self.connection.cursor() as cursor:
            if self.dry_run:
                logger.warn('not inserting item due to dry run')
                return
            self.execute(cursor, sql)
            data = list(cursor.fetchall())
            num_rows = len(data)
            if num_rows > 0:
                raise ValueError('got too many results for insert:', num_rows, sql)
