from mtemplate.html import extract_html_templates
from pathlib import Path
import os
from typing import Tuple


template_dir = Path(__file__).parent.parent.parent / 'templates/py'
# app_template_prefixes = [
#     str(template_dir),
#     str(template_dir / 'src/core')
# ]
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

            if root in model_prefixes:
                paths['model'].append(os.path.join(root, name))
            elif root in module_prefixes:
                paths['module'].append(os.path.join(root, name))
            else:
                paths['app'].append(os.path.join(root, name))
    
    return paths

def extract_py_templates():
    paths = py_template_source_paths()
    for key in paths.keys():
        print(f'py {key} templates:')
        for path in paths[key]:
            print(f'\t{path}')
    

def render_py_templates(spec:dict, output_dir:str|Path, debug:bool=False):
    extract_py_templates()
    extract_html_templates()