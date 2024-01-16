from control import Class, Attribute, Reference
from utils import get_filled_parameter_name

class DictCache:
    def __init__(self, *atts):
        self.atts = atts
        self.dicts = {}
        self.setup()

    def setup(self):
        """ Initialisiert die benötigten Dictionaries """
        for a in self.atts:
            self.dicts[a] = {}

    def store(self, element) -> None:
        """ Legt ein Element in den Dictionaries ab """
        for a in self.atts:
            self.dicts[a][getattr(element, a)] = element

    def store_custom(self, element, **kv) -> None:
        """ Legt ein Element mit den gegebenen Keys in den Dictionaries ab """
        for key, value in kv.items():
            if key in self.atts:
                self.dicts[key][value] = element

    def get(self, attr, value):
        """ Gibt ein Element anhand des übergebenen Attribut-Wert-Paares zurück """
        return self.dicts[attr].get(value)

    def contains(self, attr, value) -> bool:
        """ Gibt zurück, ein Element mit dem übergebenen Attribut-Wert-Paares vorhanden ist """
        return value in self.dicts[attr]

class StructureCache:
    def __init__(self) -> None:
        self.class_cache = DictCache('id', 'name')
        self.attribute_cache = DictCache('id', 'name')
        self.reference_cache = DictCache('id', 'name')

    def store_class(self, class_: Class) -> None:
        """ Fügt ein Klassenobjekt hinzu """
        self.class_cache.store(class_)

    def get_class(self, **key_parameters) -> Class:
        """ Gibt ein Klassenobjekt anhand 'id' oder 'name' zurück """
        key = get_filled_parameter_name(**key_parameters)
        return self.class_cache.get(key, key_parameters[key])

    def contains_class(self, **key_parameters) -> bool:
        """ Gibt anhand 'id' oder 'name' zurück, ob die Klasse im Cache vorhanden ist """
        key = get_filled_parameter_name(**key_parameters)
        return self.class_cache.contains(key, key_parameters[key])

    def store_attribute(self, attribute: Attribute) -> None:
        """ Fügt ein Attributobjekt hinzu """
        self.attribute_cache.store(attribute)

    def get_attribute(self, **key_parameters) -> Attribute:
        """ Gibt ein Attributobjekt anhand 'id' oder 'name' zurück """
        key = get_filled_parameter_name(**key_parameters)
        return self.attribute_cache.get(key, key_parameters[key])

    def contains_attribute(self, **key_parameters) -> bool:
        """ Gibt anhand 'id' oder 'name' zurück, ob das Attribut im Cache vorhanden ist """
        key = get_filled_parameter_name(**key_parameters)
        return self.attribute_cache.contains(key, key_parameters[key])

    def store_reference(self, reference: Reference) -> None:
        """ Fügt ein Referenzobjekt hinzu """
        self.reference_cache.store(reference)

    def get_reference(self, **key_parameters) -> Reference:
        """ Gibt ein Referenzobjekt anhand 'id' oder 'name' zurück """
        key = get_filled_parameter_name(**key_parameters)
        return self.reference_cache.get(key, key_parameters[key])

    def contains_reference(self, **key_parameters) -> bool:
        """ Gibt anhand 'id' oder 'name' zurück, ob die Referenz im Cache vorhanden ist """
        key = get_filled_parameter_name(**key_parameters)
        return self.reference_cache.contains(key, key_parameters[key])