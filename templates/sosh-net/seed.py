#! /usr/bin/env python3
from dotenv import load_dotenv

from mapp.context import get_context_from_env, spec_from_env
from mapp.module.model.http import http_model_create, http_model_read
from mapp.module.op.http import http_run_op
from mapp.types import new_model, new_model_class, new_op_classes, new_op_params

from mspec.seed import random_email, random_image, random_person_name, random_str, random_str_rich_text, random_user_name


NUM_USERS = 5
ITEMS_PER_ROUND = 6
SEED_PASSWORD = 'Seed_pass_1!'


def _make_username(index: int) -> str:
    base = random_user_name().lower().replace(' ', '_').replace('-', '_')
    username = f'{base}_{index}'
    return username[:25]


def _create_users_with_tokens(ctx, spec: dict, num_users: int) -> list[dict]:
    auth_module = spec['modules']['auth']
    create_user_op = auth_module['ops']['create_user']
    login_user_op = auth_module['ops']['login_user']

    create_params_class, create_output_class = new_op_classes(create_user_op, auth_module)
    login_params_class, login_output_class = new_op_classes(login_user_op, auth_module)

    users = []

    for i in range(num_users):
        email = f'seed-{i}-{random_email()}'

        create_params = new_op_params(create_params_class, {
            'name': random_person_name(),
            'email': email,
            'password': SEED_PASSWORD,
            'password_confirm': SEED_PASSWORD,
        })
        create_result = http_run_op(ctx, create_params_class, create_output_class, create_params)

        login_params = new_op_params(login_params_class, {
            'email': email,
            'password': SEED_PASSWORD,
        })
        login_result = http_run_op(ctx, login_params_class, login_output_class, login_params)

        user = {
            'id': str(create_result.result['id']),
            'email': email,
            'access_token': login_result.result['access_token'],
        }
        users.append(user)
        print(f'  :: created user {i + 1}/{num_users}: {email}')

    return users


def _create_master_image(ctx, spec: dict, image_name: str) -> str:
    media_module = spec['modules']['media']
    ingest_op = media_module['ops']['ingest_master_image']
    ingest_params_class, ingest_output_class = new_op_classes(ingest_op, media_module)

    try:
        ctx.self['file_input'] = random_image()
        ctx.self['file_input_name'] = image_name
        ingest_params = new_op_params(ingest_params_class, {
            'name': image_name,
            'content_type': 'image/png',
            'thumbnail_max_size': 1,
        })
        image_result = http_run_op(ctx, ingest_params_class, ingest_output_class, ingest_params)
        return str(image_result.result['master_image_id'])
    finally:
        ctx.self.pop('file_input', None)
        ctx.self.pop('file_input_name', None)


def _seed_profiles(ctx, spec: dict, social_module: dict, users: list[dict]):
    profile_model = social_module['models']['profile']
    profile_class = new_model_class(profile_model, social_module)

    for i, user in enumerate(users):
        ctx.client.set_bearer_token(user['access_token'])
        profile_picture = _create_master_image(ctx, spec, f'seed-profile-{i}.png')
        profile_data = {
            'user_id': '-1',
            'username': _make_username(i),
            'bio': random_str_rich_text(),
            'profile_picture': profile_picture,
        }
        profile = new_model(profile_class, profile_data)
        http_model_create(ctx, profile_class, profile)


def _seed_forums(ctx, social_module: dict, users: list[dict], num_forums: int):
    forum_model = social_module['models']['forum']
    forum_class = new_model_class(forum_model, social_module)

    for user in users:
        ctx.client.set_bearer_token(user['access_token'])
        for i in range(num_forums):
            forum_data = {
                'user_id': '-1',
                'topic': f'{random_str().title()} Forum {i + 1}',
                'description': random_str_rich_text(),
                'tags': [random_str(), random_str()],
            }
            forum = new_model(forum_class, forum_data)
            http_model_create(ctx, forum_class, forum)


def _seed_threads_in_forum_1(ctx, social_module: dict, users: list[dict], num_threads: int):
    create_thread_op = social_module['ops']['create_thread']
    params_class, output_class = new_op_classes(create_thread_op, social_module)

    for user in users:
        ctx.client.set_bearer_token(user['access_token'])
        for i in range(num_threads):
            params = new_op_params(params_class, {
                'forum_id': '1',
                'title': f'{random_str().title()} Thread {i + 1}',
                'message': random_str_rich_text(),
                'attachments': [],
                'images': [],
            })
            http_run_op(ctx, params_class, output_class, params)


def _seed_replies_in_first_thread(ctx, social_module: dict, users: list[dict], num_replies: int):
    thread_model = social_module['models']['thread']
    post_model = social_module['models']['post']
    thread_class = new_model_class(thread_model, social_module)
    post_class = new_model_class(post_model, social_module)

    ctx.client.set_bearer_token(users[0]['access_token'])
    first_thread = http_model_read(ctx, thread_class, '1')
    main_post_id = str(first_thread.main_post_id)

    for user in users:
        ctx.client.set_bearer_token(user['access_token'])
        for _ in range(num_replies):
            reply_data = {
                'user_id': '-1',
                'forum_id': '1',
                'reply_to': main_post_id,
                'message': random_str_rich_text(),
                'attachments': [],
                'images': [],
                'related_posts': [],
            }
            reply = new_model(post_class, reply_data)
            http_model_create(ctx, post_class, reply)


def seed():
    load_dotenv()
    ctx = get_context_from_env()
    spec = spec_from_env()

    social_module = spec['modules']['social']

    print(f':: round 1/4: creating {NUM_USERS} user accounts and profiles...')
    users = _create_users_with_tokens(ctx, spec, NUM_USERS)
    _seed_profiles(ctx, spec, social_module, users)

    print(f':: round 2/4: creating {ITEMS_PER_ROUND} forums per user...')
    _seed_forums(ctx, social_module, users, ITEMS_PER_ROUND)

    print(f':: round 3/4: creating {ITEMS_PER_ROUND} threads per user in forum 1...')
    _seed_threads_in_forum_1(ctx, social_module, users, ITEMS_PER_ROUND)

    print(f':: round 4/4: creating {ITEMS_PER_ROUND} replies per user in the first thread of forum 1...')
    _seed_replies_in_first_thread(ctx, social_module, users, ITEMS_PER_ROUND)

    print(':: seed workflow complete')


def main():
    seed()


if __name__ == '__main__':
    main()
