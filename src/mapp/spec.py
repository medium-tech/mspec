import os

from mspec.core import load_generator_spec
from mapp.errors import MappError


def load_spec_from_env():
    spec_path = os.environ.get('MAPP_SPEC_FILE', 'template-app.yaml')
    
    try:
        return load_generator_spec(spec_path)
    except FileNotFoundError:
        raise MappError('SPEC_FILE_NOT_FOUND', f'Spec file not found: {spec_path}')