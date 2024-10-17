from mtemplate.html import *
from pathlib import Path
import os
from typing import Tuple
from pprint import pprint


template_dir = Path(__file__).parent.parent.parent / 'templates/py'
dist_dir = Path(__file__).parent.parent.parent / 'dist/py'

model_prefixes = [
    str(template_dir / 'src/sample/sample_item'),
    str(template_dir / 'tests/sample')
]

module_prefixes = [
    str(template_dir / 'src/sample')
]

def py_template_source_paths() -> dict:
    """
    return a tuple of two lists, the first list contains the paths of the app templates
    and the second list contains the paths of the module templates
    """
    paths = {
        'app': [],
        'module': [],
        'model': []
    }
    for root, dirs, files in os.walk(template_dir):
        if '__pycache__' in root:
                continue
        
        if '.egg-info' in root:
            continue
        
        for name in files:
            if name == '.DS_Store':
                continue
            
            rel_path = os.path.relpath(os.path.join(root, name), template_dir)
            rel_path = rel_path.replace('sample_item', '{model_name_snake_case}')
            rel_path = rel_path.replace('sample', '{module_name_snake_case}')
            template = {'src': os.path.join(root, name), 'rel': rel_path}

            if root in model_prefixes:
                paths['model'].append(template)
            elif root in module_prefixes:
                paths['module'].append(template)
            else:
                paths['app'].append(template)
    
    return paths

def display_py_templates():
    paths = py_template_source_paths()
    for key in paths.keys():
        print(f'py {key} templates:')
        for path in paths[key]:
            print(f'\t{path}')
    

def render_py_templates(spec:dict, output_dir:str|Path=None, debug:bool=False):
    if output_dir is None:
        output_dir = dist_dir
        
    py = py_template_source_paths()
    project = spec['test-gen']['project']

    print('app')

    for template in py['app']:
        output = output_dir / template['rel']
        print('\t', output)

    print('modules')

    for module in project['modules'].values():

        print('\t', module['name']['lower_case'])
        
        for template in py['module']:
            output = output_dir / template['rel']
            print('\t\t', output)

        print('\t\tmodels')

        for model in module['models'].values():
            print('\t\t\t', model['name']['lower_case'])

            for template in py['model']:
                output = (output_dir / template['rel']).as_posix()
                output = output.format(
                    module_name_snake_case=module['name']['lower_case'], 
                    model_name_snake_case=model['name']['lower_case']
                )
                print('\t\t\t\t', output)
