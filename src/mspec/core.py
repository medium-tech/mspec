import os
import json

from pathlib import Path

from mspec.generator import init_generator_spec

import yaml

__all__ = [
    'sample_data_dir',
    'sample_browser2_spec_dir',
    'sample_lingo_script_spec_dir',
    'sample_generator_spec_dir',
    'dist_dir',
    'builtin_spec_files',
    'load_browser2_spec',
    'load_lingo_script_spec',
    'load_generator_spec'
]

sample_data_dir = Path(__file__).parent / 'data'
sample_browser2_spec_dir = sample_data_dir / 'lingo' / 'pages'
sample_lingo_script_spec_dir = sample_data_dir / 'lingo' / 'scripts'
sample_generator_spec_dir = sample_data_dir / 'generator'
dist_dir = Path(__file__).parent.parent.parent / 'dist'

def load_json_or_yaml(file_path:Path|str) -> dict:
    """
    load json or yaml file based on file extension
    """
    str_path = str(file_path)
    if str_path.endswith('.json'):
        with open(str_path) as f:
            return json.load(f)
    elif str_path.endswith(('.yml', '.yaml')):
        with open(str_path) as f:
            return yaml.load(f, Loader=yaml.FullLoader)
    else:
        raise ValueError(f'Unsupported file extension for file: {file_path}')

def builtin_spec_files() -> list[str]:
    script_files = os.listdir(sample_lingo_script_spec_dir)
    return {
        'browser2': os.listdir(sample_browser2_spec_dir),
        'generator': os.listdir(sample_generator_spec_dir),
        'lingo_script': list(filter(lambda f: not f.endswith('_test_data.json'), script_files)),
        'lingo_script_test_data': list(filter(lambda f: f.endswith('_test_data.json'), script_files))
    }

def load_browser2_spec(spec_file:str, display:bool=False) -> dict:
    """
    open and parse spec file into dict,
    first try to load from the path as provided,
    if not found, try searching for path in built in sample_spec_dir
    """

    try:
        if display:
            print(f'attempting to load spec file: {spec_file}')
        contents = load_json_or_yaml(spec_file)
    except FileNotFoundError:
        _path = sample_browser2_spec_dir / spec_file
        if display:
            print(f'attempting to load spec file: {_path}')
        contents = load_json_or_yaml(_path)

    try:
        if contents['lingo']['version'] != 'page-beta-1':
            raise ValueError(f'Unsupported lingo.version in spec file: {spec_file}, got: {contents["lingo"]["version"]}')
        
    except KeyError:
        raise ValueError(f'No lingo.version defined in spec file: {spec_file}')
    
    return contents

def load_lingo_script_spec(spec_file:str, display:bool=False) -> dict:
    """
    open and parse lingo script spec file into dict,
    first try to load from the path as provided,
    if not found, try searching for path in built in sample_lingo_script_spec_dir
    """

    try:
        if display:
            print(f'attempting to load lingo script spec file: {spec_file}')
        contents = load_json_or_yaml(spec_file)
        
    except FileNotFoundError:
        _path = sample_lingo_script_spec_dir / spec_file
        if display:
            print(f'attempting to load lingo script spec file: {_path}')
        contents = load_json_or_yaml(_path)

    try:
        if contents['lingo']['version'] != 'script-beta-1':
            raise ValueError(f'Unsupported lingo.version in lingo script spec file: {spec_file}, got: {contents["lingo"]["version"]}')

    except KeyError:
        raise ValueError(f'No lingo.version defined in lingo script spec file: {spec_file}')

    return contents

def load_generator_spec(spec_file:str, try_builtin:bool=True) -> dict:
    """
    open and parse spec file into dict,
    first try to load from the path as provided,
    if not found, try searching for path in built in sample_spec_dir
    """
    try:
        contents = load_json_or_yaml(spec_file)

    except FileNotFoundError:
        if try_builtin:
            _path = sample_generator_spec_dir / spec_file
            contents = load_json_or_yaml(_path)
        else:
            raise

    try:
        if contents['lingo']['version'] != 'generator-beta-1':
            raise ValueError(f'Unsupported lingo.version in spec file: {spec_file}, got: {contents["lingo"]["version"]}')
    except KeyError:
        raise ValueError(f'No lingo.version defined in spec file: {spec_file}')

    return init_generator_spec(contents)

load_mapp_spec = load_generator_spec  # alias for backward compatibility