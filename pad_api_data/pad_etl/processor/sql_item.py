from . import db_util

class SqlItem(object):
    def key_value(self):
        return getattr(self, self._key()) if self._key() else None

    def needs_insert(self):
        if not self.uses_local_primary_key():
            raise Exception('Should not call this function, uses FK primary Key')
        key_val = self.key_value()
        return key_val is None or key_val == 0


    def uses_local_primary_key(self):
        """Controls insert logic.

        If true, an insert is needed if the primary key is missing.
        If false, an insert is needed if the primary key is set but not found in the table.
        """
        return True

    def exists_sql(self):
        sql = 'SELECT {} FROM {} WHERE {}'.format(
            self._key(), self._table(), self._col_compare(self._key()))
        return sql.format(**db_util.object_to_sql_params(self))

    def needs_update_sql(self):
        update_cols = self._update_columns()
        if update_cols is None:
            return False
        cols = [self._key()] + update_cols
        sql = 'SELECT {} FROM {} WHERE'.format(self._key(), self._table())
        sql += ' ' + ' AND '.join(map(self._col_compare, cols))

        formatted_sql = sql.format(**db_util.object_to_sql_params(self))
        fixed_sql = formatted_sql.replace('= NULL', 'is NULL')
        return fixed_sql

    def _col_compare(self, col):
        return col + ' = ' + self._col_value_ref(col)

    def _col_value_ref(self, col):
        return '{' + col + '}'

    def _col_name_ref(self, col):
        return '`' + col + '`'

    # TODO: move to dbutil
    def update_sql(self):
        cols = self._update_columns()
        if not cols:
            return None  # Update not supported

        # If an item is timestamped, modify the timestamp on every update
        if hasattr(self, 'tstamp'):
            # TODO: Consider auto udpating tstamp here
            if 'tstamp' not in cols:
                cols = cols + ['tstamp']

        sql = 'UPDATE {}'.format(self._table())
        sql += ' SET ' + ', '.join(map(self._col_compare, cols))
        sql += ' WHERE ' + self._col_compare(self._key())
        return sql.format(**db_util.object_to_sql_params(self))

    def insert_sql(self):
        cols = self._insert_columns()
        if hasattr(self, 'tstamp'):
            # TODO: Consider auto udpating tstamp here
            if 'tstamp' not in cols:
                cols = cols + ['tstamp']
        return db_util.generate_insert_sql(self._table(), cols, self)

    def _table(self):
        raise NotImplemented('no table name set')

    def _key(self):
        raise NotImplemented('no key name set')

    def _insert_columns(self):
        raise NotImplemented('no insert columns set')

    def _update_columns(self):
        return None
