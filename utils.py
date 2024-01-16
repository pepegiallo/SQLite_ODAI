def get_data_table_name(class_name: str) -> str:
    return f"data_{class_name}"

def get_reference_table_name(reference_name: str) -> str:
    return f"reference_{reference_name}"

def get_index_name(table_name: str, column_name: str) -> str:
    return f"idx_{table_name}_{column_name}"

def create_condition(id: int = None, name: str = None):
    if id:
        return 'id = ?', (id,)
    elif name:
        return 'name = ?', (name,)
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