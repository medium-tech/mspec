import os
import sys
import unittest
import fnmatch
import json
import subprocess
import glob
import re
import multiprocessing
import hashlib
import shutil
import jwt
import uuid

from pathlib import Path
from copy import deepcopy
from typing import Optional, Generator
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from collections import defaultdict

from mspec.core import load_generator_spec

from dotenv import dotenv_values

def seed_pagination_item(unique_id, base_cmd, seed_cmd, env, require_auth, model_data):
    if require_auth:

        # it will create a user for each item because some models
        # have a max number of items per user.
        # this can be optimized

        try:
            del env['MAPP_CLI_SESSION_FILE']
        except KeyError:
            pass

        try:
            del env['MAPP_CLI_ACCESS_TOKEN']
        except KeyError:
            pass

        # create user #

        user_data = {
            'name': f'user {unique_id}', 
            'email': f'user.{unique_id}@example.com', 
            'password': 'password123', 
            'password_confirm': 'password123'
        }
        create_user_cmd = base_cmd + ['auth', 'create-user', 'run', json.dumps(user_data)]
        result = subprocess.run(create_user_cmd, capture_output=True, text=True, env=env, timeout=10)
        if result.returncode != 0:
            raise RuntimeError(f'Error creating user for pagination seeding:\n{result.stdout + result.stderr}')
        
        user_id = json.loads(result.stdout)['result']['id']
        model_data['user_id'] = user_id
        
        # login user #

        login_data = {
            'email': user_data['email'],
            'password': user_data['password']
        }
        login_user_cmd = base_cmd + ['auth', 'login-user', 'run', json.dumps(login_data), '--show', '--no-session']
        result = subprocess.run(login_user_cmd, capture_output=True, text=True, env=env, timeout=10)
        if result.returncode != 0:
            raise RuntimeError(f'Error logging in user for pagination seeding:\n{result.stdout + result.stderr}')
        
        access_token = json.loads(result.stdout)['result']['access_token']

        env['MAPP_CLI_ACCESS_TOKEN'] = access_token
        
    seed_cmd.append(json.dumps(model_data))

    return run_cmd(seed_cmd, env)

def run_cmd(cmd_args, env):
    result = subprocess.run(cmd_args, capture_output=True, text=True, env=env, timeout=10)
    return (cmd_args, result.returncode, result.stdout, result.stderr)

def example_from_model(model:dict, index=0) -> dict:
    data = {}
    for field_name, field in model.get('fields', {}).items():
        try:
            value = field['examples'][index]
        except (IndexError, KeyError):
            raise ValueError(f'No example for field "{model["name"]["pascal_case"]}.{field_name}" at index {index}')
        
        if field['unique'] is True:
            data[field_name] = f'unique string - {uuid.uuid4()}'
        else:
            data[field_name] = value

    return data

def model_validation_errors(model:dict) -> Generator[tuple[dict, str], None, None]:
    """
    Generate invalid examples for a model based on its field validation errors.
    Yields tuples of (invalid_example_dict, field_name) for each validation error.
    """
    example = example_from_model(model)

    for field_name, field in model.get('fields', {}).items():
        for invalid_value in field.get('validation_errors', []):
            invalid_example = deepcopy(example)
            invalid_example[field_name] = invalid_value
            yield invalid_example, field_name

def request(ctx:dict, method:str, endpoint:str, request_body:Optional[dict]=None, decode_json=True) -> tuple[int, dict]:
    """send request and returnn status code and response body as dict"""

    req = Request(
        ctx['MAPP_CLIENT_HOST'] + endpoint,
        method=method, 
        headers=ctx['headers'], 
        data=request_body,
    )

    try:
        with urlopen(req, timeout=10) as response:
            body = response.read().decode('utf-8')
            status = response.status

    except TimeoutError as e:
        raise RuntimeError(f'TimeoutError on {method} {endpoint}: {e}')
        
    except HTTPError as e:
        body = e.read().decode('utf-8')
        status = e.code
    
    if decode_json:
        try:
            response_data = json.loads(body)
            return status, response_data
        except json.JSONDecodeError as e:
            raise RuntimeError(f'Invalid JSON from {method} {endpoint}, resp length: {len(body)}: {body}')
    else:
        return status, body

def env_to_string(env:dict) -> str:
    out = ''
    for key, value in env.items():
        if ' ' in value:
            out += f'{key}="{value}"\n'
        else:
            out += f'{key}={value}\n'
    return out

def run_cli_crud_for_model(module_name_kebab, model_name, model, command_type, cmd, crud_ctx, create_user, create_user_env, other_user, other_user_env):

    logged_out_ctx = crud_ctx.copy()
    hidden = model['hidden']
    require_login = model['auth']['require_login']
    model_name_kebab = model['name']['kebab_case']
    max_models = model['auth']['max_models_per_user']
    model_db_args = cmd + [module_name_kebab, model_name_kebab, command_type]

    ctx = create_user_env if require_login else crud_ctx

    #
    # create
    #

    example_to_create = example_from_model(model)
    create_args = model_db_args + ['create', json.dumps(example_to_create)]
    created_model_id = '1'

    if hidden:
        _, code, stdout, stderr = run_cmd(create_args, ctx)
        assert code == 2, f'expected 2 got {code} for command "{" ".join(create_args)}" output: {stdout + stderr}'

    else:
        if require_login:
            _, code, stdout, stderr = run_cmd(create_args, logged_out_ctx)
            assert code == 1, f'expected 1 got {code} for command "{" ".join(create_args)}" output: {stdout + stderr}'

        num_to_create = 1 if max_models < 0 else max_models

        for n in range(num_to_create):
            _, code, stdout, stderr = run_cmd(create_args, ctx)
            assert code == 0, f'expected 0 got {code} for command "{" ".join(create_args)}" output: {stdout + stderr}'
            created_model = json.loads(stdout)
            created_model_id = created_model.pop('id')
            if require_login:
                example_to_create['user_id'] = create_user['id']
            assert created_model == example_to_create, f'Created {model_name} does not match example data {n=}'

        if max_models >= 0:
            _, code, stdout, stderr = run_cmd(create_args, ctx)
            assert code == 1, f'expected 1 got {code} for command "{" ".join(create_args)}" output: {stdout + stderr}'

        if max_models == 0:
            return

    #
    # read
    #

    read_args = model_db_args + ['read', str(created_model_id)]

    if hidden:
        _, code, stdout, stderr = run_cmd(read_args, ctx)
        assert code == 2, f'expected 2 got {code} for command "{" ".join(read_args)}" output: {stdout + stderr}'

    else:
        if require_login:
            _, code, stdout, stderr = run_cmd(read_args, logged_out_ctx)
            assert code == 1, f'expected 1 got {code} for command "{" ".join(read_args)}" output: {stdout + stderr}'

        _, code, stdout, stderr = run_cmd(read_args, ctx)
        assert code == 0, f'expected 0 got {code} for command "{" ".join(read_args)}" output: {stdout + stderr}'
        read_model = json.loads(stdout)
        read_model_id = read_model.pop('id')
        assert read_model == example_to_create, f'Read {model_name} does not match example data'
        assert read_model_id == created_model_id, f'Read {model_name} ID does not match created ID'

        if require_login:
            assert read_model['user_id'] is not None, f'Read {model_name} user_id is None'
            assert read_model['user_id'] == create_user['id'], f'Read {model_name} ID does not match created ID'

    #
    # update
    #

    try:
        updated_example = example_from_model(model, index=1)
    except ValueError as e:
        raise ValueError(f'Need at least 2 examples for update testing: {e}')

    if require_login:
        updated_example['user_id'] = create_user['id']

    update_args = model_db_args + ['update', created_model_id, json.dumps(updated_example)]

    if hidden:
        _, code, stdout, stderr = run_cmd(update_args, ctx)
        assert code == 2, f'expected 2 got {code} for command "{" ".join(update_args)}" output: {stdout + stderr}'

    else:
        if require_login:
            _, code, stdout, stderr = run_cmd(update_args, logged_out_ctx)
            assert code == 1, f'expected 1 got {code} for command "{" ".join(update_args)}" output: {stdout + stderr}'
            _, code, stdout, stderr = run_cmd(update_args, other_user_env)
            assert code == 1, f'expected 1 got {code} for command "{" ".join(update_args)}" output: {stdout + stderr}'

        _, code, stdout, stderr = run_cmd(update_args, ctx)
        assert code == 0, f'expected 0 got {code} for command "{" ".join(update_args)}" output: {stdout + stderr}'
        updated_model = json.loads(stdout)
        updated_model_id = updated_model.pop('id')
        assert updated_model == updated_example, f'Updated {model_name} does not match updated example data'
        assert updated_model_id == created_model_id, f'Updated {model_name} ID does not match created ID'

        if require_login:
            assert updated_model['user_id'] is not None, f'Updated {model_name} user_id is None'
            assert updated_model['user_id'] == create_user['id'], f'Updated {model_name} ID does not match created ID'

    #
    # delete
    #

    delete_args = model_db_args + ['delete', str(created_model_id)]

    if hidden:
        _, code, stdout, stderr = run_cmd(delete_args, ctx)
        assert code == 2, f'expected 2 got {code} for command "{" ".join(delete_args)}" output: {stdout + stderr}'

    else:
        if require_login:
            _, code, stdout, stderr = run_cmd(delete_args, logged_out_ctx)
            assert code == 1, f'expected 1 got {code} for command "{" ".join(delete_args)}" output: {stdout + stderr}'
            _, code, stdout, stderr = run_cmd(delete_args, other_user_env)
            assert code == 1, f'expected 1 got {code} for command "{" ".join(delete_args)}" output: {stdout + stderr}'

        _, code, stdout, stderr = run_cmd(delete_args, ctx)
        assert code == 0, f'expected 0 got {code} for command "{" ".join(delete_args)}" output: {stdout + stderr}'
        delete_output = json.loads(stdout)
        assert delete_output['acknowledged'], f'Delete {model_name} ID did not return acknowledgement'
        expected_delete_msg = f'{model["name"]["snake_case"]} {created_model_id} has been deleted'
        assert delete_output['message'].startswith(expected_delete_msg), f'Delete {model_name} ID did not return correct message'

        # confirm delete is idempotent #

        _, code, stdout, stderr = run_cmd(model_db_args + ['delete', str(created_model_id)], ctx)
        assert code == 0, f'expected 0 got {code} for command "{" ".join(model_db_args + ["delete", str(created_model_id)])}" output: {stdout + stderr}'
        delete_output = json.loads(stdout)
        assert delete_output['message'].startswith(expected_delete_msg), f'Delete {model_name} ID did not return correct message'

    # read after delete #

    if not hidden:
        _, code, stdout, stderr = run_cmd(model_db_args + ['read', str(created_model_id)], ctx)
        assert code == 1, f'expected 1 got {code} for command "{" ".join(model_db_args + ["read", str(created_model_id)])}" output: {stdout + stderr}'
        try:
            read_output_err = json.loads(stdout)['error']
            assert read_output_err['code'] == 'NOT_FOUND', f'Read after delete for {model_name} did not return NOT_FOUND code for id {created_model_id}'
            assert read_output_err['message'] == f'{model["name"]["snake_case"]} {created_model_id} not found', f'Read after delete for {model_name} did not return correct message for id {created_model_id}'
        except KeyError as e:
            raise RuntimeError(f'KeyError {e} while reading after delete for {model_name} id {created_model_id}: {stdout + stderr}')
        except json.JSONDecodeError as e:
            raise RuntimeError(f'JSONDecodeError {e} while reading after delete for {model_name} id {created_model_id}: {stdout + stderr}')

    #
    # isolation between users
    #

    if require_login:
        assert create_user['id'] is not None, 'Create user ID is None, test setup error'
        assert other_user['id'] is not None, 'Other user ID is None, test setup error'
        assert create_user['id'] != other_user['id'], 'Alice and Bob users have the same ID, test setup error'
        assert create_user_env['MAPP_CLI_ACCESS_TOKEN'] != other_user_env['MAPP_CLI_ACCESS_TOKEN'], 'Alice and Bob have the same access token, test setup error'

def run_server_crud_for_model(module_name_kebab, model_name, model, base_ctx, logged_out_ctx, alice_ctx, bob_ctx, charlie_ctx, alice_user, bob_user, charlie_user):

    hidden = model['hidden']
    require_login = model['auth']['require_login']
    model_name_kebab = model['name']['kebab_case']
    max_models = model['auth']['max_models_per_user']

    #
    # create
    #

    example_to_create = example_from_model(model)
    create_args = [
        'POST',
        f'/api/{module_name_kebab}/{model_name_kebab}',
        json.dumps(example_to_create).encode()
    ]

    if require_login and not hidden:
        created_status, data = request(logged_out_ctx, *create_args)
        assert created_status == 401, f'Create {model_name} without login did not return 401 Unauthorized, response: {data}'
        ctx = alice_ctx
    else:
        ctx = base_ctx

    num_to_create = 1 if max_models < 0 else max_models
    created_model_id = '1'

    for n in range(num_to_create):
        created_status, created_model = request(ctx, *create_args)

        if hidden:
            assert created_status == 404, f'Create hidden {model_name} did not return 404 Not Found, {n=} response: {created_model}'

        else:
            assert created_status == 200, f'Create {model_name} did not return status 200 OK, {n=} response: {created_model}'
            created_model_id = created_model.pop('id')
            if require_login:
                example_to_create['user_id'] = alice_user['id']
            assert created_model == example_to_create, f'Created {model_name} (id: {created_model_id} n: {n}) does not match example data'

    if max_models >= 0:
        max_created_status, max_created_model = request(ctx, *create_args)
        assert max_created_status == 400, f'Create {model_name} beyond max_models_per_user did not return 400 Bad Request, response: {max_created_model}'

    if max_models == 0:
        # remaining tests not applicable
        return

    max_models_by_field = model['auth'].get('max_models_by_field', {})
    if max_models_by_field and not hidden and require_login:
        by_field_status, by_field_model = request(ctx, *create_args)
        assert by_field_status == 400, f'Create {model_name} beyond max_models_by_field did not return 400 Bad Request, response: {by_field_model}'
        assert by_field_model.get('error', {}).get('code') == 'MAX_MODELS_BY_FIELD_EXCEEDED', f'Expected MAX_MODELS_BY_FIELD_EXCEEDED error code, got: {by_field_model}'

    has_unique_fields = any(f.get('unique') for f in model.get('fields', {}).values())
    if has_unique_fields and not hidden:
        # use charlie ctx because in the event that max_models_per_user is 1, alice and bob have already created one
        # in these tests so the following call would fail with a different error
        unique_status, unique_model = request(charlie_ctx, *create_args)
        assert unique_status == 400, f'Create {model_name} with duplicate unique field did not return 400 Bad Request, response: {unique_model}'
        assert unique_model.get('error', {}).get('code') == 'UNIQUE_CONSTRAINT_VIOLATED', f'Expected UNIQUE_CONSTRAINT_VIOLATED error code, got: {unique_model}'

    #
    # read
    #

    if require_login and not hidden:
        read_status, data = request(logged_out_ctx, 'GET', f'/api/{module_name_kebab}/{model_name_kebab}/{1}', None)
        assert read_status == 401, f'Read {model_name} without login did not return 401 Unauthorized, response: {data}'

    read_status, read_model = request(ctx, 'GET', f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}', None)

    if hidden:
        assert read_status == 404, f'Read hidden {model_name} id: {created_model_id} did not return 404 Not Found, response: {read_model}'

    else:
        assert read_status == 200, f'Read {model_name} id: {created_model_id} did not return status 200 OK, response: {read_model}'
        read_model_id = read_model.pop('id')
        assert read_model == example_to_create, f'Read {model_name} id: {read_model_id} does not match example data'
        assert read_model_id == created_model_id, f'Read {model_name} id: {read_model_id} does not match created id: {created_model_id}'

    #
    # update
    #

    try:
        updated_example = example_from_model(model, index=1)
    except ValueError as e:
        raise ValueError(f'Need at least 2 examples for update testing: {e}')

    if require_login and not hidden:
        updated_example['user_id'] = alice_user['id']

        # logged out cannot update #

        update_status, data = request(
            logged_out_ctx,
            'PUT',
            f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
            json.dumps(updated_example).encode()
        )
        assert update_status == 401, f'Update {model_name} without login did not return 401 Unauthorized, response: {data}'

        # bob cannot update alice's model #

        update_status, data = request(
            bob_ctx,
            'PUT',
            f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
            json.dumps(updated_example).encode()
        )
        assert update_status == 401, f'Update {model_name} by non-owner did not return 401 Unauthorized, response: {data}'

        # read back to confirm not updated #

        read_status, read_model = request(ctx, 'GET', f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}', None)
        assert read_status == 200, f'Read {model_name} id: {created_model_id} did not return status 200 OK, response: {read_model}'
        read_model_id = read_model.pop('id')
        assert read_model == example_to_create, f'Read {model_name} id: {read_model_id} does not match example data after failed update attempt'

    # send request #

    updated_status, updated_model = request(
        ctx,
        'PUT',
        f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
        json.dumps(updated_example).encode()
    )

    if hidden:
        assert updated_status == 404, f'Update hidden {model_name} id: {created_model_id} did not return 404 Not Found, response: {updated_model}'
        updated_model_id = '1'

    else:
        assert updated_status == 200, f'Update {model_name} id: {created_model_id} did not return status 200 OK, response: {updated_model}'
        updated_model_id = updated_model.pop('id')
        assert updated_model == updated_example, f'Updated {model_name} id: {updated_model_id} does not match updated example data'
        assert updated_model_id == created_model_id, f'Updated {model_name} id: {updated_model_id} does not match created id: {created_model_id}'

    #
    # delete
    #

    if require_login and not hidden:

        # logged out cannot delete #

        delete_status, data = request(logged_out_ctx, 'DELETE', f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}', None)
        assert delete_status == 401, f'Delete {model_name} without login did not return 401 Unauthorized, response: {data}'

        # bob cannot delete alice's model #

        delete_status, data = request(bob_ctx, 'DELETE', f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}', None)
        assert delete_status == 401, f'Delete {model_name} by non-owner did not return 401 Unauthorized, response: {data}'

        # read back to confirm not deleted #

        read_status, read_model = request(ctx, 'GET', f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}', None)
        assert read_status == 200, f'Read {model_name} id: {created_model_id} did not return status 200 OK, response: {read_model}'
        read_model_id = read_model.pop('id')
        assert read_model == updated_example, f'Read {model_name} id: {read_model_id} does not match updated example data after failed delete attempt'

    # send request #

    delete_status, delete_output = request(ctx, 'DELETE', f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}', None)

    if hidden:
        assert delete_status == 404, f'Delete hidden {model_name} id: {created_model_id} did not return 404 Not Found, response: {delete_output}'

    else:
        assert delete_status == 200, f'Delete {model_name} id: {created_model_id} did not return status 200 OK, response: {delete_output}'
        assert 'acknowledged' in delete_output, f'Delete {model_name} id: {created_model_id} did not return acknowledgement field'
        assert delete_output['acknowledged'], f'Delete {model_name} id: {created_model_id} did not return acknowledged=True'
        assert 'message' in delete_output, f'Delete {model_name} id: {created_model_id} did not return message field'
        expected_msg = f'{model["name"]["snake_case"]} {created_model_id} has been deleted'
        assert delete_output['message'].startswith(expected_msg), f'Delete {model_name} id: {created_model_id} did not return correct message'

    if not hidden:

        # confirm delete is idempotent #

        delete_status, delete_output = request(ctx, 'DELETE', f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}', None)
        assert delete_status == 200, f'Delete (2nd) {model_name} id: {created_model_id} did not return status 200 OK, response: {delete_output}'
        assert 'acknowledged' in delete_output, f'Delete {model_name} id: {created_model_id} did not return acknowledgement field'
        assert delete_output['acknowledged'], f'Delete {model_name} id: {created_model_id} did not return acknowledged=True'
        assert 'message' in delete_output, f'Delete {model_name} id: {created_model_id} did not return message field'
        expected_msg = f'{model["name"]["snake_case"]} {created_model_id} has been deleted'
        assert delete_output['message'].startswith(expected_msg), f'Delete {model_name} id: {created_model_id} did not return correct message'

        # read after delete #

        re_read_status, re_read_model = request(ctx, 'GET', f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}', None)
        assert re_read_status == 404, f'Read after delete for {model_name} id: {created_model_id} did not return 404 Not Found, resp: {re_read_model}'
        assert re_read_model.get('error', {}).get('code', '-') == 'NOT_FOUND', f'Read after delete for {model_name} id: {created_model_id} did not return not_found code, resp: {re_read_model}'

    # confirm data isolation between users #

    assert alice_user['id'] != bob_user['id'], 'Alice and Bob users have the same ID, test setup error'
    assert alice_ctx['headers']['Authorization'] != bob_ctx['headers']['Authorization'], 'Alice and Bob have the same Authorization header, test setup error'

def login_cached_user(cmd:list[str], ctx:dict, user_name:str, email:str, password:str='testpass123') -> dict:
    """Login to a cached user and return user data with env context"""
    login_params = {'email': email, 'password': password}
    login_cmd = cmd + ['auth', 'login-user', 'run', json.dumps(login_params), '--show', '--no-session']
    result = subprocess.run(login_cmd, capture_output=True, text=True, env=ctx, timeout=10)
    
    if result.returncode != 0:
        raise RuntimeError(f'Error logging in cached user {user_name}:\n{result.stdout + result.stderr}')
    
    login_response = json.loads(result.stdout)['result']
    access_token = login_response['access_token']
    
    # Decode JWT token to get user_id (without verification since we generated it locally)
    # Signature verification is disabled because:
    # 1. This is for test purposes only with locally generated tokens
    # 2. We just need to extract the user_id from the payload
    # 3. The token was just created by our own auth system
    try:
        token_payload = jwt.decode(access_token, options={'verify_signature': False})
        user_id = token_payload['sub']
    except (jwt.DecodeError, jwt.InvalidTokenError, KeyError) as e:
        raise RuntimeError(f'Error decoding access token for cached user {user_name}: {e}')
    
    user_data = {
        'id': user_id,
        'name': user_name,
        'email': email,
        'password': password,
        'password_confirm': password
    }
    
    user_env = ctx.copy()
    user_env['MAPP_CLI_ACCESS_TOKEN'] = access_token
    user_env['Authorization'] = f'Bearer {access_token}'
    
    return {'user': user_data, 'env': user_env}

def run_cli_validation_error_for_model(module_name_kebab, model, command_type, user_index, cmd, crud_users, crud_ctx):

    def _run_cmd(cmd:list[str], expected_code=0, env:Optional[dict[str, str]] = None) -> subprocess.CompletedProcess:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=10)
        msg = f'expected {expected_code} got {result.returncode} for command "{' '.join(cmd)}" output: {result.stdout + result.stderr}'
        assert result.returncode == expected_code, msg
        return result

    # Skip models that do not allow any data
    if model['auth']['max_models_per_user'] == 0:
        return
    
    if model['hidden'] is True:
        return
    
    example_to_update = example_from_model(model)

    user_id = crud_users[user_index]['user']['id']
    if model['auth']['require_login']:
        ctx = deepcopy(crud_users[user_index]['env'])
        example_to_update['user_id'] = user_id
    else:
        ctx = deepcopy(crud_ctx)

    model_name_kebab = model['name']['kebab_case']

    # seed valid model #

    args = cmd + [module_name_kebab, model_name_kebab, command_type, 'create', json.dumps(example_to_update)]
    seed_result = _run_cmd(args, env=ctx)
    update_model_id = str(json.loads(seed_result.stdout)['id'])

    for invalid_example, invalid_field_name in model_validation_errors(model):
        model_name_kebab = model['name']['kebab_case']

        # attempt to create with invalid data #

        model_command = cmd + [module_name_kebab, model_name_kebab, command_type, 'create', json.dumps(invalid_example)]
        try:
            create_result = _run_cmd(model_command, expected_code=1, env=ctx)
        except AssertionError as e:
            raise AssertionError(str(e) + f'\nfor field "{invalid_field_name}" in model "{model["name"]["pascal_case"]}"')
        create_error = json.loads(create_result.stdout).get('error', {})
        assert create_error['code'] == 'VALIDATION_ERROR', f'Expected VALIDATION_ERROR code for {model["name"]["pascal_case"]} with invalid data {invalid_example}, got {create_error} for field {invalid_field_name}'
        assert 'message' in create_error, f'Expected error message in response for {model["name"]["pascal_case"]} with invalid data {invalid_example}, got {create_error} for field {invalid_field_name}'
        assert 'field_errors' in create_error, f'Expected field_errors in response for {model["name"]["pascal_case"]} with invalid data {invalid_example}, got {create_error} for field {invalid_field_name}'
        assert isinstance(create_error['field_errors'], dict), f'Expected field_errors to be a dict in response for {model["name"]["pascal_case"]} with invalid data {invalid_example}, got {create_error} for field {invalid_field_name}'
        assert len(create_error['field_errors']) == 1, f'Expected one field error in response for {model["name"]["pascal_case"]} with invalid data {invalid_example}, got {create_error} for field {invalid_field_name}'

        # attempt to update (pre-seeded model) with invalid data #

        model_command = cmd + [module_name_kebab, model_name_kebab, command_type, 'update', update_model_id, json.dumps(invalid_example)]
        try:
            update_result = _run_cmd(model_command, expected_code=1, env=ctx)
        except AssertionError as e:
            raise AssertionError(str(e) + f'\nfor field "{invalid_field_name}" in model "{model["name"]["pascal_case"]}"')
        update_error = json.loads(update_result.stdout).get('error', {})
        assert update_error['code'] == 'VALIDATION_ERROR', f'Expected VALIDATION_ERROR code for {model["name"]["pascal_case"]} with invalid data {invalid_example}, got {update_error.get("code", update_error)} for field {invalid_field_name}'
        assert 'message' in update_error, f'Expected error message in response for {model["name"]["pascal_case"]} with invalid data {invalid_example}, got {update_error} for field {invalid_field_name}'
        assert 'field_errors' in update_error, f'Expected field_errors in response for {model["name"]["pascal_case"]} with invalid data {invalid_example}, got {update_error} for field {invalid_field_name}'
        assert isinstance(update_error['field_errors'], dict), f'Expected field_errors to be a dict in response for {model["name"]["pascal_case"]} with invalid data {invalid_example}, got {update_error} for field {invalid_field_name}'
        assert len(update_error['field_errors']) == 1, f'Expected one field error in response for {model["name"]["pascal_case"]} with invalid data {invalid_example}, got {update_error} for field {invalid_field_name}'

    # read back original example to ensure it was not modified
    read_back_result = _run_cmd(cmd + [module_name_kebab, model_name_kebab, command_type, 'read', update_model_id], env=ctx)
    read_model = json.loads(read_back_result.stdout)
    del read_model['id']
    if model['auth']['require_login']:
        example_to_update['user_id'] = user_id

    assert read_model == example_to_update, f'Read {model["name"]["pascal_case"]} does not match original example data after validation error tests'


class TestMTemplateApp(unittest.TestCase):
    
    test_dir = 'mapp-tests'

    """
    Test suite for the mtemplate app generation spec

    Generated App:
        While the applications have their own tests, this suite
        exits to ensure that the generated application matches the
        expected behavior as defined in the spec. This is necessary
        to validate the code generation process.

    Template Apps:
        This test suite is also used to validate the template apps
        themselves. (Currently just mspec/templates/go)

    """

    spec: dict
    cmd: list[str]
    host: str | None
    env_vars: dict
    use_cache: bool
    app_type: str = ''
    threads: int = 12

    pool: Optional[multiprocessing.Pool] = None

    crud_db_file = Path(f'{test_dir}/test_crud_db.sqlite3')
    crud_db_cache_file = Path(f'{test_dir}/test_crud_db_cache.sqlite3')
    crud_envfile = Path(f'{test_dir}/crud.env')
    crud_cache_envfile = Path(f'{test_dir}/crud_cache.env')
    crud_users = []
    crud_ctx = {}

    pagination_db_file = Path(f'{test_dir}/test_pagination_db.sqlite3')
    pagination_db_cache_file = Path(f'{test_dir}/test_pagination_db_cache.sqlite3')
    pagination_envfile = Path(f'{test_dir}/pagination.env')
    pagination_cache_envfile = Path(f'{test_dir}/pagination_cache.env')
    pagination_user = {}
    pagination_ctx = {}

    pagination_total_models = 25

    pagination_cases = [
        # {'size': 1, 'expected_pages': 25},
        {'size': 5, 'expected_pages': 5},
        {'size': 10, 'expected_pages': 3},
        {'size': 25, 'expected_pages': 1},
    ]

    test_password = 'testpass123'

    @classmethod
    def setUpClass(cls):

        print(f':: setting up mapp tests - use cache: {cls.use_cache}')

        crud_fs_path = Path(cls.test_dir) / 'crud_file_system'

        # delete old files #

        if not cls.use_cache:
            # delete everything including all db and cache files
            shutil.rmtree(cls.test_dir, ignore_errors=True)
            print(f':: deleted test directory: {cls.test_dir}')
        else:
            # always recreate the crud file system
            shutil.rmtree(crud_fs_path, ignore_errors=True)
            # delete working db files so they are replaced with fresh cache copies
            for db_file in [cls.crud_db_file, cls.pagination_db_file]:
                try:
                    db_file.unlink()
                except FileNotFoundError:
                    pass
            
            print(f':: deleted database files')

        os.makedirs(cls.test_dir, exist_ok=True)

        # check whether cache dbs already exist
        crud_cache_exists = cls.crud_db_cache_file.exists()
        pagination_cache_exists = cls.pagination_db_cache_file.exists()

        needs_crud_rebuild = not cls.use_cache or not crud_cache_exists
        needs_pagination_rebuild = not cls.use_cache or not pagination_cache_exists
        
        #
        # create test env files
        #

        # base env #

        # crud env file #

        default_host = cls.spec['client']['default_host']
        default_port = int(default_host.split(':')[-1])
        crud_port = default_port + 1
        crud_env = dict(cls.env_vars)
        crud_env['MAPP_SERVER_PORT'] = str(crud_port)
        crud_env['MAPP_CLIENT_HOST'] = f'http://localhost:{crud_port}'
        crud_env['MAPP_DB_URL'] = str(cls.crud_db_file.resolve())
        crud_env['MAPP_FILE_SYSTEM_REPO'] = str(crud_fs_path.resolve())
        crud_env['MAPP_SERVER_DEVELOPMENT_MODE'] = 'true'
        crud_env['MAPP_CLI_SESSION_FILE'] = os.path.join(cls.test_dir, 'crud-env-test-session.json')

        try:
            os.remove(crud_env['MAPP_CLI_SESSION_FILE'])
        except FileNotFoundError:
            pass

        try:
            del crud_env['DEBUG_DELAY']
        except KeyError:
            pass

        with open(cls.crud_envfile, 'w') as f:
            f.write(env_to_string(crud_env))

        cls.crud_ctx = os.environ.copy()
        cls.crud_ctx['MAPP_ENV_FILE'] = str(cls.crud_envfile.resolve())
        cls.crud_ctx.update(crud_env)

        # pagination env file #

        pagination_port = default_port + 2
        pagination_env = dict(cls.env_vars)
        pagination_env['MAPP_SERVER_PORT'] = str(pagination_port)
        pagination_env['MAPP_CLIENT_HOST'] = f'http://localhost:{pagination_port}'
        pagination_env['MAPP_DB_URL'] = str(cls.pagination_db_file.resolve())
        pagination_env['MAPP_FILE_SYSTEM_REPO'] = str((Path(cls.test_dir) / 'pagination_file_system').resolve())
        pagination_env['MAPP_CLI_SESSION_FILE'] = os.path.join(cls.test_dir, 'pagination-env-test-session.json')
        try:
            os.remove(pagination_env['MAPP_CLI_SESSION_FILE'])
        except FileNotFoundError:
            pass

        try:
            del pagination_env['DEBUG_DELAY']
        except KeyError:
            pass

        with open(cls.pagination_envfile, 'w') as f:
            f.write(env_to_string(pagination_env))

        cls.pagination_ctx = os.environ.copy()
        cls.pagination_ctx['MAPP_ENV_FILE'] = str(cls.pagination_envfile.resolve())
        cls.pagination_ctx.update(pagination_env)

        # open process pool #

        cls.pool = multiprocessing.Pool(processes=cls.threads)

        """
        Testing Table Creation

        There are two cli commands to create tables in MAPP:
            - mapp create-tables
            - mapp <module> <model> db create-table

        The first command creates all tables for all models in all modules.
        The second command creates all tables for a specific model.

        In these tests we create 2 environments, one for testing CRUD ops
        and one for testing pagination. We use the first command to create
        tables for the CRUD environment, and the second command to create
        tables for the pagination environment. This allows us to test both
        methods of table creation.

        --use-cache can be used to reuse seeded cache dbs across test runs.
        When the cache exists both dbs are copied from cache instead of being
        recreated from scratch. User login sessions are always created fresh
        from the copied working dbs, since tokens expire between runs.
        """

        # create crud tables in cache db #

        if needs_crud_rebuild or needs_pagination_rebuild:
            sys.stdout.write(':: rebuilding caches')
            sys.stdout.flush()

        if needs_crud_rebuild:
            sys.stdout.write('\n  :: crud: tables')
            sys.stdout.flush()
            crud_create_tables_cmd = cls.cmd + ['create-tables']
            crud_result = subprocess.run(crud_create_tables_cmd, capture_output=True, text=True, env=cls.crud_ctx)
            if crud_result.returncode != 0:
                raise RuntimeError(f'Error creating tables for crud db: {crud_result.stdout + crud_result.stderr}')
            
            try:
                crud_output = json.loads(crud_result.stdout)
                assert crud_output['acknowledged'] is True
                assert crud_output['message'] == 'All tables created or already existed.'
            except AssertionError as e:
                raise RuntimeError(f'AssertionError {e} while creating tables for crud cache db: {crud_result.stdout + crud_result.stderr}')
        
        else:
            print(f':: copying cached crud db to working db ::')
            shutil.copy2(str(cls.crud_db_cache_file), str(cls.crud_db_file))

        # create crud users

        if needs_crud_rebuild and cls.spec['project']['use_builtin_modules']:
            crud_users = ['alice', 'bob', 'charlie', 'david', 'evelyn']
            sys.stdout.write(', users')
            sys.stdout.flush()
            for user_name in crud_users:

                # logout #

                logout_cmd = cls.cmd + ['auth', 'logout-user', 'run']
                result = subprocess.run(logout_cmd, capture_output=True, text=True, env=cls.crud_ctx)
                # do not check result because logout may fail if no user is logged in

                # create #

                user_data = {
                    'name': user_name,
                    'email': f'{user_name}@example.com',
                    'password': cls.test_password,
                    'password_confirm': cls.test_password
                }

                create_cmd = cls.cmd + ['auth', 'create-user', 'run', json.dumps(user_data)]
                result = subprocess.run(create_cmd, capture_output=True, text=True, env=cls.crud_ctx)
                if result.returncode != 0:
                    raise RuntimeError(f'Error creating crud user {user_name}:\n{result.stdout + result.stderr}')
            
            shutil.copy2(str(cls.crud_db_file), str(cls.crud_db_cache_file))
            sys.stdout.write(f', cached db file')

        # create pagination tables and seed data in cache db #

        if needs_pagination_rebuild:

            sys.stdout.write('\n  :: pagination: tables')
            sys.stdout.flush()

            # setup tables in cache db #

            for module in cls.spec['modules'].values():
                module_name_kebab = module['name']['kebab_case']

                for model in module['models'].values():

                    if model['hidden'] is True:
                        continue

                    model_name_snake = model['name']['snake_case']
                    model_name_kebab = model['name']['kebab_case']

                    create_table_args = cls.cmd + [module_name_kebab, model_name_kebab, 'db', 'create-table']

                    result = subprocess.run(create_table_args, capture_output=True, text=True, env=cls.pagination_ctx)
                    if result.returncode != 0:
                        raise RuntimeError(f'Error creating table for pagination db {module_name_kebab}.{model_name_kebab}: {result.stdout + result.stderr}')

                    try:
                        pagination_output = json.loads(result.stdout)
                        assert pagination_output['acknowledged'] is True
                        assert model_name_snake in pagination_output['message']
                    except AssertionError as e:
                        raise RuntimeError(f'AssertionError {e} while creating table for pagination db {module_name_kebab}.{model_name_kebab}: {result.stdout + result.stderr}')

            # still need to use create-tables command because hidden models cannot be created individually #

            pagination_create_tables_cmd = cls.cmd + ['create-tables']
            pagination_result = subprocess.run(pagination_create_tables_cmd, capture_output=True, text=True, env=cls.pagination_ctx)
            if pagination_result.returncode != 0:
                raise RuntimeError(f'Error creating tables for pagination db: {pagination_result.stdout + pagination_result.stderr}')

            # seed pagination cache db #

            sys.stdout.write(', seeding')
            sys.stdout.flush()

            seed_jobs = []
            for module in cls.spec['modules'].values():
                module_name_kebab = module['name']['kebab_case']

                for model in module['models'].values():
                    if model['hidden'] is True:
                        continue

                    if model['auth']['max_models_per_user'] == 0:
                        continue

                    model_name_kebab = model['name']['kebab_case']

                    path = f'{module_name_kebab}.{model_name_kebab}'

                    require_auth = model['auth']['require_login']

                    for index in range(cls.pagination_total_models):
                        example_model = example_from_model(model, index=0)
                        seed_cmd = cls.cmd + [module_name_kebab, model_name_kebab, 'db', 'create']
                        unique_id = f'{path}.{index}'
                        seed_jobs.append((unique_id, cls.cmd, seed_cmd, cls.pagination_ctx, require_auth, example_model))

            results = cls.pool.starmap(seed_pagination_item, seed_jobs)

            for (cmd_args, code, stdout, stderr) in results:
                if code != 0:
                    raise RuntimeError(f':: ERROR seeding table for pagination db :: COMMAND :: {" ".join(cmd_args)} :: OUTPUT :: {stdout + stderr}')

            # create pagination user #

            if cls.spec['project']['use_builtin_modules']:
                sys.stdout.write(', user')
                sys.stdout.flush()

                user_data = {
                    'name': 'pagination_tester',
                    'email': 'pagination_tester@example.com',
                    'password': cls.test_password,
                    'password_confirm': cls.test_password
                }

                create_cmd = cls.cmd + ['auth', 'create-user', 'run', json.dumps(user_data)]
                create_result = subprocess.run(create_cmd, capture_output=True, text=True, env=cls.pagination_ctx)
                if create_result.returncode != 0:
                    raise RuntimeError(f'Error creating pagination test user: {create_result.stdout + create_result.stderr}')
            
            shutil.copy2(str(cls.pagination_db_file), str(cls.pagination_db_cache_file))
            sys.stdout.write(f', cached db file\n')
        
        else:
            print(f':: copying cached pagination db to working db ::')
            shutil.copy2(str(cls.pagination_db_cache_file), str(cls.pagination_db_file))

        # create login sessions in working dbs #

        cls.crud_users = []
        if cls.spec['project']['use_builtin_modules']:
            print(':: logging in users ::')

            crud_users = ['alice', 'bob', 'charlie', 'david', 'evelyn']
            for user_name in crud_users:
                user = login_cached_user(cls.cmd, cls.crud_ctx, user_name, f'{user_name}@example.com')
                cls.crud_users.append(user)

            cls.pagination_user = login_cached_user(
                cls.cmd,
                cls.pagination_ctx,
                'pagination_tester',
                'pagination_tester@example.com'
            )

        # delete server logs #

        for log_file in glob.glob(f'{cls.test_dir}/test_server_*.log'):
            try:
                Path(log_file).unlink()
            except FileNotFoundError:
                pass

        # create server configs #

        crud_server_start_cmd = cls.cmd + ['server']
        pagination_server_start_cmd = cls.cmd + ['server']
        cls.server_status_commands = []

        if cls.app_type == 'python':
            with open('uwsgi.yaml', 'r') as f:
                uwsgi_config = f.read()

            port_pattern = r'http:\s*:\d+'
            pid_file_pattern = r'safe-pidfile:\s*.+'
            stats_pattern = r'stats:\s*.+'
            logto_pattern = r'logto:\s*.+'

            cls.crud_pidfile = f'{cls.test_dir}/uwsgi_crud.pid'
            cls.pagination_pidfile = f'{cls.test_dir}/uwsgi_pagination.pid'
            cls.crud_stats_socket = f'{cls.test_dir}/stats_crud.socket'
            cls.crud_log_file = f'{cls.test_dir}/server_crud.log'

            cls.crud_uwsgi_config = f'{cls.test_dir}/uwsgi_crud.yaml'
            cls.pagination_uwsgi_config = f'{cls.test_dir}/uwsgi_pagination.yaml'
            cls.pagination_stats_socket = f'{cls.test_dir}/stats_pagination.socket'
            cls.pagination_log_file = f'{cls.test_dir}/server_pagination.log'

            crud_server_start_cmd = ['./server.sh', 'start', '--pid-file', cls.crud_pidfile, '--config', cls.crud_uwsgi_config, '--log-file', cls.crud_log_file]
            pagination_server_start_cmd = ['./server.sh', 'start', '--pid-file', cls.pagination_pidfile, '--config', cls.pagination_uwsgi_config, '--log-file', cls.pagination_log_file]

            cls.crud_server_stop_cmd = ['./server.sh', 'stop', '--pid-file', cls.crud_pidfile, '--config', cls.crud_uwsgi_config]
            cls.pagination_server_stop_cmd = ['./server.sh', 'stop', '--pid-file', cls.pagination_pidfile, '--config', cls.pagination_uwsgi_config]

            cls.server_status_commands.append(['./server.sh', 'status', '--pid-file', cls.crud_pidfile, '--config', cls.crud_uwsgi_config])
            cls.server_status_commands.append(['./server.sh', 'status', '--pid-file', cls.pagination_pidfile, '--config', cls.pagination_uwsgi_config])

            with open(cls.crud_uwsgi_config, 'w') as f:
                crud_uwsgi_config = re.sub(port_pattern, f'http: :{crud_port}', uwsgi_config)
                crud_uwsgi_config = re.sub(pid_file_pattern, f'safe-pidfile: {cls.crud_pidfile}', crud_uwsgi_config)
                crud_uwsgi_config = re.sub(stats_pattern, f'stats: {cls.crud_stats_socket}', crud_uwsgi_config)
                f.write(crud_uwsgi_config)
            
            with open(cls.pagination_uwsgi_config, 'w') as f:
                pagination_uwsgi_config = re.sub(port_pattern, f'http: :{pagination_port}', uwsgi_config)
                pagination_uwsgi_config = re.sub(pid_file_pattern, f'safe-pidfile: {cls.pagination_pidfile}', pagination_uwsgi_config)
                pagination_uwsgi_config = re.sub(stats_pattern, f'stats: {cls.pagination_stats_socket}', pagination_uwsgi_config)
                pagination_uwsgi_config = re.sub(logto_pattern, f'logto: {cls.pagination_log_file}', pagination_uwsgi_config)
                f.write(pagination_uwsgi_config)

        # confirm servers are stopped from previous tests #

        crud_result = subprocess.run(cls.crud_server_stop_cmd, env=cls.crud_ctx, capture_output=True, text=True, timeout=10)
        pagination_result = subprocess.run(cls.pagination_server_stop_cmd, env=cls.pagination_ctx, capture_output=True, text=True, timeout=10)
        
        # start servers #

        print(':: starting server processes ::')

        print('    :: ', ' '.join(crud_server_start_cmd))
        crud_result = subprocess.run(crud_server_start_cmd, env=cls.crud_ctx, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        if crud_result.returncode != 0:
            raise RuntimeError(f'Error starting CRUD server: {crud_result.stdout + crud_result.stderr}')

        print('    :: ', ' '.join(pagination_server_start_cmd))
        pagination_result = subprocess.run(pagination_server_start_cmd, env=cls.pagination_ctx, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        if pagination_result.returncode != 0:
            raise RuntimeError(f'Error starting pagination server: {pagination_result.stdout + pagination_result.stderr}')

        print(':: setup complete')

        print(':: test progress :: ', end='', flush=True)
    
    @classmethod
    def tearDownClass(cls):

        print('\n:: tearing down tests')

        # stop pool #

        if cls.pool:
            cls.pool.close()
            cls.pool.join()
        
        if cls.app_type == 'python':
            try:
                subprocess.run(cls.crud_server_stop_cmd, env=cls.crud_ctx, check=True, capture_output=True, timeout=15)
                subprocess.run(cls.pagination_server_stop_cmd, env=cls.pagination_ctx, check=True, capture_output=True, timeout=15)
            except subprocess.TimeoutExpired:
                print('    :: Timeout expired while stopping servers ::')
            except subprocess.CalledProcessError as e:
                print(f'    :: Error stopping servers: {e} :: {e.output} :: {e.stderr} ::')
        
        print(':: teardown complete ::')

    def _run_cmd(self, cmd:list[str], expected_code=0, env:Optional[dict[str, str]] = None) -> subprocess.CompletedProcess:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=10)
        msg = f'expected {expected_code} got {result.returncode} for command "{' '.join(cmd)}" output: {result.stdout + result.stderr}'
        self.assertEqual(result.returncode, expected_code, msg)
        return result
    
    def _check_servers_running(self):
        error = 0
        for cmd in self.server_status_commands:
            # call via subprocess and check stdout for text RUNNING
            result = subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy(), timeout=10)
            if result.returncode != 0 or 'RUNNING' not in result.stdout:
                print(f':: ERROR: Server process not running for command {" ".join(cmd)} :: Output: {result.stdout + result.stderr}')
                error += 1

        self.assertEqual(error, 0, f'{error} server processes not running')

    # builtin - auth tests #

    def _test_user_auth_flow(self, ctx:dict, io_type:str):
        """
        test auth command flow via cli <io type> command

        ./mapp auth delete-user <io type>
            * expect error
        ./mapp auth current-user <io type>
            * expect error
        ./mapp auth is-logged-in <io type>
            * expect false

        ./mapp auth create-user <io type> {"name": "brad", ...}
        ./mapp auth login-user <io type> {"email": "...", ...}
        ./mapp auth current-user <io type>
        ./mapp auth is-logged-in <io type>
        ./mapp auth logout-user <io type> {"mode": "current"}
        ./mapp auth current-user <io type>
            * expect error
        ./mapp auth login-user <io type> {"email": "...", ...}
        ./mapp auth delete-user <io type>
        ./mapp auth current-user <io type>
            * expect error
        ./mapp auth is-logged-in <io type>
            * expect false
        """
        # Setup
        cmd = self.cmd
        env = ctx.copy()
        try:
            del env['MAPP_CLI_ACCESS_TOKEN']
        except KeyError:
            pass

        env['MAPP_CLI_SESSION_FILE'] = os.path.join(self.test_dir, f'user-auth-flow-{io_type}-test-session.json')

        try:
            os.remove(env['MAPP_CLI_SESSION_FILE'])
        except FileNotFoundError:
            pass

        user_name = 'alice'
        user_email = f'alice@{io_type}.com'
        user_password = self.test_password
        
        # Helper to run a command and return output
        def run_auth_cmd(args, input_data=None, expected_code=-1):
            if input_data is not None:
                result = subprocess.run(args, input=input_data, capture_output=True, text=True, env=env)
            else:
                result = subprocess.run(args, capture_output=True, text=True, env=env)
            msg = f'expected {expected_code} got {result.returncode} for command "{' '.join(args)}" output: {result.stdout + result.stderr}'
            if expected_code >= 0:
                self.assertEqual(result.returncode, expected_code, msg)
            return result
        
        # confirm we are logged out
        logout_input = json.dumps({"mode": "current"})
        result = run_auth_cmd(cmd + ["auth", "logout-user", io_type, logout_input], expected_code=-1)

        # 1. delete-user (should error)
        result = run_auth_cmd(cmd + ["auth", "delete-user", io_type], expected_code=1)
        self.assertIn("error", result.stdout.lower())

        # 2. current-user (should error)
        result = run_auth_cmd(cmd + ["auth", "current-user", io_type], expected_code=1)
        self.assertIn("error", result.stdout.lower())

        # 3. is-logged-in (should be false)
        result = run_auth_cmd(cmd + ["auth", "is-logged-in", io_type])
        self.assertIn('"logged_in": false', result.stdout)

        # 4. create-user
        create_input = json.dumps({"name": user_name, "email": user_email, "password": user_password, "password_confirm": user_password})
        try:
            result = run_auth_cmd(cmd + ["auth", "create-user", io_type, create_input])
        except AssertionError as e:
            print(f'AssertionError running create-user command: {e}')
            breakpoint()


        self.assertIn(user_email, result.stdout)

        # 5. login-user
        login_input = json.dumps({"email": user_email, "password": user_password})
        result = run_auth_cmd(cmd + ["auth", "login-user", io_type, login_input])
        self.assertIn("access_token", result.stdout)

        # 6. current-user (should succeed)
        result = run_auth_cmd(cmd + ["auth", "current-user", io_type])
        self.assertIn(user_email, result.stdout)

        # 7. is-logged-in (should be true)
        result = run_auth_cmd(cmd + ["auth", "is-logged-in", io_type])
        self.assertIn('"logged_in": true', result.stdout)

        # 8. logout-user (current)
        logout_input = json.dumps({"mode": "current"})
        result = run_auth_cmd(cmd + ["auth", "logout-user", io_type, logout_input])
        self.assertIn("logged out", result.stdout.lower())

        # 9. current-user (should error)
        result = run_auth_cmd(cmd + ["auth", "current-user", io_type], expected_code=1)
        self.assertIn("error", result.stdout.lower())

        # 10. login-user (again)
        result = run_auth_cmd(cmd + ["auth", "login-user", io_type, login_input])
        self.assertIn("access_token", result.stdout)

        # 11. delete-user
        result = run_auth_cmd(cmd + ["auth", "delete-user", io_type])
        self.assertIn("deleted", result.stdout.lower())

        # 12. current-user (should error)
        result = run_auth_cmd(cmd + ["auth", "current-user", io_type], expected_code=1)
        self.assertIn("error", result.stdout.lower())

        # 13. is-logged-in (should be false)
        result = run_auth_cmd(cmd + ["auth", "is-logged-in", io_type])
        self.assertIn('"logged_in": false', result.stdout)


    def test_cli_run_auth_flow(self):
        self._test_user_auth_flow(self.crud_ctx, 'run')
    
    def test_cli_http_auth_flow(self):
        self._test_user_auth_flow(self.crud_ctx, 'http')

    def test_server_auth_flow(self):
        """
        test auth command flow via cli http command
        
        /api/auth/delete-user
            * expect error

        /api/auth/current-user
            * expect error

        /api/auth/is-logged-in
            * expect false

        /api/auth/create-user {"name": "brad", ...}
        /api/auth/login-user {"email": "...", ...}
        /api/auth/current-user
        /api/auth/is-logged-in
        /api/auth/logout-user {"mode": "current"}
        /api/auth/current-user
            * expect error
        /api/auth/is-logged-in
            * expect false
        /api/auth/login-user {"email": "...", ...}
        /api/auth/delete-user
        /api/auth/current-user
            * expect error
        /api/auth/is-logged-in
            * expect false
        """

        self._check_servers_running()

        base_ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }
        base_ctx.update(self.crud_ctx)

        # 1. delete-user (should error)

        logged_out_delete_status, logged_out_delete_resp = request(base_ctx, 'GET', '/api/auth/delete-user')
        self.assertEqual(logged_out_delete_status, 401)
        self.assertIn('error', logged_out_delete_resp)

        # 2. current-user (should error)
        logged_out_current_status, logged_out_current_resp = request(base_ctx, 'GET', '/api/auth/current-user')
        self.assertEqual(logged_out_current_status, 401)
        self.assertIn('error', logged_out_current_resp)

        # 3. is-logged-in (should be false)
        logged_out_is_logged_in_status, logged_out_is_logged_in_resp = request(base_ctx, 'GET', '/api/auth/is-logged-in')
        self.assertEqual(logged_out_is_logged_in_status, 200)
        self.assertIn('logged_in', logged_out_is_logged_in_resp['result'])
        self.assertFalse(logged_out_is_logged_in_resp['result']['logged_in'])


        # 4. create-user
        create_status, create_resp = request(
            base_ctx, 
            'POST', 
            '/api/auth/create-user', 
            request_body=json.dumps({
                'name': 'alice',
                'email': 'alice-server@example.com',
                'password': self.test_password,
                'password_confirm': self.test_password
            }).encode()
        )
        self.assertEqual(create_status, 200)
        self.assertIn('result', create_resp)
        self.assertIn('id', create_resp['result'])

        # 5. login-user
        login_status, login_resp = request(
            base_ctx, 
            'POST', 
            '/api/auth/login-user', 
            request_body=json.dumps({
                'email': 'alice-server@example.com',
                'password': self.test_password
            }).encode()
        )
        self.assertEqual(login_status, 200)
        self.assertIn('result', login_resp)
        self.assertIn('access_token', login_resp['result'])

        logged_in_ctx = base_ctx.copy()
        access_token = login_resp['result']['access_token']
        logged_in_ctx['headers']['Authorization'] = f'Bearer {access_token}'

        # 5. current-user (should succeed)
        current_status, current_resp = request(
            logged_in_ctx, 
            'GET', 
            '/api/auth/current-user'
        )
        self.assertEqual(current_status, 200)
        self.assertIn('email', current_resp['result'])
        self.assertEqual(current_resp['result']['email'], 'alice-server@example.com')

        # 6. is-logged-in (should be true)
        is_logged_in_status, is_logged_in_resp = request(logged_in_ctx, 'GET', '/api/auth/is-logged-in')
        self.assertEqual(is_logged_in_status, 200)
        self.assertIn('logged_in', is_logged_in_resp['result'])
        self.assertTrue(is_logged_in_resp['result']['logged_in'])

        # 7. logout-user (current)
        logout_status, logout_resp = request(
            logged_in_ctx, 
            'POST', 
            '/api/auth/logout-user', 
            request_body=json.dumps({'mode': 'current'}).encode()
        )
        self.assertEqual(logout_status, 200)
        self.assertIn('logged out', logout_resp['result']['message'].lower())

        del logged_in_ctx['headers']['Authorization']

        # 8. current-user (should error)
        logged_out_current_status, logged_out_current_resp = request(base_ctx, 'GET', '/api/auth/current-user')
        self.assertEqual(logged_out_current_status, 401)
        self.assertIn('error', logged_out_current_resp)

        # 9. is logged in (should be false)
        logged_out_is_logged_in_status, logged_out_is_logged_in_resp = request(base_ctx, 'GET', '/api/auth/is-logged-in')
        self.assertEqual(logged_out_is_logged_in_status, 200)
        self.assertIn('logged_in', logged_out_is_logged_in_resp['result'])
        self.assertFalse(logged_out_is_logged_in_resp['result']['logged_in'])

        # 10. login-user (again)
        login_status, login_resp = request(
            base_ctx, 
            'POST', 
            '/api/auth/login-user', 
            request_body=json.dumps({
                'email': 'alice-server@example.com',
                'password': self.test_password
            }).encode()
        )
        self.assertEqual(login_status, 200, f'Login failed: {login_resp}')
        self.assertIn('access_token', login_resp['result'])

        logged_in_ctx = base_ctx.copy()
        access_token = login_resp['result']['access_token']
        logged_in_ctx['headers']['Authorization'] = f'Bearer {access_token}'

        # 11. delete-user
        delete_status, delete_resp = request(
            logged_in_ctx, 
            'GET', 
            '/api/auth/delete-user'
        )
        self.assertEqual(delete_status, 200)
        self.assertIn('deleted', delete_resp['result']['message'].lower())

        # 12. current-user (should error)
        logged_out_current_status, logged_out_current_resp = request(base_ctx, 'GET', '/api/auth/current-user')
        self.assertEqual(logged_out_current_status, 401)
        self.assertIn('error', logged_out_current_resp)

        # 13. is-logged-in (should be false)
        logged_out_is_logged_in_status, logged_out_is_logged_in_resp = request(base_ctx, 'GET', '/api/auth/is-logged-in')
        self.assertEqual(logged_out_is_logged_in_status, 200)
        self.assertIn('logged_in', logged_out_is_logged_in_resp['result'])
        self.assertFalse(logged_out_is_logged_in_resp['result']['logged_in'])


    # builtin - file system tests #

    def _test_email_verification_flow(self, ctx:dict, io_type:str):
        """
        Test the email verification flow using mock SMTP.

        1. create-user and login-user
        2. com send-email (mock mode) - verify acknowledged response
        3. com start-email-verification (mock mode) - captures code from log output
        4. com verify-email-address with the code - verify acknowledged response
        5. auth current-user - verify email_verified is true
        """

        env = deepcopy(ctx)
        env['MAPP_SMTP_MOCK'] = 'true'
        env['MAPP_CLI_IGNORE_SESSION_FILE'] = 'true'

        try:
            del env['MAPP_CLI_ACCESS_TOKEN']
        except KeyError:
            pass

        user_email = f'email-verify-{io_type}@example.com'
        user_name = f'email-verify-{io_type}'
        user_password = self.test_password

        def run_cmd(args, expected_code=0):
            result = subprocess.run(args, capture_output=True, text=True, env=env, timeout=10)
            msg = f'expected {expected_code} got {result.returncode} for command:\n"{" ".join(args)}"\noutput:\n{result.stdout + result.stderr}'
            if expected_code >= 0:
                self.assertEqual(result.returncode, expected_code, msg)
            return result

        # 1. create-user #
        create_input = json.dumps({'name': user_name, 'email': user_email, 'password': user_password, 'password_confirm': user_password})
        run_cmd(self.cmd + ['--log', 'auth', 'create-user', io_type, create_input])

        # 2. login-user #
        login_input = json.dumps({'email': user_email, 'password': user_password})
        login_result = run_cmd(self.cmd + ['auth', 'login-user', io_type, login_input, '--show', '--no-session'])
        self.assertIn('access_token', login_result.stdout)

        # extract access token from login result and set in env for subsequent commands
        login_data = json.loads(login_result.stdout)['result']
        access_token = login_data['access_token']
        env['MAPP_CLI_ACCESS_TOKEN'] = access_token

        # 3. com send-email (mock) #
        send_input = json.dumps({'email': user_email, 'subject': 'Test', 'body': 'Hello'})
        send_result = run_cmd(self.cmd + ['com', 'send-email', io_type, send_input])
        send_data = json.loads(send_result.stdout)['result']
        self.assertTrue(send_data['acknowledged'], f'send-email not acknowledged: {send_data}')

        # 4. start-email-verification (mock, with --log to capture code) #
        start_result = run_cmd(self.cmd + ['--log', 'com', 'start-email-verification', io_type])
        self.assertIn('"acknowledged": true', start_result.stdout, f'start-email-verification not acknowledged: {start_result.stdout}')
        
        # 5. verify-email-address with wrong code should fail #
        wrong_code_input = json.dumps({'code': '000000'})
        run_cmd(self.cmd + ['com', 'verify-email-address', io_type, wrong_code_input], expected_code=1)

        if io_type != 'http':
            # only verify for non-http because we can't see the logs for the server to get the code
            # parse the verification code from log output #
            code_match = re.search(r'Your verification code is: (\d{6})', start_result.stdout)
            self.assertIsNotNone(code_match, f'Could not find verification code in log output: {start_result.stdout}')
            code = code_match.group(1)

            # 6. verify-email-address with code #
            verify_input = json.dumps({'code': code})
            verify_result = run_cmd(self.cmd + ['com', 'verify-email-address', io_type, verify_input])
            verify_data = json.loads(verify_result.stdout)['result']
            self.assertTrue(verify_data['acknowledged'], f'verify-email-address not acknowledged: {verify_data}')

            # 7. current-user - confirm email_verified is true #
            current_result = run_cmd(self.cmd + ['auth', 'current-user', io_type])
            current_data = json.loads(current_result.stdout)['result']
            self.assertTrue(current_data.get('email_verified'), f'email_verified should be true after verification: {current_data}')

    def test_cli_run_email_verification_flow(self):
        self._test_email_verification_flow(self.crud_ctx, 'run')

    def test_cli_http_email_verification_flow(self):
        self._test_email_verification_flow(self.crud_ctx, 'http')

    def test_server_email_verification_flow(self):
        """
        Test the email verification flow via the HTTP server.
        Requires MAPP_SMTP_MOCK to be set in the server environment.
        """
        self._check_servers_running()

        base_ctx = {
            'headers': {'Content-Type': 'application/json'}
        }
        base_ctx.update(self.crud_ctx)

        user_email = 'email-verify-server@example.com'
        user_name = 'email-verify-server'
        user_password = self.test_password

        # create-user #

        create_status, create_resp = request(
            base_ctx, 'POST', '/api/auth/create-user',
            json.dumps({'name': user_name, 'email': user_email, 'password': user_password, 'password_confirm': user_password}).encode()
        )
        self.assertEqual(create_status, 200, f'create-user failed: {create_resp}')

        # login-user #

        login_status, login_resp = request(
            base_ctx, 'POST', '/api/auth/login-user',
            json.dumps({'email': user_email, 'password': user_password}).encode()
        )
        self.assertEqual(login_status, 200, f'login-user failed: {login_resp}')
        access_token = login_resp['result']['access_token']

        logged_in_ctx = base_ctx.copy()
        logged_in_ctx['headers'] = base_ctx['headers'].copy()
        logged_in_ctx['headers']['Authorization'] = f'Bearer {access_token}'

        # send-email (mock) #

        send_status, send_resp = request(
            logged_in_ctx, 'POST', '/api/com/send-email',
            json.dumps({'email': user_email, 'subject': 'Test', 'body': 'Hello'}).encode()
        )
        self.assertEqual(send_status, 200, f'send-email failed: {send_resp}')
        self.assertTrue(send_resp['result']['acknowledged'], f'send-email not acknowledged: {send_resp}')

        # start-email-verification (mock - code will be in server logs, not returned) #

        start_status, start_resp = request(logged_in_ctx, 'POST', '/api/com/start-email-verification', b'{}')
        self.assertEqual(start_status, 200, f'start-email-verification failed: {start_resp}')
        self.assertTrue(start_resp['result']['acknowledged'], f'start-email-verification not acknowledged: {start_resp}')

        # verify-email-address with wrong code (server returns error) #

        wrong_verify_status, wrong_verify_resp = request(
            logged_in_ctx, 'POST', '/api/com/verify-email-address',
            json.dumps({'code': '000000'}).encode()
        )
        self.assertEqual(wrong_verify_status, 401, f'verify-email-address with wrong code did not return 401: {wrong_verify_resp}')

    # builtin - file system tests #

    def _test_file_system_ingest_flow(self, ctx:dict, io_type:str):
        """
        ./run.sh --log -fi ./tests/samples/splash.png file-system ingest-start run '{"name": "splash.png", "size": 4007485, "parts": 1, "finish": true}'

        ./run.sh file-system list-files run

        ./run.sh file-system list-parts run '{"file_id": ""}'

        ./run.sh -fo splash_copy.png file-system get-part-content run '{"file_id": "5", "part_number": 1}'
        """

        #
        # init
        #

        logged_out_ctx = self.crud_ctx.copy()
        user = self.crud_users[0]['user']
        user_env = self.crud_users[0]['env']

        sample_path = 'tests/samples/splash-orig.png'
        sample_size = 4007485
        sample_checksum = 'bf3bc28ca617270e3537761e2b9c935f2ea54b6d4debe926a06e765c2bab414e'

        self.assertTrue(os.path.exists(sample_path), 'Sample file for ingest test does not exist')
        self.assertEqual(os.path.getsize(sample_path), sample_size, 'Sample file size does not match expected size')

        # test create #

        json_params = json.dumps({
            'name': 'splash-orig.png',
            'size': sample_size,
            'parts': 1,
            'finish': True
        })

        cmd = self.cmd + ['-fi', sample_path, 'file-system', 'ingest-start', io_type, json_params]

        # ensure logged out user cannot ingest #

        self._run_cmd(cmd, env=logged_out_ctx, expected_code=1)

        # ingest with logged in user #

        create_cmd_result = self._run_cmd(cmd, env=user_env)
        create_result = json.loads(create_cmd_result.stdout)['result']
        self.assertIn('file_id', create_result, 'Ingest start result does not contain file_id')
        self.assertIn('status: good', create_result['message'], 'Ingest start result message does not indicate success')

        # confirm can list file #

        list_files_cmd = self.cmd + ['file-system', 'list-files', io_type, json.dumps({'file_id': create_result['file_id']})]
        list_files_result = self._run_cmd(list_files_cmd, env=user_env)
        list_files = json.loads(list_files_result.stdout)['result']

        self.assertEqual(len(list_files['items']), 1, 'Should be exactly 1 file in list files result')
        self.assertEqual(list_files['total'], 1, 'Total in list files result should be 1')

        file_record = list_files['items'][0]
        self.assertEqual(file_record['id'], create_result['file_id'], 'File ID in list files result does not match created file_id')
        self.assertEqual(file_record['name'], 'splash-orig.png', 'File name in list files result does not match expected name')
        self.assertEqual(file_record['size'], sample_size, 'File size in list files result does not match expected size')
        self.assertEqual(file_record['parts'], 1, 'File parts in list files result does not match expected parts')
        self.assertEqual(file_record['status'], 'good', 'File status in list files result does not indicate good status')
        self.assertEqual(file_record['user_id'], user['id'], 'File user_id in list files result does not match expected user_id')
        self.assertEqual(file_record['sha3_256'], sample_checksum, 'File sha3_256 in list files result does not match expected hash')

        # confirm can list parts #

        list_parts_cmd = self.cmd + ['file-system', 'list-parts', io_type, json.dumps({'file_id': create_result['file_id']})]
        list_parts_result = self._run_cmd(list_parts_cmd, env=user_env)
        list_parts = json.loads(list_parts_result.stdout)['result']
        self.assertEqual(len(list_parts['items']), 1, 'Should be exactly 1 part in list parts result')
        self.assertEqual(list_parts['total'], 1, 'Total in list parts result should be 1')

        part_record = list_parts['items'][0]
        self.assertEqual(part_record['file_id'], create_result['file_id'], 'Part file_id in list parts result does not match created file_id')
        self.assertEqual(part_record['part_number'], 1, 'Part number in list parts result does not match expected part number')
        self.assertEqual(part_record['size'], sample_size, 'Part size in list parts result does not match expected size')
        self.assertEqual(part_record['sha3_256'], sample_checksum, 'Part sha3_256 in list parts result does not match expected hash')
        self.assertEqual(part_record['user_id'], user['id'], 'Part user_id in list parts result does not match expected user_id')

        # confirm can get part content #
        local_part_dest = os.path.join(self.test_dir, f'splash-fs-part-content-{io_type}.png')
        get_part_cmd = self.cmd + ['-fo', local_part_dest, 'file-system', 'get-part-content', io_type, json.dumps({'file_id': create_result['file_id'], 'part_number': 1})]
        get_part_output = self._run_cmd(get_part_cmd, env=user_env)
        get_part_result = json.loads(get_part_output.stdout)['result']
        self.assertTrue(get_part_result['acknowledged'], 'Get part content result not acknowledged')
        self.assertTrue(os.path.exists(local_part_dest), f'Local file for part content does not exist after get-part-content command: {local_part_dest}')
        self.assertEqual(os.path.getsize(local_part_dest), sample_size, f'Local file size for part content does not match expected size: {local_part_dest}')
        with open(local_part_dest, 'rb') as f:
            local_checksum = hashlib.sha3_256(f.read()).hexdigest()
        self.assertEqual(local_checksum, sample_checksum, f'Local file checksum for part content does not match expected checksum: {local_part_dest}')

        # confirm can get file content #

        local_file_dest = os.path.join(self.test_dir, f'splash-fs-file-content-{io_type}.png')
        get_file_cmd = self.cmd + ['-fo', local_file_dest, 'file-system', 'get-file-content', io_type, json.dumps({'file_id': create_result['file_id']})]
        get_file_output = self._run_cmd(get_file_cmd, env=user_env)
        get_file_result = json.loads(get_file_output.stdout)['result']
        self.assertTrue(get_file_result['acknowledged'], 'Get file content result not acknowledged')
        self.assertTrue(os.path.exists(local_file_dest), f'Local file for file content does not exist after get-file-content command: {local_file_dest}')
        self.assertEqual(os.path.getsize(local_file_dest), sample_size, f'Local file size for file content does not match expected size: {local_file_dest}')
        with open(local_file_dest, 'rb') as f:
            local_checksum = hashlib.sha3_256(f.read()).hexdigest()
        self.assertEqual(local_checksum, sample_checksum, f'Local file checksum for file content does not match expected checksum: {local_file_dest}')

    def test_cli_run_file_system_ingest_flow(self):
        self._test_file_system_ingest_flow(self.crud_ctx, 'run')
        
    # def test_cli_http_file_system_ingest_flow(self):
    #     self._test_file_system_ingest_flow(self.crud_ctx, 'http')

    # builtin - media tests #

    def _test_media_create_image_flow(self, ctx:dict, io_type:str):
        """
        ./run.sh --log -fi ./tests/samples/splash-orig.png media create-image run '{"name": "splash.png"}'
        ./run.sh --log -fi ./tests/samples/splash-low.jpg media create-image run '{"name": "splash-low.jpg"}'

        ./run.sh media list-images run

        ./run.sh media get-image run '{"image_id": "1"}'

        ./run.sh -fo splash-media-id-1.png media get-image-file-content run '{"image_id": "1"}'

        """

        #
        # init
        #

        logged_out_ctx = self.crud_ctx.copy()
        user = self.crud_users[0]['user']
        user_env = self.crud_users[0]['env']

        sample_path = 'tests/samples/splash-orig.png'
        sample_size = 4007485
        sample_checksum = 'bf3bc28ca617270e3537761e2b9c935f2ea54b6d4debe926a06e765c2bab414e'

        self.assertTrue(os.path.exists(sample_path), 'Sample file for ingest test does not exist')
        self.assertEqual(os.path.getsize(sample_path), sample_size, 'Sample file size does not match expected size')

        # test create image #

        json_params = json.dumps({
            'name': 'splash-orig.png'
        })

        cmd = self.cmd + ['-fi', sample_path, 'media', 'create-image', io_type, json_params]

        # ensure logged out user cannot create image #

        self._run_cmd(cmd, env=logged_out_ctx, expected_code=1)

        # create image with logged in user #

        create_cmd_result = self._run_cmd(cmd, env=user_env)
        create_result = json.loads(create_cmd_result.stdout)['result']
        self.assertIn('image_id', create_result, 'Create image result does not contain image_id')
        self.assertIn('file_id', create_result, 'Create image result does not contain file_id')
        self.assertIn('message', create_result, 'Create image result does not contain message')

        self.assertTrue(isinstance(create_result['image_id'], str), 'Create image result image_id is not a string')
        self.assertTrue(isinstance(create_result['file_id'], str), 'Create image result file_id is not a string')

        # get image #

        get_image_cmd = self.cmd + ['media', 'get-image', io_type, json.dumps({'image_id': create_result['image_id']})]
        get_image_result = self._run_cmd(get_image_cmd, env=user_env)
        get_image = json.loads(get_image_result.stdout)['result']
        self.assertEqual(get_image['id'], create_result['image_id'], 'Get image result id does not match created image_id')
        self.assertEqual(get_image['file_id'], create_result['file_id'], 'Get image result file_id does not match created file_id')
        self.assertEqual(get_image['file_size'], sample_size, 'Get image result size does not match expected size')
        self.assertEqual(get_image['user_id'], user['id'], 'Get image result user_id does not match expected user_id')

        # list images #

        list_images_cmd_1 = self.cmd + ['media', 'list-images', io_type, json.dumps({'image_id': create_result['image_id']})]
        list_images_cmd_2 = self.cmd + ['media', 'list-images', io_type, json.dumps({'file_id': create_result['file_id'], 'user_id': user['id']})]

        list_cmds = [list_images_cmd_1, list_images_cmd_2]

        for cmd in list_cmds:

            list_images_result = self._run_cmd(cmd, env=user_env)
            list_images = json.loads(list_images_result.stdout)['result']
            self.assertEqual(len(list_images['items']), 1, 'Should be exactly 1 image in list images result')
            self.assertEqual(list_images['total'], 1, 'Total in list images result should be 1')

            image_record = list_images['items'][0]
            self.assertEqual(image_record['id'], create_result['image_id'], 'Image ID in list images result does not match created image_id')
            self.assertEqual(image_record['file_id'], create_result['file_id'], 'Image file_id in list images result does not match created file_id')
            self.assertEqual(image_record['file_size'], sample_size, 'Image size in list images result does not match expected size')
            self.assertEqual(image_record['user_id'], user['id'], 'Image user_id in list images result does not match expected user_id')

        # get file content (download image) #

        local_image_dest = os.path.join(self.test_dir, f'splash-media-media-content-{io_type}.png')
        get_image_file_cmd = self.cmd + ['-fo', local_image_dest, 'media', 'get-media-file-content', io_type, json.dumps({'image_id': create_result['image_id']})]
        get_image_file_output = self._run_cmd(get_image_file_cmd, env=user_env)
        get_image_file_result = json.loads(get_image_file_output.stdout)['result']
        self.assertTrue(get_image_file_result['acknowledged'], 'Get media file content result not acknowledged')
        self.assertTrue(os.path.exists(local_image_dest), 'Local file for media content does not exist after get-media-file-content command')
        self.assertEqual(os.path.getsize(local_image_dest), sample_size, 'Local file size for media content does not match expected size')
        with open(local_image_dest, 'rb') as f:
            local_checksum = hashlib.sha3_256(f.read()).hexdigest()
        self.assertEqual(local_checksum, sample_checksum, 'Local file checksum for media content does not match expected checksum')

    def test_cli_run_media_create_image_flow(self):
        self._test_media_create_image_flow(self.crud_ctx, 'run')

    def test_cli_http_media_create_image_flow(self):
        self._test_media_create_image_flow(self.crud_ctx, 'http')

    def _test_media_ingest_master_image_flow(self, ctx:dict, io_type:str):
        """
        ./run.sh --log -fi ./tests/samples/splash-orig.png media ingest-master-image run '{"name": "splash-orig.png"}'
        """

        #
        # init
        #

        logged_out_ctx = self.crud_ctx.copy()
        user = self.crud_users[0]['user']
        user_env = self.crud_users[0]['env']

        sample_path = 'tests/samples/splash-orig.png'

        self.assertTrue(os.path.exists(sample_path), 'Sample file for ingest master image test does not exist')

        json_params = json.dumps({
            'name': 'splash-orig.png',
            'thumbnail_max_size': 200
        })

        cmd = self.cmd + ['-fi', sample_path, 'media', 'ingest-master-image', io_type, json_params]

        # ensure logged out user cannot ingest master image #

        self._run_cmd(cmd, env=logged_out_ctx, expected_code=1)

        # ingest master image with logged in user #

        result_output = self._run_cmd(cmd, env=user_env)
        result = json.loads(result_output.stdout)['result']

        self.assertIn('master_image_id', result, 'Ingest master image result does not contain master_image_id')
        self.assertIn('original_image_id', result, 'Ingest master image result does not contain original_image_id')
        self.assertIn('web_image_id', result, 'Ingest master image result does not contain web_image_id')
        self.assertIn('thumbnail_image_id', result, 'Ingest master image result does not contain thumbnail_image_id')
        self.assertIn('message', result, 'Ingest master image result does not contain message')

        self.assertTrue(isinstance(result['master_image_id'], str), 'master_image_id is not a string')
        self.assertTrue(isinstance(result['original_image_id'], str), 'original_image_id is not a string')
        self.assertTrue(isinstance(result['web_image_id'], str), 'web_image_id is not a string')
        self.assertTrue(isinstance(result['thumbnail_image_id'], str), 'thumbnail_image_id is not a string')

        # verify three distinct image records were created #

        ids = [result['original_image_id'], result['web_image_id'], result['thumbnail_image_id']]
        self.assertEqual(len(set(ids)), 3, 'Expected 3 distinct image IDs for original, web, and thumbnail')

        # verify thumbnail is smaller than original #

        get_original_cmd = self.cmd + ['media', 'get-image', io_type, json.dumps({'image_id': result['original_image_id']})]
        get_thumb_cmd = self.cmd + ['media', 'get-image', io_type, json.dumps({'image_id': result['thumbnail_image_id']})]

        original_output = self._run_cmd(get_original_cmd, env=user_env)
        original_image = json.loads(original_output.stdout)['result']

        thumb_output = self._run_cmd(get_thumb_cmd, env=user_env)
        thumb_image = json.loads(thumb_output.stdout)['result']

        self.assertLessEqual(thumb_image['width'], 200, 'Thumbnail width should not exceed thumbnail_max_size')
        self.assertLessEqual(thumb_image['height'], 200, 'Thumbnail height should not exceed thumbnail_max_size')
        self.assertGreater(original_image['width'], thumb_image['width'], 'Original should be wider than thumbnail')

        # get master image record #

        get_master_cmd = self.cmd + ['media', 'get-master-image', io_type, json.dumps({'master_image_id': result['master_image_id']})]

        master_output = self._run_cmd(get_master_cmd, env=user_env)
        master_image = json.loads(master_output.stdout)['result']

        self.assertIn('id', master_image, 'get_master_image result does not contain id')
        self.assertIn('original_image_id', master_image, 'get_master_image result does not contain original_image_id')
        self.assertIn('web_image_id', master_image, 'get_master_image result does not contain web_image_id')
        self.assertIn('thumbnail_image_id', master_image, 'get_master_image result does not contain thumbnail_image_id')
        self.assertIn('user_id', master_image, 'get_master_image result does not contain user_id')
        self.assertIn('created_at', master_image, 'get_master_image result does not contain created_at')

        self.assertEqual(master_image['id'], result['master_image_id'], 'Master image ID does not match')
        self.assertEqual(master_image['original_image_id'], result['original_image_id'], 'original_image_id does not match')
        self.assertEqual(master_image['web_image_id'], result['web_image_id'], 'web_image_id does not match')
        self.assertEqual(master_image['thumbnail_image_id'], result['thumbnail_image_id'], 'thumbnail_image_id does not match')

        # ensure logged out user cannot get master image #

        self._run_cmd(get_master_cmd, env=logged_out_ctx, expected_code=1)

        # list master images #

        list_master_cmd = self.cmd + ['media', 'list-master-images', io_type, json.dumps({'offset': 0, 'size': 50, 'master_image_id': '-1', 'user_id': '-1'})]

        list_output = self._run_cmd(list_master_cmd, env=user_env)
        list_result = json.loads(list_output.stdout)['result']

        self.assertIn('items', list_result, 'list_master_images result does not contain items')
        self.assertIn('total', list_result, 'list_master_images result does not contain total')
        self.assertGreaterEqual(list_result['total'], 1, 'Expected at least one master image in list')
        self.assertGreaterEqual(len(list_result['items']), 1, 'Expected at least one master image item in list')

        # filter by master_image_id #

        list_by_id_cmd = self.cmd + ['media', 'list-master-images', io_type, json.dumps({'offset': 0, 'size': 50, 'master_image_id': result['master_image_id'], 'user_id': '-1'})]

        list_by_id_output = self._run_cmd(list_by_id_cmd, env=user_env)
        list_by_id_result = json.loads(list_by_id_output.stdout)['result']

        self.assertEqual(list_by_id_result['total'], 1, 'Expected exactly one master image when filtering by master_image_id')
        self.assertEqual(list_by_id_result['items'][0]['id'], result['master_image_id'], 'Filtered master image ID does not match')

        # ensure logged out user cannot list master images #

        self._run_cmd(list_master_cmd, env=logged_out_ctx, expected_code=1)

        # get master image file content (download original image via master_image_id) #

        local_master_content_dest = os.path.join(self.test_dir, f'splash-master-content-{io_type}.png')
        get_master_content_cmd = self.cmd + ['-fo', local_master_content_dest, 'media', 'get-media-file-content', io_type, json.dumps({'master_image_id': result['master_image_id']})]

        get_master_content_output = self._run_cmd(get_master_content_cmd, env=user_env)
        get_master_content_result = json.loads(get_master_content_output.stdout)['result']
        self.assertTrue(get_master_content_result['acknowledged'], 'Get media file content via master_image_id not acknowledged')
        self.assertTrue(os.path.exists(local_master_content_dest), 'Local file for master image content does not exist after get-media-file-content command')

        # ensure both image_id and master_image_id together throws an error #

        get_both_cmd = self.cmd + ['media', 'get-media-file-content', io_type, json.dumps({'image_id': result['original_image_id'], 'master_image_id': result['master_image_id']})]
        self._run_cmd(get_both_cmd, env=user_env, expected_code=1)

        # ensure neither image_id nor master_image_id throws an error #

        get_neither_cmd = self.cmd + ['media', 'get-media-file-content', io_type, json.dumps({})]
        self._run_cmd(get_neither_cmd, env=user_env, expected_code=1)

    def test_cli_run_media_ingest_master_image_flow(self):
        self._test_media_ingest_master_image_flow(self.crud_ctx, 'run')

    def test_cli_http_media_ingest_master_image_flow(self):
        self._test_media_ingest_master_image_flow(self.crud_ctx, 'http')

    # crud tests #

    def _test_cli_crud_commands(self, command_type:str, user_index:int):

        create_user = self.crud_users[user_index]['user']
        create_user_env = self.crud_users[user_index]['env']
        other_user = self.crud_users[0]['user']
        other_user_env = self.crud_users[0]['env']
        self.assertNotEqual(user_index, 0, 'user_index must not be 0 to ensure different users for testing')

        # create test cases #

        jobs = []
        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']
            for model_name, model in module['models'].items():
                jobs.append((module_name_kebab, model_name, model, command_type, self.cmd, self.crud_ctx, create_user, create_user_env, other_user, other_user_env))

        # parallel process tests #
        
        self.pool.starmap(run_cli_crud_for_model, jobs)
 
    def test_cli_db_crud(self):
        self._test_cli_crud_commands('db', 1)

    def test_cli_http_crud(self):
        self._test_cli_crud_commands('http', 2)

    def test_server_crud_endpoints(self):

        self._check_servers_running()
        
        base_ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }

        base_ctx.update(self.crud_ctx)

        logged_out_ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }

        #
        # create test cases
        #

        logged_out_ctx.update(self.crud_ctx)

        alice_user = self.crud_users[0]['user']
        alice_ctx = deepcopy(base_ctx)
        alice_ctx['headers']['Authorization'] = self.crud_users[0]['env']['Authorization']
        bob_user = self.crud_users[1]['user']
        bob_ctx = deepcopy(base_ctx)
        bob_ctx['headers']['Authorization'] = self.crud_users[1]['env']['Authorization']
        charlie_user = self.crud_users[2]['user']
        charlie_ctx = deepcopy(base_ctx)
        charlie_ctx['headers']['Authorization'] = self.crud_users[2]['env']['Authorization']

        jobs = []
        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']
            for model_name, model in module['models'].items():
                jobs.append((module_name_kebab, model_name, model, base_ctx, logged_out_ctx, alice_ctx, bob_ctx, charlie_ctx, alice_user, bob_user, charlie_user))

        #
        # parallel process tests
        #

        self.pool.starmap(run_server_crud_for_model, jobs)

    # pagination tests #

    def _test_cli_pagination_command(self, command_type:str):

        # init tests #

        logged_out_ctx = self.pagination_ctx.copy()
        commands = []
        test_cases = []

        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']

            for model in module['models'].values():

                if model['auth']['max_models_per_user'] == 0:
                    continue  # skip models that do not allow any data

                model_name_kebab = model['name']['kebab_case']
                model_list_command = self.cmd + [module_name_kebab, model_name_kebab, command_type, 'list']
                hidden = model['hidden']
    
                if model['auth']['require_login'] and not hidden:
                    self._run_cmd(model_list_command + ['--size=10', '--offset=0'], expected_code=1, env=logged_out_ctx)
                    ctx = self.pagination_user['env']
                else:
                    ctx = self.pagination_ctx

                if hidden is True:
                    self._run_cmd(model_list_command + ['--size=10', '--offset=0'], expected_code=2, env=self.pagination_ctx)
                    continue

                for case in self.pagination_cases:
                    size = case['size']
                    expected_pages = case['expected_pages']
                    offset = 0

                    for page in range(expected_pages):
                        commands.append((model_list_command + [f'--size={size}', f'--offset={offset}'], ctx))
                        test_cases.append((module_name_kebab, model_name_kebab, size, expected_pages, page, offset))
                        offset += size

        # run tests #

        results = self.pool.starmap(run_cmd, commands)

        # confirm results #
        
        grouped = defaultdict(list)
        for (module_name_kebab, model_name_kebab, size, expected_pages, page, offset), (cmd_args, code, stdout, stderr) in zip(test_cases, results):
            key = (module_name_kebab, model_name_kebab, size, expected_pages)
            grouped[key].append((page, offset, code, stdout, stderr))

        for (module_name_kebab, model_name_kebab, size, expected_pages), pages in grouped.items():
            pages.sort()
            page_count = 0
            for page, offset, code, stdout, stderr in pages:
                self.assertEqual(code, 0, f'Pagination for {model_name_kebab} page {page} returned non-zero exit code. STDOUT: {stdout} STDERR: {stderr}')
                response = json.loads(stdout)
                self.assertEqual(response['total'], self.pagination_total_models, f'Pagination for {model_name_kebab} page {page} returned incorrect total')
                items = response['items']
                self.assertLessEqual(len(items), size, f'Pagination for {model_name_kebab} returned more items than size {size}')
                if len(items) == 0:
                    break
                page_count += 1
            self.assertEqual(page_count, expected_pages, f'Pagination for {model_name_kebab} returned {page_count} pages, expected {expected_pages}')

    def test_cli_db_pagination(self):
        self._test_cli_pagination_command('db')

    def test_cli_http_pagination(self):
        self._test_cli_pagination_command('http')

    def test_server_pagination_endpoints(self):

        self._check_servers_running()
        
        base_ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }

        base_ctx.update(self.pagination_ctx)

        logged_out_ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }

        logged_out_ctx.update(self.pagination_ctx)

        request_jobs = []
        test_cases = []

        #
        # create test cases
        #

        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']
            for model_name, model in module['models'].items():

                if model['auth']['max_models_per_user'] == 0:
                    continue  # skip models that do not allow any data

                hidden = model['hidden']
                model_name_kebab = model['name']['kebab_case']

                if model['auth']['require_login'] and not hidden:
                    status, response = request(
                        logged_out_ctx,
                        'GET',
                        f'/api/{module_name_kebab}/{model_name_kebab}?size=10&offset=0',
                        None
                    )
                    self.assertEqual(status, 401, f'Pagination for {model_name_kebab} without login did not return 401 Unauthorized, response: {response}')
                    ctx = deepcopy(base_ctx)
                    ctx['headers']['Authorization'] = self.pagination_user['env']['Authorization']
                else:
                    ctx = base_ctx

                if hidden:
                    status, response = request(ctx, 'GET', f'/api/{module_name_kebab}/{model_name_kebab}?size=10&offset=0', None)
                    self.assertEqual(status, 404, f'Pagination for hidden {model_name_kebab} did not return 404 Not Found, response: {response}')
                    continue

                for case in self.pagination_cases:
                    size = case['size']
                    expected_pages = case['expected_pages']
                    offset = 0

                    for page in range(expected_pages):
                        request_jobs.append((ctx, 'GET', f'/api/{module_name_kebab}/{model_name_kebab}?size={size}&offset={offset}', None))
                        test_cases.append((module_name_kebab, model_name_kebab, size, expected_pages, page, offset))
                        offset += size

        #
        # parallel process tests
        #

        results = self.pool.starmap(request, request_jobs)

        #
        # confirm results
        #

        grouped = defaultdict(list)
        for (module_name_kebab, model_name_kebab, size, expected_pages, page, offset), (status, response) in zip(test_cases, results):
            key = (module_name_kebab, model_name_kebab, size, expected_pages)
            grouped[key].append((page, offset, status, response))

        for (module_name_kebab, model_name_kebab, size, expected_pages), pages in grouped.items():
            pages.sort()
            page_count = 0
            for page, offset, status, response in pages:
                self.assertEqual(status, 200, f'Pagination for {model_name_kebab} page {page} did not return status 200 OK, response: {response}')
                self.assertEqual(response['total'], self.pagination_total_models, f'Pagination for {model_name_kebab} page {page} returned incorrect total')
                items = response['items']
                self.assertLessEqual(len(items), size, f'Pagination for {model_name_kebab} returned more items than size {size}')
                if len(items) == 0:
                    break
                page_count += 1
            self.assertEqual(page_count, expected_pages, f'Pagination for {model_name_kebab} returned {page_count} pages, expected {expected_pages}')
      
    # op tests #

    def _test_op_cli(self, command_type:str):
        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']

            for op in module.get('ops', {}).values():
                op_name_kebab = op['name']['kebab_case']

                test_cases = op.get('tests', {}).get('test_cases', [])
                for n, test_case in enumerate(test_cases):
                    json_data = json.dumps(test_case['params'])
                    hidden = op['hidden']
                    args = self.cmd + [module_name_kebab, op_name_kebab, command_type, json_data]
                    if hidden:
                        self._run_cmd(args, env=self.crud_ctx, expected_code=2)
                    else:
                        result = self._run_cmd(args, env=self.crud_ctx)
                        result = json.loads(result.stdout)['result']
                        expected_result = test_case['expected_result']
                        self.assertEqual(result, expected_result, f'OP {module_name_kebab}.{op_name_kebab} output does not match expected result for index: {n}')

    def test_op_cli_run(self):
        self._test_op_cli('run')
    
    def test_op_cli_http(self):
        self._test_op_cli('http')
    
    def test_op_server_op(self):

        self._check_servers_running()

        base_ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }

        base_ctx.update(self.crud_ctx)

        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']

            for op in module.get('ops', {}).values():
                op_name_kebab = op['name']['kebab_case']
                test_cases = op.get('tests', {}).get('test_cases', [])

                for n, test_case in enumerate(test_cases):
                    json_data = json.dumps(test_case['params']).encode()
                    hidden = op['hidden']
                    op_url = f'/api/{module_name_kebab}/{op_name_kebab}'

                    status, response = request(base_ctx, 'POST', op_url, json_data)
                    
                    if hidden:
                        self.assertEqual(status, 404, f'OP {module_name_kebab}.{op_name_kebab} hidden did not return 404 Not Found, response: {response}')
                    else:
                        self.assertEqual(status, 200, f'OP {module_name_kebab}.{op_name_kebab} did not return status 200 OK, response: {response}')
                        result = response['result']
                        expected_result = test_case['expected_result']
                        self.assertEqual(result, expected_result, f'OP {module_name_kebab}.{op_name_kebab} output does not match expected result for index: {n}')

    # validation tests #

    def _test_cli_validation_error(self, command_type:str, user_index:int):
        jobs = []
        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']
            for model in module['models'].values():
                jobs.append((module_name_kebab, model, command_type, user_index, self.cmd, self.crud_users, self.crud_ctx))
        self.pool.starmap(run_cli_validation_error_for_model, jobs)

    def test_cli_db_validation_error(self):
        self._test_cli_validation_error('db', 3)


    def test_cli_http_validation_error(self):
        self._test_cli_validation_error('http', 4)

    def test_server_validation_error(self):
        self._check_servers_running()
        base_ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }
        base_ctx.update(self.crud_ctx)

        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']

            for model in module['models'].values():

                if model['hidden'] is True:
                    continue

                if model['auth']['max_models_per_user'] == 0:
                    continue  # skip models that do not allow any data

                model_name_kebab = model['name']['kebab_case']

                if model['auth']['require_login']:
                    ctx = base_ctx.copy()
                    ctx['headers']['Authorization'] = self.crud_users[0]['env']['Authorization']
                else:
                    ctx = base_ctx

                # create a valid model to update with invalid data
                example_to_update = example_from_model(model)
                create_status, create_resp = request(
                    ctx,
                    'POST',
                    f'/api/{module_name_kebab}/{model_name_kebab}',
                    json.dumps(example_to_update).encode()
                )
                self.assertEqual(create_status, 200, f'Create for validation error test failed: {create_resp}')
                update_model_id = str(create_resp['id'])

                for invalid_example, invalid_field_name in model_validation_errors(model):
                    # create (invalid)
                    status, output = request(
                        ctx,
                        'POST',
                        f'/api/{module_name_kebab}/{model_name_kebab}',
                        json.dumps(invalid_example).encode()
                    )
                    self.assertEqual(status, 400, f'Expected 400 for invalid create, got {status}, resp: {output} for field {invalid_field_name}')
                    output_error = output.get('error', {})
                    self.assertEqual(
                        output_error.get('code', 'not-set'), 
                        'VALIDATION_ERROR', 
                        f'Expected VALIDATION_ERROR code for {model_name_kebab} with invalid data {invalid_example}, got {output} for field {invalid_field_name}'
                    )
                    self.assertIn('message', output_error, f'Expected error message in response for {model_name_kebab} with invalid data {invalid_example}, got {output} for field {invalid_field_name}')

                    # update (invalid)
                    status, output = request(
                        ctx,
                        'PUT',
                        f'/api/{module_name_kebab}/{model_name_kebab}/{update_model_id}',
                        json.dumps(invalid_example).encode()
                    )
                    output_error = output.get('error', {})
                    self.assertEqual(status, 400, f'Expected 400 for invalid update, got {status}, resp: {output} for field {invalid_field_name}')
                    self.assertEqual(
                        output_error.get('code', 'not-set'), 
                        'VALIDATION_ERROR', 
                        f'Expected VALIDATION_ERROR code for {model_name_kebab} with invalid data {invalid_example}, got {output} for field {invalid_field_name}'
                    )
                    self.assertIn('message', output_error, f'Expected error message in response for {model_name_kebab} with invalid data {invalid_example}, got {output} for field {invalid_field_name}')

                # read back original example to ensure it was not modified
                status, read_model = request(
                    ctx,
                    'GET',
                    f'/api/{module_name_kebab}/{model_name_kebab}/{update_model_id}',
                    None
                )
                self.assertEqual(status, 200, f'Read after validation error for {model["name"]["pascal_case"]} did not return 200 OK, resp: {read_model}')

                del read_model['id']
                if model['auth']['require_login']:
                    example_to_update['user_id'] = self.crud_users[0]['user']['id']
                
                self.assertEqual(read_model, example_to_update, f'Read after validation error for {model["name"]["pascal_case"]} does not match original example data, expected: {example_to_update} got: {read_model}')

    # other tests #

    def test_debug_responses(self):
        """
        make request to /api/debug/PlainTextResponse
            expect 200 with request body:
              This is a plain text debug response
        """

        ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }
        ctx.update(self.crud_ctx)

        #
        # success
        #

        # plain text response #

        status, response = request(ctx, 'GET', '/api/debug/PlainTextResponse', None, decode_json=False)
        self.assertEqual(status, 200)
        self.assertEqual(response, 'This is a plain text debug response')

        # json response #

        status, response = request(ctx, 'GET', '/api/debug/JSONResponse', None)
        self.assertEqual(status, 200)
        self.assertEqual(response, {'message': 'This is a JSON debug response'})

        #
        # error
        #

        # not found response #

        status, response = request(ctx, 'GET', '/api/debug/NotFoundError', None)
        self.assertEqual(status, 404)
        self.assertEqual(response.get('error', {}).get('code', '-'), 'NOT_FOUND')
        self.assertEqual(response.get('error', {}).get('message', ''), 'Debug: NotFoundError thrown')

        # authentication error #

        status, response = request(ctx, 'GET', '/api/debug/AuthenticationError', None)
        self.assertEqual(status, 401)
        self.assertEqual(response.get('error', {}).get('code', '-'), 'AUTHENTICATION_ERROR')
        self.assertEqual(response.get('error', {}).get('message', ''), 'Debug: AuthenticationError thrown')

        # forbidden error #

        status, response = request(ctx, 'GET', '/api/debug/ForbiddenError', None)
        self.assertEqual(status, 403)
        self.assertEqual(response.get('error', {}).get('code', '-'), 'FORBIDDEN_ERROR')
        self.assertEqual(response.get('error', {}).get('message', ''), 'Debug: ForbiddenError thrown')

        # validation error #

        status, response = request(ctx, 'GET', '/api/debug/MappValidationError', None)
        self.assertEqual(status, 400)
        self.assertEqual(response.get('error', {}).get('code', '-'), 'VALIDATION_ERROR')
        self.assertEqual(response.get('error', {}).get('message', ''), 'Debug: MappValidationError thrown')
        field_errors = response.get('error', {}).get('field_errors', {})
        self.assertEqual(field_errors, {'field': 'example error'}, f'Unexpected field_errors content: {field_errors}')

        # request error #

        status, response = request(ctx, 'GET', '/api/debug/RequestError', None)
        self.assertEqual(status, 400)
        self.assertEqual(response.get('error', {}).get('code', '-'), 'REQUEST_ERROR')
        self.assertEqual(response.get('error', {}).get('message', ''), 'Debug: RequestError thrown')

        # exception #

        status, response = request(ctx, 'GET', '/api/debug/Exception', None)
        self.assertEqual(status, 500)
        error = response.get('error', {})
        self.assertIn('request_id', error, 'Expected request_id in error response for Exception')
        self.assertEqual(response.get('error', {}).get('code', '-'), 'INTERNAL_SERVER_ERROR')
        self.assertEqual(response.get('error', {}).get('message', ''), 'Contact support or check logs for details')

        response_str = json.dumps(response)
        self.assertNotIn('This error should not be shown to users', response_str, 'Internal error message leaked to user in Exception response')

    def test_cli_help_menus(self):

        help_jobs = []

        project_kebab = self.spec['project']['name']['kebab_case']
        global_help_text = ':: ' + project_kebab

        # global help
        for global_help_arg in ['help', '--help', '-h']:
            args = self.cmd + [global_help_arg]
            env = self.crud_ctx
            def assertion(stdout, stderr, code, args=args):
                self.assertEqual(code, 0, f"Global help failed: {' '.join(args)}\n{stdout}\n{stderr}")
                self.assertIn(global_help_text, stdout)
            help_jobs.append((args, env, assertion))

        # create tables help
        create_tables_help_text = global_help_text + ' :: create-tables'
        for create_tables_help_arg in ['help', '--help', '-h']:
            args = self.cmd + ['create-tables', create_tables_help_arg]
            env = self.crud_ctx
            def assertion(stdout, stderr, code, args=args):
                self.assertEqual(code, 0, f"Create-tables help failed: {' '.join(args)}\n{stdout}\n{stderr}")
                self.assertIn(create_tables_help_text, stdout)
            help_jobs.append((args, env, assertion))

        # module/model/io/op help
        for module in self.spec['modules'].values():
            module_help_text = global_help_text + f' :: {module["name"]["kebab_case"]}'
            for module_help_arg in ['help', '--help', '-h']:
                args = self.cmd + [module['name']['kebab_case'], module_help_arg]
                env = self.crud_ctx
                def assertion(stdout, stderr, code, args=args, expected=module_help_text):
                    self.assertEqual(code, 0, f"Module help failed: {' '.join(args)}\n{stdout}\n{stderr}")
                    self.assertIn(expected, stdout)
                help_jobs.append((args, env, assertion))

            for model in module.get('models', {}).values():
                if model['hidden']:
                    continue
                model_help_text = module_help_text + f' :: {model["name"]["kebab_case"]}'
                for model_help_arg in ['help', '--help', '-h']:
                    args = self.cmd + [module['name']['kebab_case'], model['name']['kebab_case'], model_help_arg]
                    env = self.crud_ctx
                    def assertion(stdout, stderr, code, args=args, expected=model_help_text):
                        self.assertEqual(code, 0, f"Model help failed: {' '.join(args)}\n{stdout}\n{stderr}")
                        self.assertIn(expected, stdout)
                    help_jobs.append((args, env, assertion))

                for io in ['db', 'http']:
                    io_help_text = model_help_text + f' :: {io}'
                    for io_help_arg in ['help', '--help', '-h']:
                        args = self.cmd + [module['name']['kebab_case'], model['name']['kebab_case'], io, io_help_arg]
                        env = self.crud_ctx
                        def assertion(stdout, stderr, code, args=args, expected=io_help_text):
                            self.assertEqual(code, 0, f"IO help failed: {' '.join(args)}\n{stdout}\n{stderr}")
                            self.assertIn(expected, stdout)
                        help_jobs.append((args, env, assertion))

                    crud_ops = ['create', 'read', 'update', 'delete', 'list']
                    if io == 'db':
                        ops_to_run = crud_ops + ['create-table']
                    else:
                        ops_to_run = crud_ops

                    for op in ops_to_run:
                        op_help_text = io_help_text + f' :: {op}'
                        for op_help_arg in ['help', '--help', '-h']:
                            args = self.cmd + [module['name']['kebab_case'], model['name']['kebab_case'], io, op, op_help_arg]
                            env = self.crud_ctx
                            def assertion(stdout, stderr, code, args=args, expected=op_help_text):
                                self.assertEqual(code, 0, f"Op help failed: {' '.join(args)}\n{stdout}\n{stderr}")
                                self.assertIn(expected, stdout.replace('\n', ''))
                            help_jobs.append((args, env, assertion))

        with multiprocessing.Pool(processes=self.threads) as pool:
            results = pool.starmap(run_cmd, [(args, env) for args, env, _ in help_jobs])

        for (args, code, stdout, stderr), (_, _, assertion) in zip(results, help_jobs):
            assertion(stdout, stderr, code, args)
    
    def test_secure_field_redaction(self):
        """
        Confirm secure fields are redacted in op output

        This command:
            ./mapp auth login-user run 

        Should return:
            {
            "result": {
                "access_token": "REDACTED",
                "token_type": "bearer"
            }
        }

        But this command:
            ./mapp auth login-user run --show

        Should return the unredacted output including the access token value, e.g.
        {
            "result": {
                "access_token": "<actual access token>",
                "token_type": "bearer"
            }
        }
        """

        env = self.crud_ctx.copy()

        try:
            del env['MAPP_CLI_ACCESS_TOKEN']
        except KeyError:
            pass

        env['MAPP_CLI_SESSION_FILE'] = os.path.join(self.test_dir, 'secure-field-test-session.json')
        try:
            os.remove(env['MAPP_CLI_SESSION_FILE'])
        except FileNotFoundError:
            pass

        # logout
        args_logout = self.cmd + ['auth', 'logout-user', 'run']
        _, code, stdout, stderr = run_cmd(args_logout, env)

        login_params = json.dumps({'email': 'evelyn@example.com', 'password': self.test_password})
        
        # confirm access_token is redacted
        args = self.cmd + ['auth', 'login-user', 'run', login_params]
        _, code, stdout, stderr = run_cmd(args, env)
        self.assertEqual(code, 0, f"Secure field redaction failed: {' '.join(args)}\n{stdout}\n{stderr}")
        json_output = json.loads(stdout)
        self.assertIn("access_token", json_output["result"])
        self.assertEqual(json_output["result"]["access_token"], "REDACTED")

        # logout
        args_logout = self.cmd + ['auth', 'logout-user', 'run']
        _, code, stdout, stderr = run_cmd(args_logout, env)
        self.assertEqual(code, 0, f"Logout failed: {' '.join(args_logout)}\n{stdout}\n{stderr}")

        # confirm access_token is unredacted when --show is passed
        args_show = self.cmd + ['auth', 'login-user', 'run', '--show', login_params]
        _, code, stdout, stderr = run_cmd(args_show, env)
        self.assertEqual(code, 0, f"Secure field unredacted output failed: {' '.join(args_show)}\n{stdout}\n{stderr}")
        json_output = json.loads(stdout)
        self.assertIn("access_token", json_output["result"])
        self.assertNotEqual(json_output["result"]["access_token"], "REDACTED")
        self.assertGreater(len(json_output["result"]["access_token"]), 25)


def test_spec(cli_args:list[str], host:str|None, env_vars:dict, use_cache:bool=False, app_type:str='', verbose:bool=False) -> bool:
    if cli_args is None:
        raise ValueError('args must be provided as a list of strings')
    
    try:
        spec_path = env_vars['MAPP_SPEC_FILE']
    except KeyError:
        raise ValueError('MAPP_SPEC_FILE must be set in env')

    test_suite = unittest.TestSuite()
    TestMTemplateApp.spec = load_generator_spec(spec_path)
    TestMTemplateApp.cmd = cli_args
    TestMTemplateApp.host = host
    TestMTemplateApp.env_vars = env_vars
    TestMTemplateApp.use_cache = use_cache
    TestMTemplateApp.app_type = app_type

    # Support test filtering by name
    test_filters = getattr(test_spec, '_test_filters', None)
    loader = unittest.TestLoader()
    if test_filters:

        # Only add tests matching any filter pattern (glob-style, case-insensitive)
        for test_name in loader.getTestCaseNames(TestMTemplateApp):
            if any(fnmatch.fnmatchcase(test_name.lower(), pat.lower()) for pat in test_filters):
                test_case = TestMTemplateApp(test_name)
                test_case.maxDiff = None
                test_suite.addTest(test_case)
    else:
        tests = loader.loadTestsFromTestCase(TestMTemplateApp)
        for test in tests:
            test.maxDiff = None
            test_suite.addTest(test)

    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(test_suite)

    TestMTemplateApp.spec = None
    TestMTemplateApp.cmd = None
    TestMTemplateApp.host = None

    return result.wasSuccessful()

def test_npm(npm_run:str, cli_args:list[str], host:str|None, env_vars:dict, use_cache:bool=False, app_type:str='', verbose:bool=False) -> bool:
    if cli_args is None:
        raise ValueError('args must be provided as a list of strings')
    
    try:
        spec_path = env_vars['MAPP_SPEC_FILE']
    except KeyError:
        raise ValueError('MAPP_SPEC_FILE must be set in env_vars')
    
    # start servers

    TestMTemplateApp.spec = load_generator_spec(spec_path)
    TestMTemplateApp.cmd = cli_args
    TestMTemplateApp.host = host
    TestMTemplateApp.env_vars = env_vars
    TestMTemplateApp.use_cache = use_cache
    TestMTemplateApp.app_type = app_type
    TestMTemplateApp.setUpClass()
    print(':: server setup complete')

    # run npm command #

    npm_cmd = ['npm', 'run', npm_run]
    print(f':: running npm command: {" ".join(npm_cmd)}')

    test_result = False
    
    try:
        process = subprocess.Popen(npm_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # run command and forward stdout/stderr in real time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output, end='')

        # process exited
        stderr = process.stderr.read()
        if stderr:
            print(stderr, end='')

        return_code = process.poll()
        print(f':: npm command exit code {return_code}')
        if return_code == 0:
            test_result = True

    except Exception as e:
        print(f':: exception while running npm command: {e}')

    finally:
        TestMTemplateApp.tearDownClass()

    print(f'\n:: npm test result: {"PASS" if test_result else "FAIL"}\n\n')
    return test_result

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Test mapp spec app', prog='mapp.test')
    parser.add_argument('--cmd', type=str, nargs='*', required=True, help='CLI command for generated app')
    parser.add_argument('--env-file', type=str, required=True, help='path to .env file to load for tests')
    parser.add_argument('--host', type=str, default=None, help='host for http client in tests (if host diff than in spec file)')
    parser.add_argument('--test-filter', type=str, nargs='*', default=None, help='Glob pattern(s) to filter test names (e.g. test_cli_db*)')
    parser.add_argument('--use-cache', action='store_true', help='Use cached test resources if available')
    parser.add_argument('--app-type', type=str, default='', help='Supply "python" to run setup for python apps')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--npm-run', type=str, help='Start test servers, then run "npm run <arg>", ex: "--npm-run test"')

    args = parser.parse_args()

    env_vars = dotenv_values(args.env_file)

    if args.npm_run:
        test_npm(args.npm_run, args.cmd, args.host, env_vars, args.use_cache, args.app_type, args.verbose)

    else:
        if args.test_filter:
            # Attach filter patterns to test_spec function for access
            test_spec._test_filters = args.test_filter
        else:
            test_spec._test_filters = None

        test_spec(args.cmd, args.host, env_vars, args.use_cache, args.app_type, args.verbose)