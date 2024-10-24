from mtemplate import MTemplateProject, MTemplateError
from pathlib import Path


__all__ = ['MTemplateHTMLProject']


class MTemplatePyProject(MTemplateProject):

    template_dir = Path(__file__).parent.parent.parent / 'templates/py'
    dist_dir = Path(__file__).parent.parent.parent / 'dist/py'

    module_prefixes = [
        str(template_dir / 'src/sample')
    ]

    model_prefixes = [
        str(template_dir / 'src/sample/sample_item'),
        str(template_dir / 'tests/sample')
    ]

    def init_template_vars(self):
        super().init_template_vars()
        self.spec['macro'].update({
            'py_example_fields': self.macro_py_example_fields,
            'py_random_fields': self.macro_py_random_fields,
            'py_verify_fields': self.macro_py_verify_fields,
            'py_field_list': self.macro_py_field_list,
        })
    
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
        out = ''
        for name, field in fields.items():
            vars = {'field': name}
            try:
                enum_values = [f"'{value}'" for value in field['enum']]
                vars['enum_value_list'] = '[' + ', '.join(enum_values) + ']'
                field_type = 'enum'
            except KeyError:
                field_type = field['type']

            try:
                out += self.spec['macro'][f'py_verify_{field_type}'](vars) + '\n'
            except KeyError:
                raise MTemplateError(f'field {name} does not have a type')
        return out

    def macro_py_field_list(self, fields:dict) -> str:
        keys = [f"'{name}'" for name in fields.keys()]
        return '[' + ', '.join(keys) + ']'

