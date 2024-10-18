from pathlib import Path
import yaml

__all__ = ['spec', 'spec_dir', 'dist_dir']

spec_dir = Path(__file__).parent.parent.parent / 'spec'
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
    load all yaml files in the spec directory and return them as a dictionary,
    each top level key is the name of the file without extension 
    and its value is the parsed yaml as a dictionary
    """
    try:
        with open(spec_file) as f:
            spec = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError:
        with open(spec_dir / spec_file) as f:
            spec = yaml.load(f, Loader=yaml.FullLoader)

    project = spec['project']
    project['name'].update(generate_names(project['name']['lower_case']))

    for module in spec['modules'].values():
        module['name'].update(generate_names(module['name']['lower_case']))
        for model in module['models'].values():
            model['name'].update(generate_names(model['name']['lower_case']))
        
    return spec
