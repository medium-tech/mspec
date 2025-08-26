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

    project = spec['project']
    project['name'].update(generate_names(project['name']['lower_case']))

    for module in spec['modules'].values():
        module['name'].update(generate_names(module['name']['lower_case']))
        for model in module['models'].values():
            model['name'].update(generate_names(model['name']['lower_case']))
        
    return spec
