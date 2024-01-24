#int {
    INTEGER
}
#text100 {
    VARCHAR(100)
}
#text {
    TEXT
}
#date {
    DATE,
    get {
        return parse_sqlite_date(value)
    }
    set {
        return date_to_string(value)
    }
}
#array {
    BLOB,
    get {
        return bytes_to_array(decompress(value))
    }
    set {
        return compress(array_to_bytes(value))
    }
}
+attributes {
    first_name: text100,
    last_name: text100,
    number: int,
    street: text100,
    house_number: text100,
    zip: text100,
    city: text100,
    birthday: date,
    entry_date: date,
    some_numbers: array
}
Address {
    street,
    house_number,
    zip {
        get {
            return 'PLZ ' + str(value)
        }
        set {
            return str(value).replace('PLZ ', '')
        }
    },
    city
}
Person {
    first_name,
    last_name,
    birthday,
    ~person_to_address -> Address
}
Employee(Person) {
    number*,
    entry_date,
    ~manager_to_employees -> Employee
}
ArrayData {
    some_numbers
}