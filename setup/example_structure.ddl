#void {
    NULL
}
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
        if value:
            return parse_sqlite_date(value)
        else:
            return None
    }
    set {
        if value:
            return date_to_string(value)
        else:
            return None
    }
}
#datetime {
    DATETIME,
    get {
        if value:
            return parse_sqlite_datetime(value)
        else:
            return None
    }
    set {
        if value:
            return datetime_to_string(value)
        else:
            return None
    }
}
#zipcode {
    VARCHAR(5)
}
#currency2 {
    INTEGER,
    get {
        if value:
            return create_decimal(value, 2)
        else:
            return None
    }
    set {
        if value:
            return get_decimal_base_value(value, 2)
        else:
            return None
    }
}
#array {
    BLOB,
    get {
        return bytes_to_array(value)
    }
    set {
        return array_to_bytes(value)
    }
}
#cbytes {
    BLOB,
    get {
        return decompress(value)
    }
    set {
        return compress(value)
    }
}
#cstring {
    #cbytes,
    get {
        return value.decode('utf-8')
    }
    set {
        return value.encode('utf-8')
    }
}
+attributes {
    first_name: shorttext,
    last_name: shorttext,
    full_name: void,
    number: int,
    street: shorttext,
    house_number: shorttext,
    zip: zipcode,
    city: shorttext,
    price: currency2,
    creation_time: datetime,
    name: longtext,
    amount: int,
    birthday: date,
    example_text: cstring
}
Person* {
    first_name,
    last_name,
    full_name {
        get {
            return this['first_name'] + ' ' + this['last_name']
        }
    },
    birthday
}
Customer*(Person) {
    street,
    house_number,
    zip,
    city
}
Product* {
    name,
    price
}
OrderPosition {
    amount,
    price {
        get {
            return this['amount'] * this.hop_first('position_to_product')['price']
        }
    },
    ~position_to_product -> Product(1)
}
Order {
    creation_time,
    price {
        get {
            return sum([position['price'] for position in this.hop('order_to_positions')])
        }
    },
    ~order_to_customer -> Customer(1),
    ~order_to_positions -> OrderPosition
}
TextObject {
    example_text
}