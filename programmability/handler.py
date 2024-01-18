import logging
import utils

def read_allowed_builtins() -> dict:
    """Reads allowed builtin names from allowed_builtins.txt and returns builtin dictionary"""
    with open('programmability/allowed_builtins.txt', 'r') as file:
        return {key: __builtins__[key] for key in [line.strip() for line in file.readlines()] if key in __builtins__.keys()}

class ExecutionHandler:
    def __init__(self, interface) -> None:
        self.interface = interface
        self.allowed_globals = {
            '__builtins__': read_allowed_builtins(),
            
            'get_class': lambda name: self.interface.get_class(name=name),
            'get_attribute': lambda name: self.interface.get_attribute(name=name),
            'get_reference': lambda name: self.interface.get_reference(name=name),
            'get_object': lambda id: self.interface.get_object(id),

            'parse_sqlite_date': utils.parse_sqlite_date,
            'parse_sqlite_datetime': utils.parse_sqlite_datetime,
            'create_decimal': utils.create_decimal,
            'get_decimal_base_value': utils.get_decimal_base_value,
            'array_to_bytes': utils.array_to_bytes,
            'bytes_to_array': utils.bytes_to_array
        }

    def transform_value(self, source: str, value, **locals):
        if source:
            allowed_locals = {'value': value}
            allowed_locals.update(locals)
            try:
                exec(source, self.allowed_globals, allowed_locals)
            except Exception as e:
                print(f"Error executing access transformer: {e}")
                return None
            return allowed_locals['value']
        else:
            return value
       