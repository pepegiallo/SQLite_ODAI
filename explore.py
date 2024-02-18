import sys
import logging
import sqlite3
from utils import print_table

FILENAME_DATABASE = 'data/database.db'

def get_db_connection():
    connection = sqlite3.connect(FILENAME_DATABASE)
    connection.row_factory = sqlite3.Row
    return connection

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)

    with get_db_connection() as connection:
        if len(sys.argv) > 1:
            sql = sys.argv[1]
        else:
            sql = 'SELECT type, name, tbl_name, rootpage FROM sqlite_schema'
        print_table(connection.execute(sql).fetchall())
