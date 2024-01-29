import sqlite3
import logging
from cache import StructureCache
from control import Datatype, Class, Attribute, AttributeAssignment, Reference, Object, ObjectList
from utils import get_data_table_name, get_reference_table_name, get_index_name, create_condition, print_table
from programmability.handler import ExecutionHandler

VERSION = '0.1'

class ObjectInterface:

    #region General
    def __init__(self, filename):
        self.filename = filename
        self.structure_cache = StructureCache()
        self.execution_handler = ExecutionHandler(self)
        self.connection = None
        self.cursor = None

    def connect(self):
        self.connection = sqlite3.connect(self.filename)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def setup(self):
        with open('setup\init.sql', 'r') as file:
            self.cursor.executescript(file.read())
        self.log('Setup')
        self.commit()
        logging.debug('Setup successful')

    def get_version(self):
        self.cursor.execute('SELECT version FROM info ORDER BY time DESC LIMIT 1')
        row = self.cursor.fetchone()
        return row['version']
    
    def info(self, limit: int = None):
        self.cursor.execute(f"SELECT * FROM info ORDER BY time DESC{f' LIMIT {limit}' if limit else ''}")
        print_table(self.cursor.fetchall())
        
    def log(self, comment: str):
        self.cursor.execute('INSERT INTO info (version, comment) VALUES (?, ?)', (VERSION, comment))

    def disconnect(self):
        self.connection.close()

    def commit(self):
        self.connection.commit()

    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.disconnect()
    #endregion
        
    #region Parser
    def parse_datatype(self, value: Datatype | int | str) -> Datatype:
        """Convert given value to Datatype object"""
        if isinstance(value, Datatype):
            return value
        elif isinstance(value, int):
            return self.get_datatype(id=value)
        elif isinstance(value, str):
            return self.get_datatype(name=value)
        else:
            raise TypeError(f'Type {type(value)} cannot be converted to Datatype object.')
        
    def parse_class(self, value: Class | int | str) -> Class:
        """Convert given value to Class object"""
        if isinstance(value, Class):
            return value
        elif isinstance(value, int):
            return self.get_class(id=value)
        elif isinstance(value, str):
            return self.get_class(name=value)
        else:
            raise TypeError(f'Type {type(value)} cannot be converted to Class object.')
        
    def parse_attribute(self, value: Attribute | int | str) -> Attribute:
        """Convert given value to Attribute object"""
        if isinstance(value, Attribute):
            return value
        elif isinstance(value, int):
            return self.get_attribute(id=value)
        elif isinstance(value, str):
            return self.get_attribute(name=value)
        else:
            raise TypeError(f'Type {type(value)} cannot be converted to Attribute object.')
        
    def parse_reference(self, value: Reference | int | str) -> Reference:
        """Convert given value to Reference object"""
        if isinstance(value, Reference):
            return value
        elif isinstance(value, int):
            return self.get_reference(id=value)
        elif isinstance(value, str):
            return self.get_reference(name=value)
        else:
            raise TypeError(f'Type {type(value)} cannot be converted to Reference object.')
    #endregion

    #region Datatype
    def create_datatype(self, name: str, generator: str, read_transformer_source: str = None, write_transformer_source: str = None) -> Datatype:
        """Creates new datatype and returns Datatype object"""
        self.cursor.execute("INSERT INTO structure_datatype (name, generator, read_transformer_source, write_transformer_source) VALUES (?, ?, ?, ?)", (name, generator, read_transformer_source, write_transformer_source))
        logging.debug(f"Created datatype {name} ({generator}, {'read transformer' if read_transformer_source else 'no read transformer'}, {'write transformer' if write_transformer_source else 'no write transformer'})")
        return Datatype(self, self.cursor.lastrowid, name, generator, read_transformer_source, write_transformer_source)
    
    def get_datatype_from_db(self, id: int = None, name: str = None) -> Datatype:
        """Reads a datatype from the database by its ID or name and returns a Datatype object"""
        condition, parameters = create_condition(id, name)
        self.cursor.execute(f"SELECT * FROM structure_datatype WHERE {condition}", parameters)
        res = self.cursor.fetchone()
        if res:
            return Datatype(self, res['id'], res['name'], res['generator'], res['read_transformer_source'], res['write_transformer_source'])
        else:
            raise KeyError(f'Datatype {parameters[0]} not found')
        
    def get_datatype(self, id: int = None, name: str = None) -> Datatype:
        """Reads a datatype from the database or cache if exists and returns a Datatype object"""
        cached_datatype = self.structure_cache.get_datatype(id=id, name=name)
        return cached_datatype if cached_datatype else self.get_datatype_from_db(id, name)
    #endregion

    #region Class
    def create_class(self, name: str, parent: Class = None):
        """Creates new class and returns Class object"""
        self.cursor.execute(f"CREATE TABLE {get_data_table_name(name)} (id INTEGER, version INTEGER, created DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(id, version))")
        if parent:
            self.cursor.execute("INSERT INTO structure_class (name, parent_id) VALUES (?, ?)", (name, parent.id))
        else:
            self.cursor.execute("INSERT INTO structure_class (name) VALUES (?)", (name,))
        logging.debug(f"Created new class {name}{f' as subclass of {parent.name}' if parent else ''}")
        return Class(self, self.cursor.lastrowid, name, parent.id if parent else None)
    
    def get_class_from_db(self, id: int = None, name: str = None):
        """Reads a class from the database by its ID or name and returns a Class object"""
        condition, parameters = create_condition(id, name)
        self.cursor.execute(f"SELECT * FROM structure_class WHERE {condition}", parameters)
        res = self.cursor.fetchone()
        if res:
            return Class(self, res['id'], res['name'], res['parent_id'])
        else:
            raise KeyError(f'Class {parameters[0]} not found')
        
    def get_class(self, id: int = None, name: str = None):
        """Reads a class from the database or cache if exists and returns a Class object"""
        cached_class = self.structure_cache.get_class(id=id, name=name)
        return cached_class if cached_class else self.get_class_from_db(id, name)
    
    def assign_attribute_to_class(self, class_: Class | int | str, attribute: Attribute | int | str, indexed: bool = False, read_transformer_source: str = None, write_transformer_source: str = None) -> AttributeAssignment:
        """Assigns given attribute to given class and return AttributeAssignment object"""
        class_ = self.parse_class(class_)
        attribute = self.parse_attribute(attribute)
        self.cursor.execute(f"ALTER TABLE {get_data_table_name(class_.name)} ADD COLUMN {attribute.name} {attribute.get_datatype().generator}")
        if indexed:
            self.cursor.execute(f"CREATE INDEX {get_index_name(class_.name, attribute.name)} ON {get_data_table_name(class_.name)}({attribute.name})")
        self.cursor.execute("INSERT INTO structure_attribute_assignment (class_id, attribute_id, indexed, read_transformer_source, write_transformer_source) VALUES (?, ?, ?, ?, ?)", (class_.id, attribute.id, indexed, read_transformer_source, write_transformer_source))
        logging.debug(f'Assigned {attribute.name} to {class_.name}')
        return AttributeAssignment(self, class_.id, attribute.id, indexed, read_transformer_source, write_transformer_source)
    
    def get_child_classes(self, class_: Class | int | str):
        """Returns the classes that have the given class as parent"""
        class_ = self.parse_class(class_)
        self.cursor.execute("SELECT id FROM structure_class WHERE parent_id = ?", (class_.id,))
        return [self.get_class(id=row['id']) for row in self.cursor.fetchall()]
    
    def get_attribute_assignments_from_db(self, class_: Class | int | str) -> list:
        """Retrieves attributes assigned to a class from the database"""
        class_ = self.parse_class(class_)
        self.cursor.execute("SELECT * FROM structure_attribute_assignment WHERE class_id = ?", (class_.id,))
        return [AttributeAssignment(self, class_.id, row['attribute_id'], row['indexed'], row['read_transformer_source'], row['write_transformer_source']) for row in self.cursor.fetchall()]
    #endregion

    #region Attribute
    def create_attribute(self, name: str, datatype: Datatype | int | str):
        """Creates a new attribute and returns Attribute object"""
        datatype = self.parse_datatype(datatype)
        self.cursor.execute("INSERT INTO structure_attribute (name, datatype_id) VALUES (?, ?)", (name, datatype.id))
        logging.debug(f'Created new attribute {name}')
        return Attribute(self, self.cursor.lastrowid, name, datatype.id)

    def get_attribute_from_db(self, id: int = None, name: str = None):
        """Reads an attribute from the database by its ID or name and returns an Attribute object"""
        condition, parameters = create_condition(id, name)
        self.cursor.execute(f"SELECT * FROM structure_attribute WHERE {condition}", parameters)
        res = self.cursor.fetchone()
        if res:
            return Attribute(self, res['id'], res['name'], res['datatype_id'])
        else:
            raise KeyError(f'Attribute {parameters[0]} not found')

    def get_attribute(self, id: int = None, name: str = None):
        """Reads an attribute from the database or cache if exists and returns an Attribute object"""
        cached_attribute = self.structure_cache.get_attribute(id=id, name=name)
        return cached_attribute if cached_attribute else self.get_attribute_from_db(id, name)
    #endregion

    #region Reference
    def create_reference(self, name: str, origin_class: Class | int | str, target_class: Class | int | str, cardinality: int = None):
        """Creates a new reference between two classes and returns Reference object"""
        origin_class = self.parse_class(origin_class)
        target_class = self.parse_class(target_class)
        self.cursor.execute("INSERT INTO structure_reference (name, origin_class_id, target_class_id, cardinality) VALUES (?, ?, ?, ?)", (name, origin_class.id, target_class.id, cardinality))
        self.cursor.execute(f"CREATE TABLE {get_reference_table_name(name)} (origin_id INTEGER REFERENCES data_meta(id), target_id INTEGER REFERENCES data_meta(id), version INTEGER, created DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(origin_id, target_id, version))")
        logging.debug(f'Created new reference {name} between class {origin_class.name} and {target_class.name}')
        return Reference(self, self.cursor.lastrowid, name, origin_class, target_class, cardinality)

    def get_reference_from_db(self, id: int = None, name: str = None):
        """Reads a reference from the database by its ID or name and returns a Reference object"""
        condition, parameters = create_condition(id, name)
        self.cursor.execute(f"SELECT * FROM structure_reference WHERE {condition}", parameters)
        res = self.cursor.fetchone()
        if res:
            return Reference(self, res['id'], res['name'], res['origin_class_id'], res['target_class_id'], res['cardinality'])
        else:
            raise KeyError(f'Reference {parameters[0]} not found')
        
    def get_reference(self, id: int = None, name: str = None):
        """Reads a reference from the database or cache if exists and returns a Reference object"""
        cached_reference = self.structure_cache.get_reference(id=id, name=name)
        return cached_reference if cached_reference else self.get_reference_from_db(id, name)
    #endregion
    
    #region Object
    def create_object(self, class_: Class | int | str, **attributes):
        """Inserts an object with the given class and attributes into the database"""
        class_ = self.parse_class(class_)

        # Zuerst das Objekt in data_meta einfügen und ID erhalten
        self.cursor.execute("INSERT INTO data_meta (class_id) VALUES (?) RETURNING id, created", (class_.id,))
        meta = self.cursor.fetchone()

        # Insert attributes
        object = Object(self, meta['id'], class_, meta['created'], **attributes)
        if len(attributes) > 0:
            self.modify(object, **attributes)
        return object
    
    def modify(self, object_: Object, **attributes) -> Object:
        """Modifies the given objects with the given attributes"""
        raw_attributes = {}

        # Get next version number
        self.cursor.execute('SELECT current_version FROM data_meta WHERE id = ?', (object_.id,))
        current_version = self.cursor.fetchone()['current_version']
        new_version = current_version + 1

        for current_class in object_.get_class().get_family_tree():
            table_name = get_data_table_name(current_class.name)

            # Get attributes that are assigned to the current class and are given as parameter and transform them for insertion into database
            class_attribute_names = [a.name for a in current_class.get_assigned_attributes()]
            current_attributes = {k: current_class.get_attribute_assignment(k).transform_write_processed_to_raw_value(v, object_) for k, v in attributes.items() if k in class_attribute_names}

            # Add transformed attributes to raw attribute dict
            raw_attributes.update(current_attributes)
            
            # Insert / Update attributes
            if current_attributes:

                # Get columns to adopt from current version
                cols_to_adopt = [col for col in class_attribute_names if col not in current_attributes.keys()]
                if len(cols_to_adopt) > 0:
                    self.cursor.execute(f"SELECT {', '.join(cols_to_adopt)} FROM {table_name} WHERE id = ? AND version = ?", (object_.id, current_version))
                    values_to_adopt = self.cursor.fetchone()
                    if values_to_adopt:
                        current_attributes.update(dict(values_to_adopt))

                # Insert new version
                str_cols = ', '.join(current_attributes.keys())
                str_placeholder = ', '.join(['?'] * len(current_attributes.keys()))
                self.cursor.execute(f"INSERT INTO {table_name} (id, version, {str_cols}) VALUES (?, ?, {str_placeholder})", (object_.id, new_version, *current_attributes.values()))

            # No changes => Just update version
            else:
                self.cursor.execute(f'UPDATE {table_name} SET version = ? WHERE id = ? AND version = ?', (new_version, object_.id, current_version))

        # Set new version to the current version
        self.cursor.execute('UPDATE data_meta SET current_version = ? WHERE id = ?', (new_version, object_.id))
        object_.update_raw_attributes(**raw_attributes)
        return object_
    
    def __get_class_view_sql__(self, class_: Class):
        strs_joins = []
        strs_cols = []
        for current_class in class_.get_family_tree():
            class_attributes = current_class.get_assigned_attributes()
            table_name = get_data_table_name(current_class.name)
            strs_joins.append(f'LEFT JOIN {table_name} ON data_meta.id = {table_name}.id AND data_meta.current_version = {table_name}.version')
            strs_cols.append(', '.join([f'{table_name}.{a.name}' for a in class_attributes]))
        str_joins = ' '.join(strs_joins)
        str_cols = ', '.join(strs_cols)
        return f'SELECT {str_cols} FROM data_meta {str_joins} WHERE data_meta.class_id = {class_.id}'
        
    def get_object(self, id: int) -> Object:
        """Reads the object with given id from database. Optionally, a snapshot time can be specified."""

        # Get meta data
        self.cursor.execute('SELECT * FROM data_meta WHERE id = ?', (id,))
        meta = self.cursor.fetchone()
        if not meta:
            return None
        
        # Get objects class
        class_ = self.get_class(id=meta['class_id'])

        # Get attributes
        self.cursor.execute(f"{self.__get_class_view_sql__(class_)} AND data_meta.id = ?", (id,))
        return Object(self, id, class_, meta['created'], **dict(self.cursor.fetchone()))
    
    def bind(self, reference: Reference | int | str, origin: Object, targets: list, rebind: bool = False):
        """Binds two objects using the given reference"""
        reference = self.parse_reference(reference)

        # Check cardinality
        if reference.cardinality is not None:
            if reference.cardinality < len(targets):
                raise ValueError(f'{len(targets)} objects can not be linked via reference with cardinality {reference.cardinality}.')
            elif rebind == False:
                current_bound_objects = len(origin.hop(reference))
                if reference.cardinality < len(targets) + current_bound_objects:
                    raise ValueError(f'{current_bound_objects} objects are already linked via reference. {len(targets)} others can not be linked with cardinality {reference.cardinality}. Use a rebind instead.')

        # Get current and next version number
        self.cursor.execute('INSERT OR IGNORE INTO structure_reference_version (reference_id, origin_object_id) VALUES (?, ?)', (reference.id, origin.id))
        self.cursor.execute('SELECT current_version FROM structure_reference_version WHERE reference_id = ? AND origin_object_id = ?', (reference.id, origin.id))
        current_version = self.cursor.fetchone()['current_version']
        new_version = current_version + 1

        # Update version of already bound objects
        table_name = get_reference_table_name(reference.name)
        if not rebind:
            self.cursor.execute(f"UPDATE {table_name} SET version = ? WHERE origin_id = ? RETURNING target_id", (new_version, origin.id))
            
            # Remove already bound objects from objects to bind
            current_target_ids = [row['target_id'] for row in self.cursor.fetchall()]
            if len(current_target_ids) > 0:
                targets = [t for t in targets if t.id not in current_target_ids]
        
        # Insert targets
        if len(targets) > 0:
            self.cursor.executemany(f"INSERT INTO {table_name} (origin_id, target_id, version) VALUES (?, ?, ?)", ((origin.id, target.id, new_version) for target in targets))
        
        # Apply new version
        self.cursor.execute("UPDATE structure_reference_version SET current_version = ? WHERE reference_id = ? AND origin_object_id = ?", (new_version, reference.id, origin.id))

    def hop(self, reference: Reference | int | str, origin: Object, version: int = None) -> ObjectList:
        """Returns objects referenced to the origin objects by the give reference"""
        reference = self.parse_reference(reference)

        # Get current version
        if not version:
            self.cursor.execute('SELECT current_version FROM structure_reference_version WHERE reference_id = ? AND origin_object_id = ?', (reference.id, origin.id))
            res = self.cursor.fetchone()
            if not res:
                return self.create_object_list()
            version = res['current_version']

        # Get referenced objects
        table_name = get_reference_table_name(reference.name)
        self.cursor.execute(f"SELECT target_id FROM {table_name} WHERE origin_id = ? AND version = ?", (origin.id, version))
        return self.create_object_list([self.get_object(row['target_id']) for row in self.cursor.fetchall()])
    #endregion

    def create_object_list(self, objects: list = []) -> ObjectList:
        """Creates ObjectList object from the given list"""
        return ObjectList(self, objects)
