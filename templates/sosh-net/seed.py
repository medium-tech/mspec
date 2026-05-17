#! /usr/bin/env python3
import random

from dotenv import load_dotenv

from mapp.context import get_context_from_env, spec_from_env
from mapp.module.model.http import http_model_create, http_model_read
from mapp.module.op.http import http_run_op
from mapp.types import new_model, new_model_class, new_op_classes, new_op_params

from mspec.seed import (
    random_email, 
    random_image, 
    random_person_name, 
    random_str, 
    random_str_rich_text, 
    random_user_name, 
    random_list_of_words
)


NUM_USERS = 33
ITEMS_PER_ROUND = 5
SEED_PASSWORD = 'Seed_pass_1!'
REACTION_TYPES = ['🙂', '❤️', '😂', '👍', '👎', '😢', '😡', '😬', '🥱', '😮', '🤔']


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
        try:
            create_result = http_run_op(ctx, create_params_class, create_output_class, create_params)
        except Exception as e:
            print(f'  :: failed to create user {i + 1}/{num_users}: {email}, error: {e}')
            raise e

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
    """Create a master image via media ingest and return its id."""
    media_module = spec['modules']['media']
    ingest_op = media_module['ops']['ingest_master_image']
    ingest_params_class, ingest_output_class = new_op_classes(ingest_op, media_module)

    try:
        ctx.self['file_input'] = random_image()
        ctx.self['file_input_name'] = image_name
        ingest_params = new_op_params(ingest_params_class, {'name': image_name})
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
        print('  :: seeding profile for user {}/{} with profile picture {}'.format(i + 1, len(users), profile_picture))
        while True:
            try:
                profile_data = {
                    'user_id': '-1',
                    'username': random_user_name(max_length=25),
                    'bio': random_str_rich_text(),
                    'profile_picture': profile_picture,
                }
                profile = new_model(profile_class, profile_data)
                http_model_create(ctx, profile_class, profile)
                break
            except Exception as e:
                if 'Another record with the same value exists' in str(e):
                    print('   :: username conflict, retrying with a new username...')
                    continue
                else:
                    raise e


def _seed_forums(ctx, social_module: dict, users: list[dict], num_forums: int):
    forum_model = social_module['models']['forum']
    forum_class = new_model_class(forum_model, social_module)

    for user in users:
        ctx.client.set_bearer_token(user['access_token'])
        for i in range(num_forums):
            forum_data = {
                'user_id': '-1',
                'topic': f'{random_str().title()}',
                'description': random_str_rich_text(),
                'tags': random_list_of_words(0, 5),
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
                'title': f'{random_str().title()}',
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


def _seed_reactions(ctx, social_module: dict, users: list[dict], num_threads: int, num_replies: int):
    thread_model = social_module['models']['thread']
    thread_class = new_model_class(thread_model, social_module)

    get_replies_op = social_module['ops']['get_replies_for_post']
    get_replies_params_class, get_replies_output_class = new_op_classes(get_replies_op, social_module)

    react_to_thread_op = social_module['ops']['react_to_thread_main_post']
    react_to_thread_params_class, react_to_thread_output_class = new_op_classes(react_to_thread_op, social_module)

    react_to_reply_op = social_module['ops']['react_to_reply']
    react_to_reply_params_class, react_to_reply_output_class = new_op_classes(react_to_reply_op, social_module)

    thread_ids = []
    for thread_id in range(1, num_threads + 1):
        try:
            http_model_read(ctx, thread_class, str(thread_id))
            thread_ids.append(str(thread_id))
        except Exception as e:
            print(f'  :: skipping thread {thread_id} while seeding reactions: {e}')
            continue

    ctx.client.set_bearer_token(users[0]['access_token'])
    first_thread = http_model_read(ctx, thread_class, '1')
    main_post_id = str(first_thread.main_post_id)

    get_replies_params = new_op_params(get_replies_params_class, {
        'post_id': main_post_id,
        'offset': 0,
        'size': num_replies,
    })
    replies_result = http_run_op(ctx, get_replies_params_class, get_replies_output_class, get_replies_params)
    reply_ids = [str(reply['id']) for reply in replies_result.result.get('replies', [])]

    for user in users:
        ctx.client.set_bearer_token(user['access_token'])

        for thread_id in thread_ids:
            react_to_thread_params = new_op_params(react_to_thread_params_class, {
                'thread_id': thread_id,
                'reaction_type': random.choice(REACTION_TYPES),
            })
            http_run_op(ctx, react_to_thread_params_class, react_to_thread_output_class, react_to_thread_params)

        for reply_id in reply_ids:
            react_to_reply_params = new_op_params(react_to_reply_params_class, {
                'post_id': reply_id,
                'reaction_type': random.choice(REACTION_TYPES),
            })
            http_run_op(ctx, react_to_reply_params_class, react_to_reply_output_class, react_to_reply_params)


def seed():
    load_dotenv()
    ctx = get_context_from_env()
    spec = spec_from_env()

    social_module = spec['modules']['social']

    print(f':: round 1/5: creating {NUM_USERS} user accounts and profiles...')
    users = _create_users_with_tokens(ctx, spec, NUM_USERS)
    print(f'    :: seeding profiles for {NUM_USERS} users...')
    _seed_profiles(ctx, spec, social_module, users)

    print(f':: round 2/5: creating {ITEMS_PER_ROUND} forums per user...')
    _seed_forums(ctx, social_module, users, ITEMS_PER_ROUND)

    print(f':: round 3/5: creating {ITEMS_PER_ROUND} threads per user in forum 1...')
    _seed_threads_in_forum_1(ctx, social_module, users, ITEMS_PER_ROUND)

    print(f':: round 4/5: creating {ITEMS_PER_ROUND} replies per user in the first thread of forum 1...')
    _seed_replies_in_first_thread(ctx, social_module, users, ITEMS_PER_ROUND)

    print(f':: round 5/5: creating 1 random reaction per user for first {ITEMS_PER_ROUND} threads and first {ITEMS_PER_ROUND} replies in thread 1...')
    _seed_reactions(ctx, social_module, users, ITEMS_PER_ROUND, ITEMS_PER_ROUND)

    print(':: seed workflow complete')


def main():
    seed()


if __name__ == '__main__':
    main()
