from interface import ObjectInterface
from flask import Flask, render_template, request, redirect, url_for, abort

FILENAME_DATABASE = 'data/database.db'
app = Flask(__name__)

def get_interface() -> ObjectInterface:
    interface = ObjectInterface(FILENAME_DATABASE)
    interface.connect()
    return interface

@app.route('/')
def index():
    with get_interface() as interface:
        interface.cursor.execute("SELECT id FROM structure_class ORDER BY id")
        return render_template('class_list.html', classes=[interface.get_class(row['id']) for row in interface.cursor.fetchall()])

@app.route('/class/<int:class_id>')
def show_class(class_id: int):
    with get_interface() as interface:

        # Klasse und alle Children ermitteln
        class_ = interface.get_class(id=class_id)
        valid_classes = [class_, *class_.get_total_children()]

        # Attribute ermitteln
        total_attributes = [aa.get_attribute() for aa in class_.get_total_attribute_assignments()]
        class_attributes = [aa.get_attribute() for aa in class_.get_attribute_assignments()]
        inherited_attributes = [ta for ta in total_attributes if ta.id not in [ca.id for ca in class_attributes]]
        displayed_attribute_names = [ta.name for ta in total_attributes]

        # Objekte ermitteln
        interface.cursor.execute(f"SELECT id FROM data_meta WHERE class_id IN ({', '.join([str(c.id) for c in valid_classes])})")
        objects = [interface.get_object(row['id']) for row in interface.cursor.fetchall()]

        return render_template('show_class.html', 
                               class_=class_, 
                               class_attributes=class_attributes,
                               inherited_attributes=inherited_attributes,
                               displayed_attribute_names=displayed_attribute_names, 
                               objects=objects)
    
@app.route('/attribute/<int:class_id>/<int:attribute_id>')
def show_attribute_assignment(class_id: int, attribute_id: int):
    with get_interface() as interface:

        # Klasse und Attributzuweisung ermitteln
        class_ = interface.get_class(id=class_id)
        attribute_assignments = [aa for aa in class_.get_attribute_assignments() if aa.class_id == class_id and aa.attribute_id == attribute_id]
        if len(attribute_assignments) == 0:
            abort(400, 'Attribute assignment not found')
        attribute_assignment = attribute_assignments[0]

        return render_template('show_attribute_assignment.html',
                               class_=class_,
                               attribute=attribute_assignment.get_attribute())

if __name__ == '__main__':
    app.run(debug=True)