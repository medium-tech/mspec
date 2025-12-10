#!/usr/bin/env python3
import argparse
import os
import sys

from getpass import getpass

import dotenv
dotenv.load_dotenv(dotenv_path='.env', override=True)

# import after loading env vars so that MAPP_APP_PATH is set correctly
from mapp.auth import ROOT_PASSWORD_HASH_FILE, _get_password_hash, _verify_root_password
from mapp.errors import MappError, MappValidationError


def cmd_create_pw():
    password = getpass('Enter new root password: ')
    password_confirm = getpass('Confirm new root password: ')

    if password != password_confirm:
        field_errors = {'password_confirm': 'Password confirmation does not match password'}
        raise MappValidationError('Passwords do not match', field_errors)
    
    root_hash = _get_password_hash(password)

    try:
        with open(ROOT_PASSWORD_HASH_FILE, 'w', encoding='utf-8') as f:
            f.write(root_hash)
    except Exception as e:
        raise MappError('ROOT_PASSWORD_FILE_ERROR', f'Could not write root password file: {e}')

    print(':: root password set successfully')

def cmd_is_set():
    try:
        if os.path.getsize(ROOT_PASSWORD_HASH_FILE) > 0:
            print(':: root password is set')
            sys.exit(0)
        else:
            print(':: root password is not set')
            sys.exit(1)
    except FileNotFoundError:
        print(':: root password is not set')
        sys.exit(1)

def cmd_verify_pw():
    password = getpass('Enter root password: ')
    if _verify_root_password(password):
        print('Password verified: True')
        sys.exit(0)
    else:
        print('Password verified: False')
        sys.exit(1)

def main():
    description = 'Root password management for Mapp application.'
    parser = argparse.ArgumentParser(description=description)
    subparsers = parser.add_subparsers(dest='command', required=True)

    subparsers.add_parser('create-pw', help='Set the root password')
    subparsers.add_parser('is-set', help='Check if root password is set')
    subparsers.add_parser('verify-pw', help='Verify root password')

    args = parser.parse_args()

    match args.command:
        case 'create-pw':
            cmd_create_pw()
        case 'is-set':
            cmd_is_set()
        case 'verify-pw':
            cmd_verify_pw()
        case _:
            parser.print_help()
            sys.exit(2)

if __name__ == '__main__':
    main()
