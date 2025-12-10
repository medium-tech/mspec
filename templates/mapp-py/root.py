#!/usr/bin/env python3
import argparse
import dotenv
from getpass import getpass

dotenv.load_dotenv(dotenv_path='.env', override=True)

# import after loading env vars so that MAPP_APP_PATH is set correctly
from mapp.auth import _create_root_password_hash

description = 'Run this script to interactively set the root password for the Mapp application.'
parser = argparse.ArgumentParser(description=description)
args = parser.parse_args()

password = getpass('Enter new root password: ')
confirm_password = getpass('Confirm new root password: ')

_create_root_password_hash(password, confirm_password)
print(':: Root password set successfully ::')
