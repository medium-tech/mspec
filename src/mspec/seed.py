import random
import datetime
import argparse

from mapp.context import spec_from_env, get_context_from_env
from mapp.types import new_model_class, new_model, new_op_classes, new_op_params
from mapp.module.model.http import http_model_create
from mapp.module.op.http import http_run_op


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
    'random_person_name',
    'random_user_name',
    'random_thing_name',
    'random_email',
    'random_phone_number',

    'seed',
    'main',
]

#
# random data generators
#

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

def random_list(element_type:str, enum_choices=None) -> list:
    items = []
    for _ in range(random.randint(0, 5)):
        if enum_choices is not None:
            items.append(random.choice(enum_choices))
        elif element_type == 'str':
            items.append(random.choice(random_words))
        else:
            items.append(globals()[f'random_{element_type}']())
    return items

def random_datetime() -> datetime.datetime:
    return datetime.datetime.fromtimestamp(random.randint(1705900793, 1768972793))

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

#
# seeder internals
#

_SKIP_MODULES = {'auth', 'file_system', 'media'}


def _random_field_value(field: dict):
    """Return a random value for the given field spec."""
    random_func_name = field.get('random')
    if random_func_name:
        if not random_func_name.startswith('random_') or random_func_name not in __all__:
            raise ValueError(f'Invalid random function specified for field {field["name"]["snake_case"]}: {random_func_name}')
        return globals()[random_func_name]()
    if field['type'] == 'list':
        return random_list(field.get('element_type', 'str'))
    return random.choice(field['examples'])


def _has_unsupported_fields(model: dict) -> bool:
    """Return True if the model has non-user_id foreign_key fields."""
    for field_name, field in model['fields'].items():
        if field['type'] == 'foreign_key' and field_name != 'user_id':
            return True
    return False


def _create_model(ctx, module: dict, model: dict):
    """Build and POST a single random model. Returns the created model or None on error."""
    model_class = new_model_class(model, module)
    data = {}
    for field_name, field in model['fields'].items():
        snake_name = field['name']['snake_case']
        if field['type'] == 'foreign_key':
            # user_id is overridden server-side; use first example as placeholder
            data[snake_name] = str(field['examples'][0])
        else:
            data[snake_name] = _random_field_value(field)
    model_obj = new_model(model_class, data)
    try:
        return http_model_create(ctx, model_class, model_obj)
    except Exception as e:
        model_path = f'{module["name"]["snake_case"]}.{model["name"]["snake_case"]}'
        print(f'  :: error creating {model_path}: {e}')
        return None


def _seed_users(ctx, spec: dict, num_users: int) -> list:
    """
    Create num_users users via HTTP and return a list of (user_id, access_token) tuples.
    """
    auth_module = spec['modules'].get('auth')
    if auth_module is None:
        print(':: no auth module found, skipping user creation')
        return []

    create_user_op = auth_module['ops'].get('create_user')
    login_user_op = auth_module['ops'].get('login_user')

    if create_user_op is None or login_user_op is None:
        print(':: auth module missing create_user or login_user ops, skipping user creation')
        return []

    create_params_class, create_output_class = new_op_classes(create_user_op, auth_module)
    login_params_class, login_output_class = new_op_classes(login_user_op, auth_module)

    users = []
    # fixed password for all seeded users - intended for development environments only
    password = 'Seed_pass_1!'

    for i in range(num_users):
        name = random_person_name()
        email = random_email()

        create_params = new_op_params(create_params_class, {
            'name': name,
            'email': email,
            'password': password,
            'password_confirm': password,
        })

        try:
            create_result = http_run_op(ctx, create_params_class, create_output_class, create_params)
            user_id = create_result.result['id']
        except Exception as e:
            print(f'  :: error creating user {i + 1}/{num_users} ({email}): {e}')
            continue

        login_params = new_op_params(login_params_class, {
            'email': email,
            'password': password,
        })

        try:
            login_result = http_run_op(ctx, login_params_class, login_output_class, login_params)
            access_token = login_result.result['access_token']
            users.append((user_id, access_token))
            print(f'  :: created user {i + 1}/{num_users}: {email} (id: {user_id})')
        except Exception as e:
            print(f'  :: error logging in user {i + 1}/{num_users} ({email}): {e}')

    return users

#
# public seed function
#

def seed(ctx, spec: dict, num_users: int, min_models: int, max_models: int):
    """
    Seed random data into a running mapp application.

    args ::
        ctx         :: MappContext from get_context_from_env()
        spec        :: loaded app spec from spec_from_env()
        num_users   :: number of users to create
        min_models  :: minimum models to create per user / per model
        max_models  :: maximum models to create per user / per model
    """

    # create users #

    print(f':: creating {num_users} users...')
    users = _seed_users(ctx, spec, num_users)
    print(f':: created {len(users)}/{num_users} users')

    # seed models #

    spec_modules = spec['modules']

    for module_name, module in spec_modules.items():

        if module_name in _SKIP_MODULES:
            continue

        for model_name, model in module.get('models', {}).items():

            if model.get('hidden', False):
                continue

            model_path = f'{module["name"]["snake_case"]}.{model["name"]["snake_case"]}'
            require_login = model.get('auth', {}).get('require_login', False)

            if _has_unsupported_fields(model):
                print(f':: skipping {model_path}: has non-user_id foreign_key fields (not supported in seeder v1)')
                continue

            if require_login:

                if num_users == 0:
                    print(f':: skipping {model_path}: no users created (--users 0)')
                    continue

                max_per_user = model['auth'].get('max_models_per_user', -1)

                for user_id, access_token in users:
                    ctx.client.set_bearer_token(access_token)
                    num_models = random.randint(min_models, max_models)
                    if max_per_user >= 0:
                        num_models = min(num_models, max_per_user)
                    print(f':: seeding {num_models} {model_path} models for user {user_id}...')
                    for _ in range(num_models):
                        _create_model(ctx, module, model)

            else:
                ctx.client.headers.pop('Authorization', None)
                num_models = random.randint(min_models, max_models)
                print(f':: seeding {num_models} {model_path} models...')
                for _ in range(num_models):
                    _create_model(ctx, module, model)

#
# cli entry point
#

def main():

    # parse args #

    parser = argparse.ArgumentParser(
        prog='mspec.seed',
        description='Seed data for a mapp application using its spec'
    )
    parser.add_argument('--users', type=int, default=10,
                        help='Number of users to create (default: 10)')
    parser.add_argument('--min-models', type=int, default=0,
                        help='Minimum models to create per user/model (default: 0)')
    parser.add_argument('--max-models', type=int, default=25,
                        help='Maximum models to create per user/model (default: 25)')

    args = parser.parse_args()

    # load spec and context #

    spec = spec_from_env()
    ctx = get_context_from_env()

    seed(ctx, spec, num_users=args.users, min_models=args.min_models, max_models=args.max_models)


if __name__ == '__main__':
    main()
