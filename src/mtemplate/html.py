from mtemplate import MTemplateProject, MTemplateError
from pathlib import Path


__all__ = ['MTemplateHTMLProject']


class MTemplateHTMLProject(MTemplateProject):

    template_dir = Path(__file__).parent.parent.parent / 'templates/html'
    dist_dir = Path(__file__).parent.parent.parent / 'dist/html'

    module_prefixes = [
        str(template_dir / 'srv/sample-module')
    ]

    model_prefixes = [
        str(template_dir / 'tests/sample-module'),
        str(template_dir / 'srv/sample-module/example-item')
    ]

    def init_template_vars(self):
        super().init_template_vars()
        self.spec['macro'].update({
            'html_unittest_form': self.macro_html_unittest_form,
            'html_random_fields': self.macro_html_random_fields,
            'html_verify_fields': self.macro_html_verify_fields,
            'html_from_input_tbody_fields': self.macro_html_from_input_tbody_fields,
            'html_to_input_tbody': self.macro_html_to_input_tbody,
            'html_to_display_tbody': self.macro_html_to_display_tbody,
            'html_to_table_row': self.macro_html_to_table_row,
            'html_list_table_headers': self.macro_html_list_table_headers,
            'html_field_list': self.macro_html_field_list,
        })

    def macro_html_list_table_headers(self, fields:dict, indent='\t') -> str:
        out = ''
        all_keys = ['id'] + list(fields.keys())
        for name in all_keys:
            vars = {'field': name}
            out += self.spec['macro'][f'html_list_table_header'](vars) + '\n'
        return out

    def macro_html_to_table_row(self, fields:dict, indent='\t') -> str:
        out = ''
        for name, field in fields.items():
            vars = {'field': name}
            field_type = field['type']

            try:
                out += self.spec['macro'][f'html_to_table_row_{field_type}'](vars) + '\n'
            except KeyError:
                raise MTemplateError(f'field {name} does not have type "{field_type}"')
        return out

    def macro_html_to_display_tbody(self, fields:dict, indent='\t') -> str:
        out = ''
        for name, field in fields.items():
            vars = {'field': name}
            field_type = field['type']

            try:
                out += self.spec['macro'][f'html_to_display_tbody_{field_type}'](vars) + '\n'
            except KeyError:
                raise MTemplateError(f'field {name} does not have type "{field_type}"')
        return out

    def macro_html_to_input_tbody(self, fields:dict, indent='\t') -> str:
        out = ''
        for name, field in fields.items():
            vars = {'field': name}
            field_type = 'enum' if 'enum' in field else field['type']

            try:
                out += self.spec['macro'][f'html_to_input_tbody_{field_type}'](vars) + '\n'
            except KeyError:
                raise MTemplateError(f'field {name} does not have type "{field_type}"')
        return out

    def macro_html_from_input_tbody_fields(self, fields:dict, indent='\t') -> str:
        out = ''
        for name, field in fields.items():
            vars = {'field': name}
            field_type = 'enum' if 'enum' in field else field['type']

            try:
                out += self.spec['macro'][f'html_from_input_tbody_{field_type}'](vars) + '\n'
            except KeyError:
                raise MTemplateError(f'field {name} does not have type "{field_type}"')
        return out

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

            if 'enum' in field:
                enum_values = [f"'{value}'" for value in field['enum']]
                vars['enum_value_list'] = '[' + ', '.join(enum_values) + ']'
                field_type = 'enum'

            elif field['type'] == 'list':

                if field['element_type'] == 'str':
                    js_element_type = 'string'
                elif field['element_type'] == 'bool':
                    js_element_type = 'boolean'
                elif field['element_type'] == 'int':
                    js_element_type = 'number'
                elif field['element_type'] == 'float':
                    js_element_type = 'number'
                else:
                    raise MTemplateError(f'field "{name}" has unsupported element_type "{field["element_type"]}"')
                
                vars['element_type'] = js_element_type
                field_type = 'list'

            else:
                field_type = field['type']

            try:
                out += self.spec['macro'][f'html_verify_{field_type}'](vars) + '\n'
            except KeyError:
                raise MTemplateError(f'field {name} does not have type "{field_type}"')
            
        return out
    
    def macro_html_field_list(self, fields:dict) -> str:
        all_keys = ['id'] + list(fields.keys())
        keys = [f"'{name}'" for name in all_keys]
        return '[' + ', '.join(keys) + ']'