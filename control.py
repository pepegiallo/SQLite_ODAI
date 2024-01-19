from datetime import datetime
from utils import remove_duplicates

class ObjectInterfaceControl:
    def __init__(self, interface) -> None:
        self.interface = interface

class Datatype(ObjectInterfaceControl):
    def __init__(self, interface, id: int, name: str, generator: str, read_transformer_source: str, write_transformer_source: str) -> None:
        super().__init__(interface)
        self.id = id
        self.name = name
        self.generator = generator

        # Transformfunktionen
        self.read_transformer_source = read_transformer_source
        self.transform_read_value = interface.execution_handler.generate_transformer(read_transformer_source, parameters=['value'])
        self.write_transformer_source = write_transformer_source
        self.transform_write_value = interface.execution_handler.generate_transformer(write_transformer_source, parameters=['value'])

        # In den Cache einfügen
        interface.structure_cache.store_datatype(self)


class Class(ObjectInterfaceControl):
    def __init__(self, interface, id: int, name: str, parent_id: int) -> None:
        super().__init__(interface)
        self.id = id
        self.name = name
        self.parent_id = parent_id
        self.attribute_assignments = None
        self.total_attribute_assignments = None
        interface.structure_cache.store_class(self)

    def get_parent(self):
        """ Gibt Klassenobjekt der Parent-Klasse zurück """
        if self.parent_id is not None:
            return self.interface.get_class(id=self.parent_id)
        else:
            return None

    def get_family_tree(self) -> list:
        """ Gibt den Stammbaum der Klasse (alle übergeordneten Klassen und sich selbst) zurück """
        if self.is_root():
          return [self]
        else:
          family_tree = self.get_parent().get_family_tree()
          family_tree.append(self)
          return family_tree
        
    def get_children(self) -> list:
        """ Gibt die untergeordneten Klassen zurück """
        return self.interface.get_child_classes(self)
        
    def get_total_children(self) -> list:
        """ Gibt die untergeordneten Klassen rekursiv zurück """
        total_children = []
        for child in self.get_children():
            total_children.append(child)
            total_children.extend(child.get_total_children())
        return total_children

    def get_attribute_assignments(self):
        """ Gibt die Attributzuweisungen der Klasse zurück """
        if not self.attribute_assignments:
            self.attribute_assignments = self.interface.get_attribute_assignments_from_db(self)
        return self.attribute_assignments

    def get_assigned_attributes(self):
        """ Gibt die der Klasse direkt zugewiesenen Attribute zurück """
        return [assignment.get_attribute() for assignment in self.get_attribute_assignments()]

    def is_root(self):
        """ Gibt zurück, ob die Klasse eine Ursprungsklasse ist (keine Vorfahren hat) """
        return self.parent_id is None

    def __get_total_attribute_assignments__(self) -> dict:
        """ Erstellt eine Liste der AttributeAssignments aller der Klasse zugeordneten Objekte (selbst und übergeordnet) zurück """
        total_attribute_assignments = []
        for class_ in self.get_family_tree():
            total_attribute_assignments.extend(class_.get_attribute_assignments())
        return total_attribute_assignments
    
    def get_total_attribute_assignments(self):
        """ Gibt die Liste der AttributeAssignments aller der Klasse zugeordneten Objekte (selbst und übergeordnet) zurück """
        if not self.total_attribute_assignments:
            self.total_attribute_assignments = self.__get_total_attribute_assignments__()
        return self.total_attribute_assignments

    def get_attribute_assignment(self, attribute_name: str):
        """ Gibt die Attributzuweisung aller bei der Klasse erlaubten Attribute anhand des gegeben Attributnamens zurück """
        for aa in self.get_total_attribute_assignments():
            if aa.get_attribute().name == attribute_name:
                return aa
        return None


class Attribute(ObjectInterfaceControl):
    def __init__(self, interface, id: str, name: str, datatype_id: int) -> None:
        super().__init__(interface)
        self.id = id
        self.name = name
        self.datatype_id = datatype_id
        interface.structure_cache.store_attribute(self)

    def get_datatype(self) -> Datatype:
        return self.interface.get_datatype(id=self.datatype_id)


class AttributeAssignment(ObjectInterfaceControl):
    def __init__(self, interface, class_id: str, attribute_id: str, indexed: bool, read_transformer_source: str, write_transformer_source: str):
        super().__init__(interface)
        self.class_id = class_id
        self.attribute_id = attribute_id
        self.indexed = indexed

        # Eigene Transformfunktionen
        self.read_transformer_source = read_transformer_source
        self.transform_read_value = interface.execution_handler.generate_transformer(read_transformer_source, parameters=['value', 'this'])
        self.write_transformer_source = write_transformer_source
        self.transform_write_value = interface.execution_handler.generate_transformer(write_transformer_source, parameters=['value', 'this'])
        
        # Transformfunktionen des Datentyps
        datatype = self.get_attribute().get_datatype()
        self.datatype_transform_read_value = datatype.transform_read_value
        self.datatype_transform_write_value = datatype.transform_write_value

    def transform_write_processed_to_raw_value(self, value, object_):
        return self.transform_write_value(self.datatype_transform_write_value(value), object_)

    def get_class(self) -> Class:
        """ Gibt Klassenobjekt zurück """
        return self.interface.get_class(id=self.class_id)

    def get_attribute(self) -> Attribute:
        """ Gibt Attributobjekt zurück """
        return self.interface.get_attribute(id=self.attribute_id)


class Reference(ObjectInterfaceControl):
    def __init__(self, interface, id: str, name: str, origin_class_id: str, target_class_id: str) -> None:
        super().__init__(interface)
        self.id = id
        self.name = name
        self.origin_class_id = origin_class_id
        self.target_class_id = target_class_id
        interface.structure_cache.store_reference(self)

    def get_origin_class(self):
        """ Gibt Klassenobjekt der Ursprungsklasse zurück """
        return self.interface.get_class(id=self.origin_class_id)

    def get_target_class(self):
        """ Gibt Klassenobjekt der Zielklasse zurück """
        return self.interface.get_class(id=self.target_class_id)

class Object(ObjectInterfaceControl):
    def __init__(self, interface, id: str, class_: Class, created: datetime, **raw_attributes):
        super().__init__(interface)
        self.id = id
        self.class_ = class_
        self.created = created
        self.raw_attributes = raw_attributes
        self.__attributes__ =  {}
        self.__unprocessed_attributes__ = {}

    def __getitem__(self, key: str):
        return self.get_value(key)

    def get_class(self) -> Class:
        """ Gibt die Klasse des Objekts zurück """
        return self.class_
    
    def get_attribute_names(self) -> list:
        return self.raw_attributes.keys()

    def modify(self, **attributes):
        """ Aktualisiert die übergebenen Attribute """
        self.interface.modify(self, **attributes)

    def bind(self, reference: Reference, targets: list, rebind: bool = False):
        self.interface.bind(reference, self, targets, rebind)

    def hop(self, reference: Reference, version: int = None):
        return self.interface.hop(reference, self, version)

    def dump(self):
        """ Gibt String mit allen Objekteigenschaften zurück """
        str_attributes = '\n  '.join(f'{attribute_name} = {self[attribute_name]}' for attribute_name in self.get_attribute_names())
        return f'{self.class_.name} {self.id}:\n  {str_attributes}'
    
    def update_raw_attributes(self, **raw_attributes):
        self.raw_attributes.update(raw_attributes)
        for key in raw_attributes.keys():
            self.__attributes__.pop(key, None)
            self.__unprocessed_attributes__.pop(key, None)
    
    def calculate_value(self, attribute_name: str):
        """ Berechnet den finalen Attributwert mithilfe der Lesen-Methode der Attributzuweisung """
        assignment = self.class_.get_attribute_assignment(attribute_name)
        self.__attributes__[attribute_name] = assignment.transform_read_value(self.get_unprocessed_value(attribute_name), self)

    def calculate_unprocessed_value(self, attribute_name: str):
        """ Berechnet den Attributwert mithilfe der Umwandlungsmethode des Datentyps """
        assignment = self.class_.get_attribute_assignment(attribute_name)
        self.__unprocessed_attributes__[attribute_name] = assignment.datatype_transform_read_value(self.raw_attributes[attribute_name])
    
    def get_value(self, attribute_name: str):
        if attribute_name in self.raw_attributes.keys():
            if not attribute_name in self.__attributes__.keys():
                self.calculate_value(attribute_name)
            return self.__attributes__[attribute_name]
        else:
            raise KeyError(f'Invalid attribute {attribute_name}')
        
    def get_unprocessed_value(self, attribute_name: str):
        if attribute_name in self.raw_attributes.keys():
            if not attribute_name in self.__unprocessed_attributes__.keys():
                self.calculate_unprocessed_value(attribute_name)
            return self.__unprocessed_attributes__[attribute_name]
        else:
            raise KeyError(f'Invalid attribute {attribute_name}')
        
    def get_raw_value(self, attribute_name: str):
        if attribute_name in self.raw_attributes.keys():
            return self.raw_attributes[attribute_name]
        else:
            raise KeyError(f'Invalid attribute {attribute_name}')
        
class ObjectList(ObjectInterfaceControl, list):
    def __init__(self, interface, objects: list):
        super().__init__(interface)
        self.extend(objects)

    def hop(self, reference: Reference):
        referenced_objects = []
        for object in self:
            referenced_objects.extend(self.interface.hop(reference, object))
        self.clear()
        self.extend(remove_duplicates(referenced_objects))
        return self
