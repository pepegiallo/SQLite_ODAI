import os
import logging
import sqlite3
from interface import ObjectInterface
from ddl import Interpreter
from utils import print_table
import examples.randomdata as rd
import random

FILENAME_DATABASE = 'data/database.db'
FILENAME_STRUCTURE = 'setup/example_structure.ddl'

def get_db_connection():
    connection = sqlite3.connect(FILENAME_DATABASE)
    connection.row_factory = sqlite3.Row
    return connection

def explore():
    with get_db_connection() as connection:
        sql = 'SELECT type, name, tbl_name, rootpage FROM sqlite_schema'
        while len(sql):
            print_table(connection.execute(sql).fetchall())
            sql = input('> ')

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)

    # Datenbank neu aufsetzen und verbinden
    if os.path.exists(FILENAME_DATABASE):
        os.remove(FILENAME_DATABASE)
    interface = ObjectInterface(FILENAME_DATABASE)
    interface.connect()
    interface.setup()

    # Datenmodell einspielen
    interpreter = Interpreter(interface)
    with open(FILENAME_STRUCTURE, 'r') as file:
        interpreter.run(file.read())
    interface.commit()

    # Seed setzen
    rd.set_seed(1902)

    # Zufällige Personen erstellen
    n_samples = 100
    persons = []
    addresses = []
    c_person = interface.get_class(name='Person')
    c_address = interface.get_class(name='Address')
    ref_person_to_address = interface.get_reference(name='person_to_address')
    for i in range(n_samples):
        persons.append(interface.create_object(c_person, **rd.get_random_person()))
        addresses.append(interface.create_object(c_address, **rd.get_random_address()))
        interface.bind(ref_person_to_address, persons[-1], [addresses[-1]])

    # Zufällige Mitarbeitende erstellen
    n_samples = 100
    employees = []
    c_employee = interface.get_class(name='Employee')
    ref_manager_to_employees = interface.get_reference(name='manager_to_employees')
    for i in range(n_samples):
        employees.append(interface.create_object(c_employee, **rd.get_random_employee()))
        addresses.append(interface.create_object(c_address, **rd.get_random_address()))
        interface.bind(ref_person_to_address, employees[-1], [addresses[-1]])

        # Führungskraft?
        if random.randint(0, 9) == 0 and len(employees) > 10:
            interface.bind(ref_manager_to_employees, employees[-1], random.sample(employees[0: -1], random.randint(2, 10)))
    interface.commit()

    # Objekte zufällig anpassen
    n_iterations = 4
    for i in range(n_iterations):

        # Personen
        for p in random.sample(persons, len(persons) // 4):
            random_attributes = rd.get_random_person()
            some_random_attributes = dict(random.sample(random_attributes.items(), random.randint(1, len(random_attributes))))
            p.modify(**some_random_attributes)

        # Addressen
        for a in random.sample(addresses, len(addresses) // 4):
            random_attributes = rd.get_random_address()
            some_random_attributes = dict(random.sample(random_attributes.items(), random.randint(1, len(random_attributes))))
            a.modify(**some_random_attributes)

        # Mitarbeitende
        for e in random.sample(employees, len(employees) // 4):
            random_attributes = rd.get_random_employee()
            some_random_attributes = dict(random.sample(random_attributes.items(), random.randint(1, len(random_attributes))))
            e.modify(**some_random_attributes)

            # Führungskraft?
            if random.randint(0, 9) == 0:
                interface.bind(ref_manager_to_employees, e, random.sample(employees[0: -1], random.randint(2, 10)), rebind=random.choice([True, False]))
            else:
                interface.bind(ref_manager_to_employees, e, [], rebind=True)
    interface.commit()

    # Hop
    for e in employees:
        manager_employees = e.hop(ref_manager_to_employees)
        if len(manager_employees) > 0:
            print(f'Manager has {len(manager_employees)} employees\n{e.dump()}\n\nEmployees:')
            for me in manager_employees:
                print(me.dump())
            print('################################################################################')


    interface.disconnect()

    with get_db_connection() as connection:
        sql = interface.__get_class_view_sql__(c_employee)
        print_table(connection.execute(sql).fetchall())

    #explore()

    
