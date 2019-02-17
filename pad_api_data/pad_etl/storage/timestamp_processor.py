
def update_timestamps(db_wrapper):
    get_tables_sql = 'SELECT `internal_table` FROM get_timestamp'
    tables = list(map(lambda x: x['internal_table'], db_wrapper.fetch_data(get_tables_sql)))
    for table in tables:
        get_tstamp_sql = 'SELECT MAX(tstamp) as tstamp FROM `{}`'.format(table.lower() + '_list')
        try:
            tstamp_row = db_wrapper.get_single_or_no_row(get_tstamp_sql)
            if tstamp_row:
                tstamp = tstamp_row['tstamp']
                update_tstamp_sql = 'UPDATE get_timestamp SET tstamp = {} WHERE internal_table = "{}"'.format(
                    tstamp, table)
                db_wrapper.insert_item(update_tstamp_sql)
        except:
            pass  # table probably didn't exist

