from mtemplate import MTemplateProject, MTemplateError
from pathlib import Path


__all__ = ['MTemplateHTMLProject']


class MTemplateHTMLProject(MTemplateProject):

    app_name = 'html'

    template_dir = Path(__file__).parent.parent.parent / 'templates/html'

    module_prefixes = [
        str(template_dir / 'srv/test-module')
    ]

    model_prefixes = [
        str(template_dir / 'tests/test-module'),
        str(template_dir / 'srv/test-module/test-model')
    ]

    def init_template_vars(self):
        super().init_template_vars()
        self.spec['macro'].update({
            'html_init_fields': self.macro_html_init_fields,
            'html_unittest_form': self.macro_html_unittest_form,
            'html_random_fields': self.macro_html_random_fields,
            'html_verify_fields': self.macro_html_verify_fields,
            'html_from_input_tbody_fields': self.macro_html_from_input_tbody_fields,
            'html_to_input_tbody': self.macro_html_to_input_tbody,
            'html_to_display_tbody': self.macro_html_to_display_tbody,
            'html_to_table_row': self.macro_html_to_table_row,
            'html_list_table_headers': self.macro_html_list_table_headers,
            'html_field_list': self.macro_html_field_list,
            'html_enum_definitions': self.macro_html_enum_definitions,
            'html_example_fields': self.macro_html_example_fields,
        })

    def macro_html_init_fields(self, fields:dict, indent='\t') -> str:
        out = ''
        for name, field in fields.items():
            vars = {'field': name}

            macro_name = f'html_init_{field["type"]}'

            if field['type'] == 'list':
                macro_name += f"_{field['element_type']}"

            if 'enum' in field:
                macro_name += '_enum'

            try:
                out += self.spec['macro'][macro_name](vars) + '\n'
            except KeyError:
                raise MTemplateError(f'field {name} does not have type "{macro_name}"')
            
        return out

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
            macro_name = f'html_to_table_row_{field_type}'

            try:
                macro_name += '_' + field['element_type']
            except KeyError:
                pass

            if 'enum' in field:
                macro_name += '_enum'

            try:
                out += self.spec['macro'][macro_name](vars) + '\n'
            except KeyError:
                raise MTemplateError(f'field {name} does not have type "{field_type}"')
        return out

    def macro_html_to_display_tbody(self, fields:dict, indent='\t') -> str:
        out = ''
        for name, field in fields.items():
            vars = {'field': name}

            macro_name = f'html_to_display_tbody_{field["type"]}'

            try:
                macro_name += '_' + field['element_type']
            except KeyError:
                pass

            if 'enum' in field:
                macro_name += '_enum'

            out += self.spec['macro'][macro_name](vars) + '\n'
            
        return out

    def macro_html_to_input_tbody(self, fields:dict, indent='\t') -> str:
        out = ''
        for name, field in fields.items():
            vars = {'field': name}

            macro_name = f'html_to_input_tbody_{field["type"]}'

            try:
                macro_name += '_' + field['element_type']
            except KeyError:
                pass

            if 'enum' in field:
                macro_name += '_enum'

            out += self.spec['macro'][macro_name](vars) + '\n'
            
        return out

    def macro_html_from_input_tbody_fields(self, fields:dict, indent='\t') -> str:
        out = ''
        for name, field in fields.items():
            vars = {'field': name}

            macro_name = f'html_from_input_tbody_{field["type"]}'

            try:
                macro_name += '_' + field['element_type']
            except KeyError:
                pass

            if 'enum' in field:
                macro_name += '_enum'

            out += self.spec['macro'][macro_name](vars) + '\n'
            
        return out

    def macro_html_unittest_form(self, fields:dict, indent='\t'):
        out = ''
        for name, field in fields.items():
            vars = {'field': name}
            macro_name = f'html_unittest_form_{field["type"]}'

            if field['type'] == 'list':

                # list fields #

                macro_name += '_' + field['element_type']

                if field['element_type'] == 'str':
                    if 'enum' in field:
                        macro_name += '_enum'
                        vars['list_element_1'] = field['enum'][0]
                        vars['list_element_2'] = field['enum'][1]
                    else:
                        vars['list_element_1'] = 'grass'
                        vars['list_element_2'] = 'trees'

                elif field['element_type'] == 'bool':
                    vars['list_element_1'] = 'true'
                    vars['list_element_2'] = 'false'
                elif field['element_type'] == 'int':
                    vars['list_element_1'] = '66'
                    vars['list_element_2'] = '81'
                elif field['element_type'] == 'float':
                    vars['list_element_1'] = '4.9'
                    vars['list_element_2'] = '8.1128'
                elif field['element_type'] == 'datetime':
                    vars['list_element_1'] = '1998-06-04T04:35'
                    vars['list_element_2'] = '2023-01-01T00:00'
                else:
                    raise MTemplateError(f'field "{name}" has unsupported element_type "{field["element_type"]}"')
                
            else:

                # non-list fields #
                
                if field['type'] == 'str':
                    if 'enum' in field:
                        macro_name += '_enum'
                        vars['value'] = field['enum'][0]
                    else:
                        vars['value'] = 'one'

                elif field['type'] == 'bool':
                    vars['value'] = 'true'
                elif field['type'] == 'int':
                    vars['value'] = '1'
                elif field['type'] == 'float':
                    vars['value'] = '1.4'
                elif field['type'] == 'datetime':
                    vars['value'] = '1998-06-04T04:35'
                else:
                    raise MTemplateError(f'field "{name}" has unsupported type "{field["type"]}"')

            try:
                out += self.spec['macro'][macro_name](vars) + '\n'
            except KeyError as e:
                raise MTemplateError(f'field {name} does not have type "{field["type"]}"') from e
        return out
    
    def macro_html_random_fields(self, fields:dict, indent='\t\t') -> str:
        lines = []
        for name, field in fields.items():
            custom_function = field.get('random', None)
            if custom_function:
                lines.append(f"{indent}{name}: {custom_function}(),")

            else:
                vars = {'field': name}
                macro_name = f'html_random_{field["type"]}'
                try:
                    macro_name += '_' + field['element_type']
                except KeyError:
                    pass

                if 'enum' in field:
                    macro_name += '_enum'

                lines.append(self.spec['macro'][macro_name](vars))

        return '\n'.join(lines)
    
    def macro_html_verify_fields(self, fields:dict, indent='\t') -> str:
        out = ''
        for name, field in fields.items():
            vars = {'field': name}

            macro_name = f'html_verify_{field["type"]}'

            try:
                macro_name += '_' + field['element_type']
            except KeyError:
                pass

            if 'enum' in field:
                macro_name += '_enum'

            out += self.spec['macro'][macro_name](vars) + '\n'
            
        return out
    
    def macro_html_field_list(self, fields:dict) -> str:
        all_keys = ['id'] + list(fields.keys())
        keys = [f"'{name}'" for name in all_keys]
        return '[' + ', '.join(keys) + ']'
    
    def macro_html_enum_definitions(self, fields:dict, indent='    ') -> str:
        out = ''
        for name, field in fields.items():
            if 'enum' not in field:
                continue

            out += self.spec['macro'][f'html_enum_definition_begin']({'field_name': name}) + '\n'

            for option in field['enum']:
                option_value = option.replace("'", "\'")
                out += self.spec['macro'][f'html_enum_definition_option']({'option': option_value}) + '\n'

            out += self.spec['macro'][f'html_enum_definition_end']({}) + '\n'

        return out
    
    def macro_html_example_fields(self, fields:dict, indent='\t\t\t') -> str:

        def convert_val(value, field_type):
            if field_type in ['bool', 'int', 'float']:
                return str(value).lower()
            elif field_type == 'str':
                return f"'{value.replace("'", "\'")}'"
            elif field_type == 'datetime':
                return f"new Date('{value}')"   # ex: 2023-01-01T00:00:00Z

        lines = []

        for name, field in fields.items():
            try:
                example = field["examples"][0]
            except (KeyError, IndexError):
                raise MTemplateError(f'field {name} does not have an example')
            
            if field['type'] == 'list':
                values = []
                for item in example:
                    values.append(convert_val(item, field['element_type']))
                value = '[' + ', '.join(values) + ']'

            else:
                value = convert_val(example, field['type'])

            lines.append(f"{indent}{name}: {value}")

        return ',\n'.join(lines)