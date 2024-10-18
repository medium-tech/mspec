from mtemplate import MTemplateProject
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

    

def render_py_templates(spec:dict, output_dir:str|Path=None, debug:bool=False):
    template_proj = MTemplateProject(spec, debug=debug)

    if output_dir is None:
        output_dir = dist_dir
        
    py = py_template_source_paths()

    print(':: app')
    for template in py['app']:
        app_output = output_dir / template['rel']

        print('\t', app_output)
        template_proj.render_template({}, template['src'], app_output)

    print(':: modules')
    for module in spec['modules'].values():
        print('\t', module['name']['lower_case'])
        
        for template in py['module']:
            module_output = (output_dir / template['rel']).as_posix()
            module_output = module_output.format(module_name_snake_case=module['name']['snake_case'])

            print('\t\t', module_output)
            template_proj.render_template({'module': module}, template['src'], module_output)

        print('\n\t\t:: models')
        for model in module['models'].values():
            print('\t\t\t', model['name']['lower_case'])

            for template in py['model']:
                model_output = (output_dir / template['rel']).as_posix()
                model_output = model_output.format(
                    module_name_snake_case=module['name']['snake_case'], 
                    model_name_snake_case=model['name']['snake_case']
                )

                print('\t\t\t\t', model_output)
                template_proj.render_template({'module': module, 'model': model}, template['src'], model_output)

    print(':: done')