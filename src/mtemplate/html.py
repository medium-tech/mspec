import os
from pathlib import Path
from typing import Tuple


template_dir = Path(__file__).parent.parent.parent / 'templates/html'

model_prefixes = [
    str(template_dir / 'tests/sample'),
    str(template_dir / 'srv/sample/sample-item')
]

module_prefixes = [
    str(template_dir / 'srv/sample')
]

def html_template_source_paths() -> Tuple[list[str], list[str]]:

    paths = {
        'app': [],
        'module': [],
        'model': []
    }

    for root, dirs, files in os.walk(template_dir):
        
        if 'node_modules' in root:
                continue
        
        if 'test-results' in root:
            continue

        if 'playwright-report' in root:
            continue
        
        for name in files:
            if name == '.DS_Store':
                continue

            if name == 'package-lock.json':
                continue

            if root in model_prefixes:
                paths['model'].append(os.path.join(root, name))
            elif root in module_prefixes:
                paths['module'].append(os.path.join(root, name))
            else:
                paths['app'].append(os.path.join(root, name))
    
    return paths

def display_html_templates():
    paths = html_template_source_paths()
    for key in paths.keys():
        print(f'html {key} templates:')
        for path in paths[key]:
            print(f'\t{path}')


def render_html_templates(spec:dict, output_dir:str|Path, debug:bool=False):
    display_html_templates()
