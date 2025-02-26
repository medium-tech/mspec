from mtemplate import MTemplateProject, MTemplateError, iso_format_string
from pathlib import Path
from datetime import datetime
from copy import deepcopy


__all__ = ['MTemplateHTMLProject']


class MTemplatePyProject(MTemplateProject):

    template_dir = Path(__file__).parent.parent.parent / 'templates/py'
    dist_dir = Path(__file__).parent.parent.parent / 'dist/py'

    module_prefixes = [
        str(template_dir / 'src/sample_module')
    ]

    model_prefixes = [
        str(template_dir / 'src/sample_module/example_item'),
        str(template_dir / 'tests/sample_module')
    ]

    def init_template_vars(self):
        super().init_template_vars()
        self.spec['macro'].update({
            'py_example_fields': self.macro_py_example_fields,
            'py_random_fields': self.macro_py_random_fields,
            'py_verify_fields': self.macro_py_verify_fields,
            'py_field_list': self.macro_py_field_list,
            'py_field_definitions': self.macro_py_field_definitions,
        })
    
    def macro_py_example_fields(self, fields:dict, indent='\t') -> str:
        lines = []

        for name, field in fields.items():
            try:
                example = field["examples"][0]
            except (KeyError, IndexError):
                raise MTemplateError(f'field {name} does not have an example')

            if field['type'] in ['bool', 'int', 'float']:
                value = str(example)
            elif field['type'] == 'str':
                value = f"'{example}'"
            elif field['type'] == 'list':
                item_display = lambda i: f"'{i}'" if isinstance(i, str) else str(i)
                value = '[' + ', '.join([item_display(item) for item in example]) + ']'
            elif field['type'] == 'datetime':
                value = f"datetime.strptime('{example}', '{iso_format_string}')"
            else:
                raise MTemplateError(f'field "{name}" has unsupported type "{field["type"]}"')

            lines.append(f"{indent * 2}'{name}': {value}")

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
            vars = {'field': deepcopy(field)}
            vars['field']['name'] = name

            if 'enum' in field:
                enum_values = [f"'{value}'" for value in field['enum']]
                vars['enum_value_list'] = '[' + ', '.join(enum_values) + ']'
                field_type = 'str_enum'
            else:
                field_type = field['type']

            try:
                out += self.spec['macro'][f'py_verify_{field_type}'](vars) + '\n'
            except KeyError:
                raise MTemplateError(f'field {name} does not have a type')
        return out

    def macro_py_field_list(self, fields:dict) -> str:
        all_keys = ['id'] + list(fields.keys())
        keys = [f"'{name}'" for name in all_keys]
        return '[' + ', '.join(keys) + ']'

    def macro_py_field_definitions(self, fields:dict, indent='\t') -> str:
        out = ''
        for name, field in fields.items():
            if field['type'] == 'list':
                type_def = f'list[' + field['element_type'] + ']'
            else:
                type_def = field['type']
            out += f'{indent}{name}: {type_def}\n'
        return out