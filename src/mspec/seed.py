import random
import io
import datetime
import argparse

from PIL import Image, ImageDraw

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

def random_list(element_type:str, enum_choices=None, min=0, max=5) -> list:
    items = []
    for _ in range(random.randint(min, max)):
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

_MEDIA_INGEST_TABLES = {'file', 'image', 'master_image'}


def _make_minimal_png() -> bytes:
    """Create a 500x500 PNG with random text placed at random positions."""
    if random.choice([True, False]):
        bg_color = (255, 255, 255)
        text_color = (0, 0, 0)
    else:
        bg_color = (0, 0, 0)
        text_color = (255, 255, 255)
    img = Image.new('RGB', (1000, 1000), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    for word in random_list('str', min=1, max=7):
        x = random.randint(0, 800)
        y = random.randint(0, 950)
        draw.text((x, y), word, fill=text_color, font_size=random.randint(35, 150))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


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


def _ingest_for_table(ctx, spec: dict, ref_table_name: str):
    """
    Ingest a dummy media asset for a foreign key that points to a media table.
    Returns the new id string, or None on error.
    """
    try:
        if ref_table_name == 'file':
            file_system_module = spec['modules']['file_system']
            op = file_system_module['ops']['ingest_start']
            params_class, output_class = new_op_classes(op, file_system_module)
            content = b'seed file content'
            filename = 'seed-file.txt'
            ctx.self['file_input'] = content
            ctx.self['file_input_name'] = filename
            params = new_op_params(params_class, {
                'name': filename,
                'size': len(content),
                'parts': 1,
                'content_type': 'text/plain',
                'finish': True,
            })
            result = http_run_op(ctx, params_class, output_class, params)
            return str(result.result['file_id'])

        elif ref_table_name == 'image':
            media_module = spec['modules']['media']
            op = media_module['ops']['create_image']
            params_class, output_class = new_op_classes(op, media_module)
            content = _make_minimal_png()
            filename = 'seed-image.png'
            ctx.self['file_input'] = content
            ctx.self['file_input_name'] = filename
            params = new_op_params(params_class, {
                'name': filename,
                'content_type': 'image/png',
            })
            result = http_run_op(ctx, params_class, output_class, params)
            return str(result.result['image_id'])

        elif ref_table_name == 'master_image':
            media_module = spec['modules']['media']
            op = media_module['ops']['ingest_master_image']
            params_class, output_class = new_op_classes(op, media_module)
            content = _make_minimal_png()
            filename = 'seed-master-image.png'
            ctx.self['file_input'] = content
            ctx.self['file_input_name'] = filename
            params = new_op_params(params_class, {
                'name': filename,
                'content_type': 'image/png',
                'thumbnail_max_size': 1,
            })
            result = http_run_op(ctx, params_class, output_class, params)
            return str(result.result['master_image_id'])

    except Exception as e:
        print(f'  :: error ingesting {ref_table_name}: {e}')
        return None

    finally:
        ctx.self.pop('file_input', None)
        ctx.self.pop('file_input_name', None)


def _seed_foreign_model(ctx, spec: dict, ref_module_name: str, ref_table_name: str, _depth: int = 0):
    """
    Create a model in the referenced module/table and return its id string,
    or None on error. Circular foreign key references are not supported and
    are guarded against with a depth limit.
    """
    if _depth > 1:
        # print(f'  :: foreign key depth limit reached for {ref_module_name}.{ref_table_name}, skipping')
        return None
    try:
        ref_module = spec['modules'][ref_module_name]
        ref_model = ref_module['models'][ref_table_name]
        result = _create_model(ctx, spec, ref_module, ref_model, _depth=_depth + 1)
        if result is None:
            return None
        return str(result.id)
    except Exception as e:
        print(f'  :: error seeding foreign model {ref_module_name}.{ref_table_name}: {e}')
        return None


def _create_model(ctx, spec: dict, module: dict, model: dict, _depth: int = 0):
    """Build and POST a single random model. Returns the created model or None on error."""
    model_class = new_model_class(model, module)
    data = {}
    for field_name, field in model['fields'].items():
        snake_name = field['name']['snake_case']
        if field['type'] == 'foreign_key':
            references = field['references']
            ref_module_name = references['module']
            ref_table_name = references['table']
            if ref_table_name == 'user':
                # user_id is overridden server-side; use first example as placeholder
                data[snake_name] = str(field['examples'][0])
            elif ref_table_name in _MEDIA_INGEST_TABLES:
                new_id = _ingest_for_table(ctx, spec, ref_table_name)
                if new_id is None:
                    default = field.get('default')
                    if default is not None:
                        data[snake_name] = str(default)
                    else:
                        return None
                else:
                    data[snake_name] = new_id
            else:
                new_id = _seed_foreign_model(ctx, spec, ref_module_name, ref_table_name, _depth=_depth)
                if new_id is None:
                    default = field.get('default')
                    if default is not None:
                        data[snake_name] = str(default)
                    else:
                        return None
                else:
                    data[snake_name] = new_id
        elif field['type'] == 'list' and field.get('element_type') == 'foreign_key':
            references = field['references']
            ref_module_name = references['module']
            ref_table_name = references['table']
            ids = []
            if ref_table_name != 'user':
                for _ in range(random.randint(0, 3)):
                    if ref_table_name in _MEDIA_INGEST_TABLES:
                        new_id = _ingest_for_table(ctx, spec, ref_table_name)
                    else:
                        new_id = _seed_foreign_model(ctx, spec, ref_module_name, ref_table_name, _depth=_depth)
                    if new_id is not None:
                        ids.append(new_id)
            data[snake_name] = ids
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
                        _create_model(ctx, spec, module, model)

            else:
                ctx.client.headers.pop('Authorization', None)
                num_models = random.randint(min_models, max_models)
                print(f':: seeding {num_models} {model_path} models...')
                for _ in range(num_models):
                    _create_model(ctx, spec, module, model)

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
