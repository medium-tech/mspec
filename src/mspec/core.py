import os
import json

import yaml

from pathlib import Path

from mspec.util import generate_names


__all__ = [
    'SAMPLE_DATA_DIR',
    'SAMPLE_BROWSER2_SPEC_DIR',
    'SAMPLE_LINGO_SCRIPT_SPEC_DIR',
    'SAMPLE_GENERATOR_SPEC_DIR',
    'DIST_DIR',
    'builtin_spec_files',
    'load_json_or_yaml',
    'load_browser2_spec',
    'load_lingo_script_spec',
    'load_generator_spec',
    'init_generator_spec',
]

SAMPLE_DATA_DIR = Path(__file__).parent / 'data'
SAMPLE_BROWSER2_SPEC_DIR = SAMPLE_DATA_DIR / 'lingo' / 'pages'
SAMPLE_LINGO_SCRIPT_SPEC_DIR = SAMPLE_DATA_DIR / 'lingo' / 'scripts'
SAMPLE_GENERATOR_SPEC_DIR = SAMPLE_DATA_DIR / 'generator'
DIST_DIR = Path(__file__).parent.parent.parent / 'dist'

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
    script_files = os.listdir(SAMPLE_LINGO_SCRIPT_SPEC_DIR)
    return {
        'browser2': os.listdir(SAMPLE_BROWSER2_SPEC_DIR),
        'generator': os.listdir(SAMPLE_GENERATOR_SPEC_DIR),
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
        _path = SAMPLE_BROWSER2_SPEC_DIR / spec_file
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
        _path = SAMPLE_LINGO_SCRIPT_SPEC_DIR / spec_file
        if display:
            print(f'attempting to load lingo script spec file: {_path}')
        contents = load_json_or_yaml(_path)

    try:
        if contents['lingo']['version'] != 'script-beta-1':
            raise ValueError(f'Unsupported lingo.version in lingo script spec file: {spec_file}, got: {contents["lingo"]["version"]}')

    except KeyError:
        raise ValueError(f'No lingo.version defined in lingo script spec file: {spec_file}')

    return contents

def load_builtin_generator_modules() -> dict:
    built_path = SAMPLE_DATA_DIR / 'builtin.yaml'
    with open(built_path, 'r') as f:
        spec = yaml.load(f, Loader=yaml.FullLoader)

    if spec['lingo']['version'] != 'builtin-beta-1':
        raise ValueError(f'Unsupported builtin spec file version, got: {spec["lingo"]["version"]}')
    
    return spec

def load_generator_spec(spec_file:str, try_examples:bool=True) -> dict:
    """
    open and parse spec file into dict,
    first try to load from the path as provided,
    if not found and try_examples is True,
    try searching for path in built in sample_generator_spec_dir
    """
    try:
        contents = load_json_or_yaml(spec_file)

    except FileNotFoundError:
        if try_examples:
            _path = SAMPLE_GENERATOR_SPEC_DIR / spec_file
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


def init_generator_spec(spec:dict) -> dict:

    #
    # project
    #

    project = spec['project']
    for key, value in generate_names(project['name']['lower_case']).items():
        if key not in project['name']:
            project['name'][key] = value

    try:
        spec_modules:dict = spec['modules']
    except KeyError:
        raise ValueError('No modules defined in the spec file.')
    
    try:
        use_builtin_modules = project['use_builtin_modules']
    except Exception:
        project['use_builtin_modules'] = True
        use_builtin_modules = True
    
    if use_builtin_modules is True:
        try:
            builtin_modules = load_builtin_generator_modules()
        except Exception as e:
            raise ValueError(f'Failed to load builtin modules: {str(e)}')
        
        for module_name, module in builtin_modules['modules'].items():
            if module_name not in spec_modules:
                spec_modules[module_name] = module

    #
    # modules
    #

    for module in spec_modules.values():
        for key, value in generate_names(module['name']['lower_case']).items():
            if key not in module['name']:
                module['name'][key] = value

        module_snake = module['name']['snake_case']

        #
        # models
        #

        module_model_names = []
        module_op_names = []

        for model in module['models'].values():
            for key, value in generate_names(model['name']['lower_case']).items():
                if key not in model['name']:
                    model['name'][key] = value

                module_model_names.append(model['name'][key])

            if 'hidden' not in model:
                model['hidden'] = False

            model_snake = model['name']['snake_case']

            model_path = f'{module_snake}.{model_snake}'

            #
            # fields
            #

            try:
                fields:dict = model['fields']
            except KeyError:
                raise ValueError(f'No fields defined in model {model_path}')
            
            total_fields = len(fields)
            non_list_fields = []
            list_fields = []
            sorted_fields = []
            enum_fields = []

            for field_name, field in fields.items():
                try:
                    field['name']['lower_case']
                except KeyError:
                    raise ValueError(f'Must define name.lower_case for field {field_name} in model {model_path}')
                for key, value in generate_names(field['name']['lower_case']).items():
                    if key not in field['name']:
                        field['name'][key] = value

                try:
                    if not isinstance(field['required'], bool):
                        raise ValueError(f'field {field_name} in model {model_path} has invalid required value, must be bool')
                except KeyError:
                    field['required'] = True

                try:
                    field['examples'][0]
                except (KeyError, IndexError):
                    raise ValueError(f'field {field_name} does not have an example in model {model_path}')

                sorted_fields.append(field)

                try:
                    field_type = field['type']
                except KeyError:
                    raise ValueError(f'No type defined for field {field_name} in model {model_path}')
                
                type_id = field_type
                
                if field_type == 'list':
                    try:
                        type_id += '_' + field['element_type']
                    except KeyError:
                        raise ValueError(f'No element_type defined for list field {field_name} in model {model_path}')
                    list_fields.append(field)
                else:
                    non_list_fields.append(field)

                if 'enum' in field:
                    type_id += '_enum'
                    enum_fields.append(field)

                field['type_id'] = type_id

            model['non_list_fields'] = sorted(non_list_fields, key=lambda x: x['name']['snake_case'])
            model['list_fields'] = sorted(list_fields, key=lambda x: x['name']['snake_case'])
            model['enum_fields'] = sorted(enum_fields, key=lambda x: x['name']['snake_case'])
            model['sorted_fields'] = sorted(sorted_fields, key=lambda x: x['name']['snake_case'])
            model['total_fields'] = total_fields

            if total_fields == 0:
                raise ValueError(f'No fields defined in model {model_path}')
            
            # other model checks #
            user_id = fields.get('user_id', None)
            if user_id is not None:
                if user_id['type'] != 'foreign_key':
                    raise ValueError(f'user_id is a reserved field, must be type foreign_key in model {model_path}')
                try:
                    if user_id['references']['table'] != 'user':
                        raise ValueError(f'user_id is a reserved field, must reference user table in model {model_path}')
                    if user_id['references']['field'] != 'id':
                        raise ValueError(f'user_id is a reserved field, must reference id field in model {model_path}')
                except KeyError:
                    raise ValueError(f'user_id is a reserved field, must reference user.id in model {model_path}')
            
            if 'auth' in model:
                if use_builtin_modules is False:
                    raise ValueError(f'project.use_builtin_modules must be true to use auth in model {model_path}')
                if 'require_login' not in model['auth']:
                    model['auth']['require_login'] = False
                if 'max_models_per_user' not in model['auth']:
                    model['auth']['max_models_per_user'] = None
            else:
                model['auth'] = {
                    'require_login': False,
                    'max_models_per_user': None
                }
        
        #
        # ops
        #

        for op in module.get('ops', {}).values():

            for key, value in generate_names(op['name']['lower_case']).items():
                if key not in op['name']:
                    op['name'][key] = value

                module_op_names.append(op['name'][key])

            op_path = f'{module_snake}.{op["name"]["snake_case"]}'

            try:
                op_params = op['params']
            except KeyError:
                raise ValueError(f'No params defined in op {op["name"]["lower_case"]} in module {module_snake}')
            
            try:
                op_output = op['output']
            except KeyError:
                raise ValueError(f'No output defined in op {op["name"]["lower_case"]} in module {module_snake}')

            for param_name, param in op_params.items():
                for key, value in generate_names(param['name']['lower_case']).items():
                    if key not in param['name']:
                        param['name'][key] = value

                try:
                    if not isinstance(param['required'], bool):
                        raise ValueError(f'param {param_name} in op {op_path} has invalid required value, must be bool')
                except KeyError:
                    param['required'] = True

                try:
                    if param['secure_input']:
                        if not param['type'] != 'str':
                            raise ValueError(f'param {param_name} in op {op_path} must be string type to use secure_input')
                except KeyError:
                    param['secure_input'] = False
            
            for out_name, out_field in op_output.items():
                for key, value in generate_names(out_field['name']['lower_case']).items():
                    if key not in out_field['name']:
                        out_field['name'][key] = value

                try:
                    if not isinstance(out_field['required'], bool):
                        raise ValueError(f'output field {out_name} in op {op_path} has invalid required value, must be bool')
                except KeyError:
                    out_field['required'] = True

        # check for duplicate names #

        duplicate_names = set(module_model_names) & set(module_op_names)
        num_dupe_names = len(duplicate_names)
        if num_dupe_names > 0:
            raise ValueError(f'{num_dupe_names} duplicate model and op names in module {module_snake}: {duplicate_names}')

    return spec