-- Allgemeine Informationen
CREATE TABLE info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    "version" VARCHAR(8) NOT NULL,
    comment TEXT,
    "time" DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Datentyp
CREATE TABLE structure_datatype (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    read_transformer_source TEXT,
    write_transformer_source TEXT,
    generator TEXT,
    parent_id INTEGER REFERENCES structure_class(id)
);
CREATE INDEX datatype_name ON structure_datatype(name);

-- Klasse
CREATE TABLE structure_class (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    parent_id INTEGER REFERENCES structure_class(id)
);
CREATE INDEX class_name ON structure_class(name);

-- Attribut
CREATE TABLE structure_attribute (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    datatype_id INTEGER REFERENCES datatype(id)
);
CREATE INDEX attribute_name ON structure_attribute(name);

-- Attributzuweisung: Zuweisung von Attributen zu Klassen
CREATE TABLE structure_attribute_assignment (
    class_id INTEGER REFERENCES structure_class(id),
    attribute_id INTEGER REFERENCES structure_attribute(id),
    indexed TINYINT NOT NULL,
    read_transformer_source TEXT,
    write_transformer_source TEXT,
    PRIMARY KEY (class_id, attribute_id)
);

-- Referenz: Verknüpfungen zwischen Objekten, Referenzen können nur zwischen zwei definierten Objektklassen bestehen
CREATE TABLE structure_reference (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    origin_class_id INTEGER REFERENCES structure_class(id),
    target_class_id INTEGER REFERENCES structure_class(id),
    cardinality UNSIGNED INTEGER
);
CREATE INDEX reference_name ON structure_reference(name);

-- Referenz-Versionen nach Ursprungsobjekt
CREATE TABLE structure_reference_version (
    reference_id INTEGER REFERENCES structure_reference(id),
    origin_object_id INTEGER REFERENCES data_meta(id),
    current_version INTEGER DEFAULT 0,
    PRIMARY KEY(reference_id, origin_object_id)
);

-- Objekt-Metadaten
CREATE TABLE data_meta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER REFERENCES structure_class(id),
    status INTEGER REFERENCES utils_status(id) DEFAULT {STATUS_IN_CREATION},
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    current_version INTEGER DEFAULT 0
);