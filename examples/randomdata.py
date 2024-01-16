import random
from datetime import datetime, timedelta

# Read sample data
with open('examples/data/sample_first_names.txt', 'r', encoding='utf-8') as file:
    FIRST_NAMES = [line.strip() for line in file.readlines()]
with open('examples/data/sample_last_names.txt', 'r', encoding='utf-8') as file:
    LAST_NAMES = [line.strip() for line in file.readlines()]
ALL_NAMES = [*FIRST_NAMES, *LAST_NAMES]

def get_random_datetime(start, end) -> datetime:
    """Returns random datetime between start and end """
    delta = end - start
    delta_secs = (delta.days * 24 * 60 * 60) + delta.seconds
    return start + timedelta(seconds=random.randrange(delta_secs))

def set_seed(seed):
    random.seed(seed)

def get_random_address():
    return {
        'street': f"{random.choice(ALL_NAMES)}{random.choice(['straße', 'weg'])}",
        'house_number': f"{random.randint(1, 500)}{random.choice(['', '', '', '', 'a', 'b', 'c', 'd'])}",
        'zip': f"{random.randint(10000, 99999)}",
        'city': f"{random.choice(ALL_NAMES)}{random.choice(['stadt', 'dorf', 'ingen', 'heim'])}"
    }

def get_random_person():
    return {
        'first_name': random.choice(FIRST_NAMES),
        'last_name': random.choice(LAST_NAMES),
        'birthday': get_random_datetime(datetime(1930, 1, 1), datetime.now()).date()
    }

def get_random_employee():
    person = get_random_person()
    random_dt = get_random_datetime(datetime(2002, 1, 1), datetime.now())
    person.update({
        'number': random.randint(1000, 9999),
        'entry_date': datetime(random_dt.year, random_dt.month, 1).date()
    })
    return person