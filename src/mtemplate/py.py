from mtemplate import MTemplateProject, MTemplateError
from mtemplate.html import *
from pathlib import Path
import os
from typing import Tuple
from pprint import pprint


class MTemplatePyProject(MTemplateProject):

    template_dir = Path(__file__).parent.parent.parent / 'templates/py'
    dist_dir = Path(__file__).parent.parent.parent / 'dist/py'

    model_prefixes = [
        str(template_dir / 'src/sample/sample_item'),
        str(template_dir / 'tests/sample')
    ]

    module_prefixes = [
        str(template_dir / 'src/sample')
    ]

    def init_template_vars(self):
        super().init_template_vars()
        self.spec['macro'].update({
            'py_example_fields': self.macro_py_example_fields,
            'py_random_fields': self.macro_py_random_fields,
            'py_verify_fields': self.macro_py_verify_fields,
            'py_field_list': self.macro_py_field_list,
        })

    def template_source_paths(self) -> dict[str, list[dict[str, str]]]:
        """
        return a tuple of two lists, the first list contains the paths of the app templates
        and the second list contains the paths of the module templates
        """
        paths = {
            'app': [],
            'module': [],
            'model': []
        }
        for root, _, files in os.walk(self.template_dir):
            if '__pycache__' in root:
                    continue
            
            if '.egg-info' in root:
                continue
            
            for name in files:
                if name == '.DS_Store':
                    continue
                
                rel_path = os.path.relpath(os.path.join(root, name), self.template_dir)
                rel_path = rel_path.replace('sample_item', '{model_name_snake_case}')
                rel_path = rel_path.replace('sample', '{module_name_snake_case}')
                template = {'src': os.path.join(root, name), 'rel': rel_path}

                if root in self.model_prefixes:
                    paths['model'].append(template)
                elif root in self.module_prefixes:
                    paths['module'].append(template)
                else:
                    paths['app'].append(template)

        self.template_paths = paths
        return paths
    
    def macro_py_example_fields(self, fields:dict, indent='\t') -> str:
        lines = []
        for name, field in fields.items():
            try:
                lines.append(f"{indent * 2}'{name}': '{field["examples"][0]}'")
            except (KeyError, IndexError):
                raise MTemplateError(f'field {name} does not have an example')  
        return ',\n'.join(lines)

    def macro_py_random_fields(self, fields:dict, indent='\t') -> str:
        lines = []
        for name, field in fields.items():
            field_type = 'enum' if 'enum' in field else field['type']
            try:
                lines.append(f"{indent * 2}'{name}': random_{field_type}()")
            except KeyError:
                raise MTemplateError(f'field {name} does not have a type')  
        return ',\n'.join(lines)

    def macro_py_verify_fields(self, fields:dict, indent='\t') -> str:
        lines = []
        for name, field in fields.items():
            field_type = 'enum' if 'enum' in field else field['type']
            try:
                raise NotImplementedError('this feature not implented yet')
                lines.append(f"{indent}raise NotImplementedError('macro_py_verify_" + field_type + "')")
            except KeyError:
                raise MTemplateError(f'field {name} does not have a type')
        return '\n'.join(lines)

    def macro_py_field_list(self, fields:dict) -> str:
        keys = [f"'{name}'" for name in fields.keys()]
        return '[' + ', '.join(keys) + ']'

    def render_templates(self, output_dir:str|Path=None):
        
        if output_dir is None:
            output_dir = self.dist_dir

        print(':: app')
        for template in self.template_paths['app']:
            app_output = output_dir / template['rel']

            print('\t', app_output)
            self.render_template({}, template['rel'], app_output)

        print(':: modules')
        for module in self.spec['modules'].values():
            print('\t', module['name']['lower_case'])
            
            for template in self.template_paths['module']:
                module_output = (output_dir / template['rel']).as_posix()
                module_output = module_output.format(module_name_snake_case=module['name']['snake_case'])

                print('\t\t', module_output)
                self.render_template({'module': module}, template['rel'], module_output)

            print('\n\t\t:: models')
            for model in module['models'].values():
                print('\t\t\t', model['name']['lower_case'])

                for template in self.template_paths['model']:
                    model_output = (output_dir / template['rel']).as_posix()
                    model_output = model_output.format(
                        module_name_snake_case=module['name']['snake_case'], 
                        model_name_snake_case=model['name']['snake_case']
                    )

                    print('\t\t\t\t', model_output)
                    self.render_template({'module': module, 'model': model}, template['rel'], model_output)

        print(':: done')


def render_py_templates(spec:dict, output_dir:str|Path=None, debug:bool=False):
    template_proj = MTemplatePyProject(spec, debug=debug)
    template_proj.extract_templates()
    template_proj.init_template_vars()
    template_proj.render_templates(output_dir)
