import random

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
    'random_enum',
    'random_list',
    'random_person_name',
    'random_user_name',
    'random_thing_name'
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

def random_enum(enum:list) -> str:
    return random.choice(enum)

def random_list() -> list:
    return random.choices(random_adjectives, k=random.randint(0, 5))

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
    elif num == 4:
        _words = []
        
        for i in range(random.randint(3, 4)):
            _word = random.choice(random_words)
            if random.randint(0, 2) == 0:
                _words.append(_word.upper())
            else:
                _words.append(_word)

        random.shuffle(_words)
        name = ' '.join(_words)

def random_thing_name() -> str:
    words = []
    for _ in range(random.randint(1, 3)):
        words.append(random.choice(random_adjectives))
    
    words.append(random.choice(random_nouns))

    return ' '.join(words)
