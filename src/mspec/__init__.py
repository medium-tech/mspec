import os
import json
from pathlib import Path
import yaml
__all__ = [
    'sample_data_dir',
    'sample_browser2_spec_dir',
    'sample_lingo_script_spec_dir',
    'sample_generator_spec_dir',
    'dist_dir',
    'builtin_spec_files',
    'generate_names',
    'load_browser2_spec',
    'load_lingo_script_spec',
    'load_generator_spec'
]

sample_data_dir = Path(__file__).parent / 'data'
sample_browser2_spec_dir = sample_data_dir / 'lingo' / 'pages'
sample_lingo_script_spec_dir = sample_data_dir / 'lingo' / 'scripts'
sample_generator_spec_dir = sample_data_dir / 'generator'
dist_dir = Path(__file__).parent.parent.parent / 'dist'

def builtin_spec_files() -> list[str]:
    script_files = os.listdir(sample_lingo_script_spec_dir)
    return {
        'browser2': os.listdir(sample_browser2_spec_dir),
        'generator': os.listdir(sample_generator_spec_dir),
        'lingo_script': list(filter(lambda f: not f.endswith('_test_data.json'), script_files)),
        'lingo_script_test_data': list(filter(lambda f: f.endswith('_test_data.json'), script_files))
    }

def generate_names(lower_case:str) -> dict:
    name_split = lower_case.split(' ')
    pascal_case = ''.join([name.capitalize() for name in name_split])
    return {
        'snake_case': '_'.join(name_split),
        'pascal_case': pascal_case,
        'kebab_case': '-'.join(name_split),
        'camel_case': pascal_case[0].lower() + pascal_case[1:]
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
        with open(spec_file) as f:
            contents = json.load(f)
    except FileNotFoundError:
        _path = sample_browser2_spec_dir / spec_file
        if display:
            print(f'attempting to load spec file: {_path}')
        with open(_path) as f:
            contents = json.load(f)

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
        with open(spec_file) as f:
            contents = json.load(f)
        
    except FileNotFoundError:
        _path = sample_lingo_script_spec_dir / spec_file
        if display:
            print(f'attempting to load lingo script spec file: {_path}')
        with open(_path) as f:
            contents = json.load(f)

    try:
        if contents['lingo']['version'] != 'script-beta-1':
            raise ValueError(f'Unsupported lingo.version in lingo script spec file: {spec_file}, got: {contents["lingo"]["version"]}')

    except KeyError:
        raise ValueError(f'No lingo.version defined in lingo script spec file: {spec_file}')

    return contents

def load_generator_spec(spec_file:str) -> dict:
    """
    open and parse spec file into dict,
    first try to load from the path as provided,
    if not found, try searching for path in built in sample_spec_dir
    """
    try:
        with open(spec_file) as f:
            spec = yaml.load(f, Loader=yaml.FullLoader)

    except FileNotFoundError:
        _path = sample_generator_spec_dir / spec_file
        with open(_path) as f:
            spec = yaml.load(f, Loader=yaml.FullLoader)

    try:
        if spec['lingo']['version'] != 'generator-beta-1':
            raise ValueError(f'Unsupported lingo.version in spec file: {spec_file}, got: {spec["lingo"]["version"]}')
    except KeyError:
        raise ValueError(f'No lingo.version defined in spec file: {spec_file}')

    #
    # project
    #

    project = spec['project']
    for key, value in generate_names(project['name']['lower_case']).items():
        if key not in project['name']:
            project['name'][key] = value

    #
    # modules
    #

    for module in spec['modules'].values():
        for key, value in generate_names(module['name']['lower_case']).items():
            if key not in module['name']:
                module['name'][key] = value

        #
        # models
        #

        for model in module['models'].values():
            for key, value in generate_names(model['name']['lower_case']).items():
                if key not in model['name']:
                    model['name'][key] = value

            #
            # fields
            #

            try:
                fields:dict = model['fields']
            except KeyError:
                raise ValueError(f'No fields defined in model {module["name"]["lower_case"]}.{model["name"]["lower_case"]}')
            
            total_fields = len(fields)
            non_list_fields = []
            list_fields = []
            sorted_fields = []
            enum_fields = []

            for field_name, field in fields.items():
                try:
                    field['name']['lower_case']
                except KeyError:
                    raise ValueError(f'Must define name.lower_case for field {field_name} in model {module["name"]["lower_case"]}.{model["name"]["lower_case"]}')
                for key, value in generate_names(field['name']['lower_case']).items():
                    if key not in field['name']:
                        field['name'][key] = value

                try:
                    field['examples'][0]
                except (KeyError, IndexError):
                    raise ValueError(f'field {field_name} does not have an example in model {module["name"]["lower_case"]}.{model["name"]["lower_case"]}')

                sorted_fields.append(field)

                try:
                    field_type = field['type']
                except KeyError:
                    raise ValueError(f'No type defined for field {field_name} in model {module["name"]["lower_case"]}.{model["name"]["lower_case"]}')
                
                type_id = field_type
                
                if field_type == 'list':
                    try:
                        type_id += '_' + field['element_type']
                    except KeyError:
                        raise ValueError(f'No element_type defined for list field {field_name} in model {module["name"]["lower_case"]}.{model["name"]["lower_case"]}')
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
                raise ValueError(f'No fields defined in model {module["name"]["lower_case"]}.{model["name"]["lower_case"]}')
            
            # other model checks #
            
            if fields.get('user_id', None) is not None:
                if fields['user_id']['type'] != 'str':
                    raise ValueError(f'user_id is a reserved field, must be type str in model {model["name"]["lower_case"]}')
            
            if 'auth' in model:
                if 'require_login' not in model['auth']:
                    model['auth']['require_login'] = False
                if 'max_models_per_user' not in model['auth']:
                    model['auth']['max_models_per_user'] = None
            else:
                model['auth'] = {
                    'require_login': False,
                    'max_models_per_user': None
                }
        
    return spec
