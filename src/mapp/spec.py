import os

from mspec.core import load_generator_spec
from mapp.errors import MappError


def load_spec():
    try:
        spec_path = os.environ['MAPP_SPEC_FILE']
    except KeyError:
        raise MappError('MAPP_SPEC_FILE environment variable not set.')
    
    try:
        load_generator_spec(spec_path)
    except FileNotFoundError:
        raise MappError('SPEC_FILE_NOT_FOUND', f'Spec file not found: {spec_path}')