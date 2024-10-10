from mtemplate.html import extract_html_templates
from pathlib import Path
import os
from typing import Tuple


template_dir = Path(__file__).parent.parent.parent / 'templates/py'
app_template_prefixes = [
    str(template_dir),
    str(template_dir / 'src/core')
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

        is_app_dir = root in app_template_prefixes
        
        for name in files:
            if name == '.DS_Store':
                continue

            if is_app_dir:
                paths['app'].append(os.path.join(root, name))
            else:
                paths['module'].append(os.path.join(root, name))
    
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