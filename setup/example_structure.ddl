#int {
    INTEGER
}
#shorttext {
    VARCHAR(64)
}
#longtext {
    VARCHAR(256)
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
#datetime {
    DATETIME,
    get {
        return parse_sqlite_datetime(value)
    }
    set {
        return datetime_to_string(value)
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
#zipcode {
    VARCHAR(5)
}
#currency2 {
    INTEGER,
    get {
        return create_decimal(value, 2)
    }
    set {
        return get_decimal_base_value(value, 2)
    }
}
+attributes {
    first_name: shorttext,
    last_name: shorttext,
    number: int,
    street: shorttext,
    house_number: shorttext,
    zip: zipcode,
    city: shorttext,
    price: currency2,
    creation_time: datetime,
    product_name: longtext,
    amount: int,
    birthday: date
}
Person {
    first_name,
    last_name,
    birthday
}
Customer(Person) {
    street,
    house_number,
    zip,
    city
}
Product {
    product_name,
    price
}
OrderPosition {
    amount,
    ~position_to_product -> Product
}
Order {
    creation_time,
    ~order_to_customer -> Customer,
    ~order_to_positions -> OrderPosition
}