import time

from . import db_util
from .sql_item import SqlItem


class NewsItem(SqlItem):
    def __init__(self, server: str, title: str, url: str):
        self.tn_seq = None  # Provided at insert

        self.del_yn = 0
        self.os_type = 'C'  # Both OSes
        self.server = server  # JP or US

        self.title_jp = title
        self.title_kr = title
        self.title_us = title

        self.tstamp = int(time.time()) * 1000

        self.url_jp = url
        self.url_kr = url
        self.url_us = url

    def insert_sql(self, tn_seq):
        self.tn_seq = tn_seq
        return super().insert_sql()

    def exists_sql(self):
        sql = """SELECT tn_seq FROM news_list
                 WHERE server = {server}
                 AND title_us  = {title_us}
                 """.format(**db_util.object_to_sql_params(self))
        return sql

    def _table(self):
        return 'news_list'

    def _key(self):
        return 'tn_seq'

    def _insert_columns(self):
        return [
            'tn_seq',
            'del_yn',
            'os_type',
            'server',
            'title_jp', 'title_kr', 'title_us',
            'tstamp',
            'url_jp', 'url_kr', 'url_us',
        ]

    def __repr__(self):
        return 'NewsItem({})'.format(self.title_us)
