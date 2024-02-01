from datetime import datetime, date
from decimal import Decimal
import math
import numpy as np
from io import BytesIO
from functools import wraps
from time import time

def get_data_table_name(class_name: str) -> str:
    return f"data_{class_name}"

def get_reference_table_name(reference_name: str) -> str:
    return f"reference_{reference_name}"

def get_index_name(table_name: str, column_name: str) -> str:
    return f"idx_{table_name}_{column_name}"

def create_condition(key: int | str):
    if isinstance(key, int):
        return 'id = ?', (key,)
    elif isinstance(key, str):
        return 'name = ?', (key,)
    else:
        raise KeyError('Id or name required')
    
def get_filled_parameter_name(**parameters):
    for key in parameters.keys():
        if parameters[key]:
            return key
    raise KeyError('At least one parameter requires a value')
    
def print_table(rows: list):
    """ Prints a list of dictionaries with equal keys as table """
    if len(rows) > 0:
        headers = rows[0].keys()
        n_cols = len(headers)
        max_length = list(map(lambda col: max(max(map(lambda row: len(str(rows[row][col])), range(len(rows)))), len(headers[col])), range(n_cols)))
        table_rows = [' | '.join(map(lambda i: headers[i].ljust(max_length[i]), range(n_cols)))]
        table_rows.append(''.ljust(len(table_rows[0]), '-'))
        for row in rows:
            table_rows.append(' | '.join(map(lambda i: (str(row[i]) if row[i] is not None else '-').ljust(max_length[i]), range(n_cols))))
        print('\n'.join(table_rows))
    else:
        print('No data')

def remove_duplicates(objects: list):
    """Removes duplicates from a list with objects (Asserts that the objects have a unique attribute id)"""
    unique_ids = set()
    unique_objects = []
    for obj in objects:
        if obj.id not in unique_ids:
            unique_ids.add(obj.id)
            unique_objects.append(obj)
    return unique_objects

def measure_runtime(func):
    @wraps(func)
    def wrapper_func(*args, **kwargs):
        start_time = time()
        func(*args, **kwargs)
        print(f'Execution lasted {time() - start_time:.2f} seconds')
    return wrapper_func

def parse_sqlite_date(str_date: str) -> datetime:
    return datetime.strptime(str_date, r'%Y-%m-%d').date()

def date_to_string(d: date) -> str:
    return d.strftime(r'%Y-%m-%d')

def parse_sqlite_datetime(str_datetime: str) -> datetime:
    return datetime.strptime(str_datetime, r'%Y-%m-%d %H:%M:%S')

def datetime_to_string(dt: datetime) -> str:
    return dt.strftime(r'%Y-%m-%d %H:%M:%S')

def create_decimal(base_value: int, decimal_digits: int) -> Decimal:
    return Decimal(base_value) / Decimal(math.pow(10, decimal_digits))

def get_decimal_base_value(decimal_: Decimal, decimal_digits: int) -> int:
    return int(decimal_ * int(math.pow(10, decimal_digits)))

def array_to_bytes(array: np.array) -> bytes:
    buffer = BytesIO()
    np.save(buffer, array, allow_pickle=True)
    return buffer.getvalue()

def bytes_to_array(bytes_: bytes) -> np.array:
    buffer = BytesIO(bytes_)
    return np.load(buffer, allow_pickle=True)