import random
import datetime
from core.types import CID, Entity, Permission, entity_types, permission_types

__all__ = [
    'random_nouns',
    'random_adjectives',
    'random_words',

    'random_first_names',
    'random_last_names',

    'random_bool',
    'random_int',
    'random_float',
    'random_str',
    'random_str_enum',
    'random_list',
    'random_datetime',
    'random_cid',
    'random_entity',
    'random_permission',
    'random_person_name',
    'random_user_name',
    'random_thing_name',
    'random_email',
    'random_phone_number'
]

random_nouns = ['apple', 'banana', 'horse', 'iguana', 'jellyfish', 'kangaroo', 'lion', 'quail', 'rabbit', 'snake', 'tiger', 'x-ray', 'yak', 'zebra']
random_adjectives = ['shiny', 'dull', 'new', 'old', 'big', 'small', 'fast', 'slow', 'hot', 'cold', 'happy', 'sad', 'angry', 'calm', 'loud', 'quiet']
random_words = random_nouns + random_adjectives

random_first_names = ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Hank', 'Ivy', 'Jack', 'Kate', 'Liam', 'Mia', 'Noah', 'Olivia', 'Paul', 'Quinn', 'Ryan', 'Sara', 'Tom', 'Uma', 'Vince', 'Wendy', 'Xander', 'Yara', 'Zane']
random_last_names = ['Adams', 'Brown', 'Clark', 'Davis', 'Evans', 'Ford', 'Garcia', 'Hill', 'Irwin', 'Jones', 'King', 'Lee', 'Moore', 'Nolan', 'Owens', 'Perez', 'Quinn', 'Reed', 'Smith', 'Taylor', 'Upton', 'Vance', 'Wong', 'Xu', 'Young', 'Zhang']

def random_bool() -> bool:
    return random.choice([True, False])

def random_int(min:int=-100, max:int=100) -> int:
    return random.randint(min, max)

def random_float(min:float=-100.0, max:float=100.0, round_to=2) -> float:
    return round(random.uniform(min, max), round_to)

def random_str() -> str:
    return ' '.join(random.choices(random_words, k=random.randint(1, 5)))

def random_str_enum(enum:list) -> str:
    return random.choice(enum)

def random_list(element_type:str, enum_choies=None) -> list:
    items = []
    for _ in range(random.randint(0, 5)):
        if enum_choies is not None:
            items.append(random.choice(enum_choies))
        elif element_type == 'str':
            items.append(random.choice(random_words))
        else:
            items.append(globals()[f'random_{element_type}']())
    return items

def random_datetime() -> datetime.datetime:
    return datetime.datetime.fromtimestamp(random.randint(1705900793, 1768972793))

def random_cid() -> CID:
    return CID.from_string(random_str())

def random_entity() -> Entity:
    return Entity(random_cid(), random.choice(entity_types))

def random_permission() -> Permission:
    return Permission(
        read=random.choice(permission_types),
        write=random.choice(permission_types),
        delete=random.choice(permission_types)
    )

def random_person_name() -> str:
    first = random.choice(random_first_names)
    middle = random.choice(random_first_names)
    last = random.choice(random_last_names)

    name = ''
    if random.randint(0, 3) > 0:
        name += first
    else:
        name += first[0]

    middle_seed = random.randint(0, 5)
    if middle_seed == 0:
        name += ' ' + middle
    elif middle_seed < 2:
        name += ' ' + middle[0]
    else:
        name += ' '

    last_seed = random.randint(0, 5)
    if last_seed == 0:
        pass
    elif last_seed < 2:
        name += ' ' + last[0]
    else:
        name += ' ' + last
    
    return name

def random_user_name() -> str:
    num = random.randint(1, 4)
    if num == 1:
        name = random.choice(random_adjectives) + ' ' + random.choice(random_nouns)
    elif num == 2:
        name = ('The ' + random.choice(random_nouns) + ' ' + random.choice(random_nouns)).title()
    elif num == 3:
        name = random.choice(random_words).title()
        if random.randint(0, 2) == 0:
            name += f'_{random.randint(1, 100)}'
    else:
        _words = []
        
        for i in range(random.randint(3, 4)):
            _word = random.choice(random_words)
            if random.randint(0, 2) == 0:
                _words.append(_word.upper())
            else:
                _words.append(_word)

        random.shuffle(_words)
        name = ' '.join(_words)

    return name

def random_thing_name() -> str:
    words = []
    for _ in range(random.randint(1, 3)):
        words.append(random.choice(random_adjectives))
    
    words.append(random.choice(random_nouns))

    return ' '.join(words)

def random_email() -> str:
    user_name = random_user_name().replace(' ', '_')
    domain = random.choice(random_words)
    tld = random.choice(['com', 'net', 'org', 'io', 'ai'])
    return f'{user_name}@{domain}.{tld}'

def random_phone_number() -> str:
    country_code = random.randint(1, 99)
    area_code = random.randint(100, 999)
    exchange = random.randint(100, 999)
    number = random.randint(1000, 9999)
    return f'+{country_code} ({area_code}) {exchange}-{number}'
