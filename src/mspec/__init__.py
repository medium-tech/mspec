from pathlib import Path
import yaml

__all__ = ['spec', 'sample_spec_dir', 'dist_dir']

sample_spec_dir = Path(__file__).parent / 'data'
dist_dir = Path(__file__).parent.parent.parent / 'dist'

def generate_names(lower_case:str) -> dict:
    name_split = lower_case.split(' ')
    pascal_case = ''.join([name.capitalize() for name in name_split])
    return {
        'snake_case': '_'.join(name_split),
        'pascal_case': pascal_case,
        'kebab_case': '-'.join(name_split),
        'camel_case': pascal_case[0].lower() + pascal_case[1:]
    }

def load_spec(spec_file:str) -> dict:
    """
    open and parse spec file into dict,
    first try to load from the path as provided,
    if not found, try searching for path in built in sample_spec_dir
    """
    try:
        print(f'attempting to load spec file: {spec_file}')
        with open(spec_file) as f:
            spec = yaml.load(f, Loader=yaml.FullLoader)
        print(f'\tloaded.')

    except FileNotFoundError:
        _path = sample_spec_dir / spec_file
        print(f'attempting to load spec file: {_path}')
        with open(_path) as f:
            spec = yaml.load(f, Loader=yaml.FullLoader)
        print(f'\tloaded.')

    #
    # project
    #

    project = spec['project']
    project['name'].update(generate_names(project['name']['lower_case']))

    #
    # modules
    #

    for module in spec['modules'].values():
        module['name'].update(generate_names(module['name']['lower_case']))

        #
        # models
        #

        for model in module['models'].values():
            model['name'].update(generate_names(model['name']['lower_case']))

            #
            # fields
            #

            try:
                fields = model['fields']
            except KeyError:
                raise ValueError(f'No fields defined in model {module["name"]["lower_case"]}.{model["name"]["lower_case"]}')
            
            total_fields = len(fields)
            non_list_fields = []
            list_fields = []
            sorted_fields = []
            enum_fields = []

            for field_name, field in fields.items():
                if 'name' not in field:
                    breakpoint()
                field['name'].update(generate_names(field['name']['lower_case']))

                entry = (field_name, field)     # storing this as a tuple is from before the name
                sorted_fields.append(entry)     # generation was added, could probably be simplified

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
                    list_fields.append(entry)
                else:
                    non_list_fields.append(entry)

                if 'enum' in field:
                    type_id += '_enum'
                    enum_fields.append(entry)

                field['type_id'] = type_id

            model['non_list_fields'] = sorted(non_list_fields, key=lambda x: x[0])
            model['list_fields'] = sorted(list_fields, key=lambda x: x[0])
            model['enum_fields'] = sorted(enum_fields, key=lambda x: x[0])
            model['sorted_fields'] = sorted(sorted_fields, key=lambda x: x[0])
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
