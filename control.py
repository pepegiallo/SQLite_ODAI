from datetime import datetime
from utils import remove_duplicates
import pandas as pd
from functools import cache
from constant import STATUS_ACTIVE

class ObjectInterfaceControl:
    def __init__(self, interface) -> None:
        self.interface = interface

    def clear_cache(self):
        pass

class Datatype(ObjectInterfaceControl):
    def __init__(self, interface, id: int, name: str, read_transformer_source: str, write_transformer_source: str, generator: str, parent_id: int) -> None:
        super().__init__(interface)
        self.id = id
        self.name = name
        self.__generator__ = generator
        self.parent_id = parent_id

        # Transformfunktionen
        self.read_transformer_source = read_transformer_source
        self.__transform_read_value__ = interface.execution_handler.generate_transformer(read_transformer_source, parameters=['value'])
        self.write_transformer_source = write_transformer_source
        self.__transform_write_value__ = interface.execution_handler.generate_transformer(write_transformer_source, parameters=['value'])

        self.interface.register_control(self)

    def get_generator(self):
        """ Gibt den Generator des Datentyps zurück """
        if self.is_root():
            return self.__generator__
        else:
            return self.get_parent().get_generator()

    def is_root(self):
        """ Gibt zurück, ob der Datentyp ein Ursprungstyp ist (keine Vorfahren hat) """
        return self.parent_id is None

    def transform_read_value(self, value):
        """ Transformiert den gegebenen Wert mithilfe der Lesen-Umwandlungsfunktion des Datentyps """
        if self.is_root():
            return self.__transform_read_value__(value)
        else:
            return self.__transform_read_value__(self.get_parent().transform_read_value(value))
        
    def transform_write_value(self, value):
        """ Transformiert den gegebenen Wert mithilfe der Schreiben-Umwandlungsfunktion des Datentyps"""
        if self.is_root():
            return self.__transform_write_value__(value)
        else:
            return self.get_parent().transform_write_value(self.__transform_write_value__(value))

    def get_parent(self):
        """ Gibt Datentypobjekt des Parent-Datentypen zurück """
        if self.parent_id is not None:
            return self.interface.get_datatype(self.parent_id)
        else:
            return None


class Class(ObjectInterfaceControl):
    def __init__(self, interface, id: int, name: str, parent_id: int) -> None:
        super().__init__(interface)
        self.id = id
        self.name = name
        self.parent_id = parent_id
        self.interface.register_control(self)

    def clear_cache(self):
        super().clear_cache()
        self.get_family_tree.cache_clear()
        self.get_total_children.cache_clear()
        self.get_total_attribute_assignments.cache_clear()
        self.get_attribute_assignment.cache_clear()

    def get_parent(self):
        """ Gibt Klassenobjekt der Parent-Klasse zurück """
        if self.parent_id is not None:
            return self.interface.get_class(self.parent_id)
        else:
            return None

    @cache
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
    
    @cache
    def get_total_children(self) -> list:
        """ Gibt die untergeordneten Klassen rekursiv zurück """
        total_children = []
        for child in self.get_children():
            total_children.append(child)
            total_children.extend(child.get_total_children())
        return total_children
    
    def get_attribute_assignments(self):
        """ Gibt die Attributzuweisungen der Klasse zurück """
        return self.interface.get_attribute_assignments(self)

    def get_assigned_attributes(self):
        """ Gibt die der Klasse direkt zugewiesenen Attribute zurück """
        return [assignment.get_attribute() for assignment in self.get_attribute_assignments()]

    def is_root(self):
        """ Gibt zurück, ob die Klasse eine Ursprungsklasse ist (keine Vorfahren hat) """
        return self.parent_id is None

    @cache
    def get_total_attribute_assignments(self) -> dict:
        """ Gibt die Liste der AttributeAssignments aller der Klasse zugeordneten Objekte (selbst und übergeordnet) zurück """
        total_attribute_assignments = []
        for class_ in self.get_family_tree():
            total_attribute_assignments.extend(class_.get_attribute_assignments())
        return total_attribute_assignments
    
    def get_total_assigned_attributes(self) -> list:
        """ Gibt die Liste der Attribute aller der Klasse zugeordneten Objekte (selbst und übergeordnet) zurück """
        return [assignment.get_attribute() for assignment in self.get_total_attribute_assignments()]

    @cache
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
        self.interface.register_control(self)

    def get_datatype(self) -> Datatype:
        return self.interface.get_datatype(self.datatype_id)


class AttributeAssignment(ObjectInterfaceControl):
    def __init__(self, interface, class_id: str, attribute_id: str, indexed: bool, read_transformer_source: str, write_transformer_source: str):
        super().__init__(interface)
        self.class_id = class_id
        self.attribute_id = attribute_id
        self.indexed = indexed
        self.interface.register_control(self)

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
        return self.interface.get_class(self.class_id)

    def get_attribute(self) -> Attribute:
        """ Gibt Attributobjekt zurück """
        return self.interface.get_attribute(self.attribute_id)


class Reference(ObjectInterfaceControl):
    def __init__(self, interface, id: str, name: str, origin_class_id: str, target_class_id: str, cardinality: int) -> None:
        super().__init__(interface)
        self.id = id
        self.name = name
        self.origin_class_id = origin_class_id
        self.target_class_id = target_class_id
        self.cardinality = cardinality
        self.interface.register_control(self)

    def get_origin_class(self):
        """ Gibt Klassenobjekt der Ursprungsklasse zurück """
        return self.interface.get_class(self.origin_class_id)

    def get_target_class(self):
        """ Gibt Klassenobjekt der Zielklasse zurück """
        return self.interface.get_class(self.target_class_id)

class Object(ObjectInterfaceControl):
    def __init__(self, interface, id: str, class_: Class, status: int, created: datetime, **raw_attributes):
        super().__init__(interface)
        self.id = id
        self.class_ = class_
        self.status = status
        self.created = created
        self.raw_attributes = raw_attributes
        self.interface.register_control(self)

    def __getitem__(self, key: str):
        return self.get_value(key)

    def get_class(self) -> Class:
        """ Gibt die Klasse des Objekts zurück """
        return self.class_
    
    def get_attribute_names(self) -> list:
        return self.raw_attributes.keys()
    
    def clear_cache(self):
        super().clear_cache()
        self.get_value.cache_clear()
        self.get_unprocessed_value.cache_clear()

    def is_active(self):
        """ Gibt zurück, ob das Objekt aktiv ist """
        return self.status == STATUS_ACTIVE

    def activate(self):
        """ Aktiviert das Objekt """
        self.interface.activate(self)

    def deactivate(self):
        """ Deaktiviert das Objekt """
        self.interface.deactivate(self)

    def delete(self):
        """ Löscht das Objekt """
        self.interface.delete(self)

    def modify(self, **attributes):
        """ Aktualisiert die übergebenen Attribute """
        self.interface.modify(self, **attributes)

    def bind(self, reference: Reference | int | str, targets: list, rebind: bool = False):
        self.interface.bind(reference, self, targets, rebind)

    def hop(self, reference: Reference | int | str, version: int = None):
        return self.interface.hop(reference, self, version)
    
    def hop_first(self, reference: Reference | int | str, version: int = None):
        objects = self.hop(reference, version)
        if len(objects) > 0:
            return objects[0]
        else:
            return None

    def dump(self):
        """ Gibt String mit allen Objekteigenschaften zurück """
        str_attributes = '\n  '.join(f'{attribute_name} = {self[attribute_name]}' for attribute_name in self.get_attribute_names())
        return f"{self.class_.name} {self.id} ({['In creation', 'Active', 'Inactive', 'Deleted'][self.status]}):\n  {str_attributes}"
    
    def update_raw_attributes(self, **raw_attributes):
        self.raw_attributes.update(raw_attributes)
        for key in raw_attributes.keys():
            self.get_value.cache_parameters().pop(key, None)
            self.get_unprocessed_value.cache_parameters().pop(key, None)
    
    @cache
    def get_value(self, attribute_name: str):
        """ Gibt den transformierten Wert eines Attributs zurück """
        if attribute_name in self.raw_attributes.keys():
            assignment = self.class_.get_attribute_assignment(attribute_name)
            return assignment.transform_read_value(self.get_unprocessed_value(attribute_name), self)
        else:
            raise KeyError(f'Invalid attribute {attribute_name}')
    
    @cache
    def get_unprocessed_value(self, attribute_name: str):
        """ Gibt den nicht-transformierten Wert eines Attributs zurück """
        if attribute_name in self.raw_attributes.keys():
            assignment = self.class_.get_attribute_assignment(attribute_name)
            return assignment.datatype_transform_read_value(self.raw_attributes[attribute_name])
        else:
            raise KeyError(f'Invalid attribute {attribute_name}')
        
    def get_raw_value(self, attribute_name: str):
        """ Gibt den Datenbankwert eines Attributs zurück """
        if attribute_name in self.raw_attributes.keys():
            return self.raw_attributes[attribute_name]
        else:
            raise KeyError(f'Invalid attribute {attribute_name}')
        
class ObjectList(ObjectInterfaceControl):
    def __init__(self, interface, objects: list = []):
        super().__init__(interface)
        self.objects = objects
        self.interface.register_control(self)

    def __len__(self):
        return len(self.objects)
    
    def __iter__(self):
        return iter(self.objects)
    
    def __getitem__(self, index: int):
        return self.objects[index]

    def append(self, object_: Object):
        self.objects.append(object_)
        self.get_dataframe.cache_clear()

    def extend(self, objects: list):
        self.objects.extend(objects)
        self.get_dataframe.cache_clear()

    def clear(self):
        self.objects.clear()
        self.get_dataframe.cache_clear()

    @cache
    def get_dataframe(self) -> pd.DataFrame:
        """ Wandelt die enthaltenden Objekte mit den gegebenen oder allen Attributen in ein Dataframe um """
        if len(self) > 0:
            data = [{'id': obj.id} | {key: obj[key] for key in obj.get_attribute_names()} for obj in self]
            return pd.DataFrame.from_dict(data).set_index('id')
        else:
            return pd.DataFrame({'id': []}).set_index('id')

    def hop(self, reference: Reference | int | str):
        referenced_objects = []
        for object in self:
            referenced_objects.extend(self.interface.hop(reference, object))
        return ObjectList(self.interface, remove_duplicates(referenced_objects))
    
    def get_column(self, attribute_name: str) -> pd.Series:
        return self.get_dataframe()[attribute_name]
    
    def filter(self, conditions):
        indices = list(self.get_dataframe()[conditions].index)
        return ObjectList(self.interface, [obj for obj in self if obj.id in indices])
