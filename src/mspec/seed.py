import random
import argparse

import mapp.seed as seed_funcs

from mapp.context import spec_from_env, get_context_from_env
from mapp.types import new_model_class, new_model, new_op_classes, new_op_params
from mapp.module.model.http import http_model_create
from mapp.module.op.http import http_run_op


__all__ = ['main']


_SKIP_MODULES = {'auth', 'file_system', 'media'}


def _random_field_value(field: dict):
    """Return a random value for the given field spec."""
    random_func_name = field.get('random')
    if random_func_name:
        return getattr(seed_funcs, random_func_name)()
    if field['type'] == 'list':
        return seed_funcs.random_list(field.get('element_type', 'str'))
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
        name = seed_funcs.random_person_name()
        email = seed_funcs.random_email()

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


def main():

    # parse args #

    parser = argparse.ArgumentParser(
        prog='mspec.seed',
        description='Seed data for a mapp application using its spec'
    )
    parser.add_argument('--users', type=int, default=5,
                        help='Number of users to create (default: 5)')
    parser.add_argument('--min-models', type=int, default=0,
                        help='Minimum models to create per user/model (default: 0)')
    parser.add_argument('--max-models', type=int, default=10,
                        help='Maximum models to create per user/model (default: 10)')

    args = parser.parse_args()

    # load spec and context #

    spec = spec_from_env()
    ctx = get_context_from_env()

    # create users #

    print(f':: creating {args.users} users...')
    users = _seed_users(ctx, spec, args.users)
    print(f':: created {len(users)}/{args.users} users')

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

                if args.users == 0:
                    print(f':: skipping {model_path}: no users created (--users 0)')
                    continue

                for user_id, access_token in users:
                    ctx.client.set_bearer_token(access_token)
                    num_models = random.randint(args.min_models, args.max_models)
                    print(f':: seeding {num_models} {model_path} models for user {user_id}...')
                    for _ in range(num_models):
                        _create_model(ctx, module, model)

            else:
                ctx.client.headers.pop('Authorization', None)
                num_models = random.randint(args.min_models, args.max_models)
                print(f':: seeding {num_models} {model_path} models...')
                for _ in range(num_models):
                    _create_model(ctx, module, model)


if __name__ == '__main__':
    main()
