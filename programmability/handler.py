import logging
import utils
import zlib

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
            'date_to_string': utils.date_to_string,
            'parse_sqlite_datetime': utils.parse_sqlite_datetime,
            'datetime_to_string': utils.datetime_to_string,
            'create_decimal': utils.create_decimal,
            'get_decimal_base_value': utils.get_decimal_base_value,
            'array_to_bytes': utils.array_to_bytes,
            'bytes_to_array': utils.bytes_to_array,
            'compress': zlib.compress,
            'decompress': zlib.decompress
        }

    def transform_value(self, source: str, value, **locals):
        if source:
            source_def_content = '\n'.join([f'    {line}' for line in source.splitlines() if len(line) > 0])
            source_to_execute = f"def transform(value):\n{source_def_content}"
            allowed_locals = {}
            allowed_locals.update(locals)
            try:
                exec(source_to_execute, self.allowed_globals, allowed_locals)
            except Exception as e:
                logging.error(f"Error executing access transformer: {e}")
                return None
            return allowed_locals['transform'](value)
        else:
            return value

    def generate_transformer(self, source: str, parameters: list = ['value'], **locals):
        if source:
            source_def_content = '\n'.join([f'    {line}' for line in source.splitlines() if len(line) > 0])
            source_to_execute = f"def transform({','.join(parameters)}):\n{source_def_content}"
            try:
                exec(source_to_execute, self.allowed_globals, locals)
            except Exception as e:
                logging.error(f"Error generating transformer function: {e}")
                return None
        else:
            exec(f"transform = lambda {','.join(parameters)}: {parameters[0]}", self.allowed_globals, locals)
        return locals['transform']
       