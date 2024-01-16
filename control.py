from datetime import datetime
from utils import remove_duplicates

class Class:
    def __init__(self, interface, id: int, name: str, parent_id: int) -> None:
        self.interface = interface
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

    def get_attribute_assignment(self, name: str):
        """ Gibt die Attributzuweisung aller bei der Klasse erlaubten Attribute anhand des gegeben Attributnamens zurück """
        for aa in self.get_total_attribute_assignments():
            if aa.get_attribute().name == name:
                return aa
        return None


class Attribute:
    def __init__(self, interface, id: str, name: str, generator: str) -> None:
        self.interface = interface
        self.id = id
        self.name = name
        self.generator = generator
        interface.structure_cache.store_attribute(self)

class AttributeAssignment:
    def __init__(self, interface, class_id: str, attribute_id: str, indexed: bool, nullable: bool, default: str, getter_transformer_source: str, setter_transformer_source: str):
        self.interface = interface
        self.class_id = class_id
        self.attribute_id = attribute_id
        self.indexed = indexed
        self.nullable = nullable
        self.default = default
        self.getter_transformer_source = getter_transformer_source
        self.setter_transformer_source = setter_transformer_source

    def get_class(self) -> Class:
        """ Gibt Klassenobjekt zurück """
        return self.interface.get_class(id=self.class_id)

    def get_attribute(self) -> Attribute:
        """ Gibt Attributobjekt zurück """
        return self.interface.get_attribute(id=self.attribute_id)

class Reference:
    def __init__(self, interface, id: str, name: str, origin_class_id: str, target_class_id: str) -> None:
        self.interface = interface
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

class Object:
    def __init__(self, interface, id: str, class_: Class, created: datetime, **attributes):
        self.interface = interface
        self.id = id
        self.class_ = class_
        self.created = created
        self.attributes = attributes

    def get_class(self) -> Class:
        """ Gibt die Klasse des Objekts zurück """
        return self.class_

    def modify(self, **attributes):
        """ Aktualisiert die übergebenen Attribute """
        self.interface.modify(self, **attributes)

    def bind(self, reference: Reference, targets: list, rebind: bool = False):
        self.interface.bind(reference, self, targets, rebind)

    def hop(self, reference: Reference, version: int = None):
        return self.interface.hop(reference, self, version)

    def dump(self):
        """ Gibt String mit allen Objekteigenschaften zurück """
        str_attributes = '\n  '.join(f'{attribute} = {value}' for attribute, value in self.attributes.items())
        return f'{self.class_.name} {self.id}:\n  {str_attributes}'
    
    def get_attribute_value(self, name: str):
        assignment = self.class_.get_attribute_assignment(name)
        value = self.attributes[name]
        if assignment.getter_transformer_source:
            value = self.interface.execution_handler.transform_value(assignment.getter_transformer_source, self, value)
        return value
        
class ObjectList(list):
    def __init__(self, interface, objects: list):
        self.interface = interface
        self.extend(objects)

    def hop(self, reference: Reference):
        referenced_objects = []
        for object in self:
            referenced_objects.extend(self.interface.hop(reference, object))
        self.clear()
        self.extend(remove_duplicates(referenced_objects))
        return self
