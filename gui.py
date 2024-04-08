from interface import ObjectInterface
from flask import Flask, render_template, request, redirect, url_for, abort
import utils

FILENAME_DATABASE = 'data/database.db'
app = Flask(__name__)

def get_interface() -> ObjectInterface:
    interface = ObjectInterface(FILENAME_DATABASE)
    interface.connect()
    return interface

# Eigene Methoden in den Templates
@app.context_processor
def utility_processor():
    return dict(display_datetime=utils.display_datetime)

@app.route('/')
def class_list():
    with get_interface() as interface:
        interface.cursor.execute("SELECT id FROM structure_class ORDER BY id")
        return render_template('class_list.html', classes=[interface.get_class(row['id']) for row in interface.cursor.fetchall()])

@app.route('/class/<int:class_id>')
def show_class(class_id: int):
    with get_interface() as interface:

        # Klasse und alle Children ermitteln
        class_ = interface.get_class(class_id)
        valid_classes = [class_, *class_.get_children(True)]

        # Attribute ermitteln
        all_attributes = [aa.get_attribute() for aa in class_.get_attribute_assignments(True)]
        class_attributes = [aa.get_attribute() for aa in class_.get_attribute_assignments()]
        inherited_attributes = [ta for ta in all_attributes if ta.id not in [ca.id for ca in class_attributes]]

        # Referenzen ermitteln
        all_references = class_.get_references(recursive=True)
        class_references = class_.get_references()
        inherited_references = [tr for tr in all_references if tr.id not in [cr.id for cr in class_references]]

        # Objekte ermitteln
        objects = interface.get_instances(class_id, recursive=True)

        return render_template('show_class.html', 
                               class_=class_, 
                               class_attributes=class_attributes,
                               inherited_attributes=inherited_attributes,
                               class_references=class_references,
                               inherited_references=inherited_references,
                               objects=objects)

# Attributzuweisung anzeigen    
@app.route('/attribute/<int:class_id>/<int:attribute_id>')
def show_attribute_assignment(class_id: int, attribute_id: int):
    with get_interface() as interface:

        # Klasse und Attributzuweisung ermitteln
        class_ = interface.get_class(class_id)
        attribute_assignments = [aa for aa in class_.get_attribute_assignments() if aa.class_id == class_id and aa.attribute_id == attribute_id]
        if len(attribute_assignments) == 0:
            abort(400, 'Attribute assignment not found')
        attribute_assignment = attribute_assignments[0]

        return render_template('show_attribute_assignment.html',
                               class_=class_,
                               attribute=attribute_assignment.get_attribute())

# Objekt anzeigen    
@app.route('/object/<int:object_id>')
def show_object(object_id: int):
    with get_interface() as interface:
        object_ = interface.get_object(object_id)
        return render_template('show_object.html', object_=object_)
    
# Logeinträge anzeigen
@app.route('/log')
def log():
    with get_interface() as interface:
        return render_template('log.html', rows=interface.get_log())
        
if __name__ == '__main__':
    app.run(debug=True)