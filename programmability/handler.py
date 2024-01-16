import logging

def read_allowed_builtins() -> dict:
    """Reads allowed builtin names from allowed_builtins.txt and returns builtin dictionary"""
    with open('programmability/allowed_builtins.txt', 'r') as file:
        return {key: __builtins__[key] for key in [line.strip() for line in file.readlines()]}

class ExecutionHandler:
    def __init__(self, interface) -> None:
        self.interface = interface
        self.allowed_globals = {
            '__builtins__': read_allowed_builtins(),
            'get_class': lambda name: self.interface.get_class(name=name),
            'get_attribute': lambda name: self.interface.get_attribute(name=name),
            'get_reference': lambda name: self.interface.get_reference(name=name),
            'get_object': lambda id: self.interface.get_object(id)
        }

    def transform_value(self, source: str, object, value):
        allowed_locals = {'value': value, 'this': object}
        try:
            exec(source, self.allowed_globals, allowed_locals)
        except Exception as e:
            print(f"Error executing accessor transformer on object {object.id}: {e}")
            return None
        return allowed_locals['value']
       