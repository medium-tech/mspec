from mtemplate import MTemplateProject, MTemplateError
from pathlib import Path


__all__ = ['MTemplateHTMLProject']


class MTemplateHTMLProject(MTemplateProject):

    template_dir = Path(__file__).parent.parent.parent / 'templates/html'
    dist_dir = Path(__file__).parent.parent.parent / 'dist/html'

    module_prefixes = [
        str(template_dir / 'srv/sample')
    ]

    model_prefixes = [
        str(template_dir / 'tests/sample'),
        str(template_dir / 'srv/sample/sample-item')
    ]

    def init_template_vars(self):
        super().init_template_vars()
        self.spec['macro'].update({
            'html_unittest_form': self.macro_html_unittest_form,
            'html_random_fields': self.macro_html_random_fields,
            'html_verify_fields': self.macro_html_verify_fields
        })

    def macro_html_unittest_form(self, fields:dict, indent='\t'):
        out = ''
        for name, field in fields.items():
            vars = {'field': name}
            try:
                vars['enum_choice'] = field['enum'][0]
                field_type = 'enum'
            except KeyError:
                field_type = field['type']

            try:
                out += self.spec['macro'][f'html_unittest_form_{field_type}'](vars) + '\n'
            except KeyError:
                raise MTemplateError(f'field {name} does not have type "{field_type}"')
        return out
    
    def macro_html_random_fields(self, fields:dict, indent='\t') -> str:
        lines = []
        for name, field in fields.items():
            field_type = 'enum' if 'enum' in field else field['type']
            try:
                lines.append(f"{indent * 2}'{name}': random{field_type.capitalize()}()")
            except KeyError:
                raise MTemplateError(f'field {name} does not have a type')  
        return ',\n'.join(lines)
    
    def macro_html_verify_fields(self, fields:dict, indent='\t') -> str:
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
                out += self.spec['macro'][f'html_verify_{field_type}'](vars) + '\n'
            except KeyError:
                raise MTemplateError(f'field {name} does not have type "{field_type}"')
        return out