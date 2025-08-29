from mtemplate import MTemplateProject, MTemplateError
from pathlib import Path


__all__ = ['MTemplateBrowser1Project']


class MTemplateBrowser1Project(MTemplateProject):

    app_name = 'browser1'
    template_dir = Path(__file__).parent.parent.parent / 'templates' / app_name
    cache_dir = Path(__file__).parent / '.cache' / app_name

    prefixes = {
        'srv/template-module': 'module',

        'tests/template-module': 'model',
        'srv/template-module/single-model': 'model',

        'srv/template-module/multi-model': 'macro_only',
        'tests/template-module/multiModel': 'macro_only',
    }

    def macro_browser1_init_fields(self, fields:dict, indent='\t') -> str:
        out = ''
        for name, field in fields.items():
            vars = {'field': name}

            macro_name = f'browser1_init_{field["type"]}'

            if field['type'] == 'list':
                macro_name += f"_{field['element_type']}"

            if 'enum' in field:
                macro_name += '_enum'

            try:
                out += self.spec['macro'][macro_name](vars) + '\n'
            except KeyError:
                raise MTemplateError(f'field {name} does not have type "{macro_name}"')
            
        return out

    def macro_browser1_list_table_headers(self, fields:dict, indent='\t') -> str:
        out = ''
        all_keys = ['id'] + list(fields.keys())
        for name in all_keys:
            vars = {'field': name}
            out += self.spec['macro'][f'browser1_list_table_header'](vars) + '\n'
        return out

    def macro_browser1_to_table_row(self, fields:dict, indent='\t') -> str:
        out = ''
        for name, field in fields.items():
            vars = {'field': name}
            field_type = field['type']
            macro_name = f'browser1_to_table_row_{field_type}'

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

    def macro_browser1_to_display_tbody(self, fields:dict, indent='\t') -> str:
        out = ''
        for name, field in fields.items():
            vars = {'field': name}

            macro_name = f'browser1_to_display_tbody_{field["type"]}'

            try:
                macro_name += '_' + field['element_type']
            except KeyError:
                pass

            if 'enum' in field:
                macro_name += '_enum'

            out += self.spec['macro'][macro_name](vars) + '\n'
            
        return out

    def macro_browser1_to_input_tbody(self, fields:dict, indent='\t') -> str:
        out = ''
        for name, field in fields.items():
            vars = {'field': name}

            macro_name = f'browser1_to_input_tbody_{field["type"]}'

            try:
                macro_name += '_' + field['element_type']
            except KeyError:
                pass

            if 'enum' in field:
                macro_name += '_enum'

            out += self.spec['macro'][macro_name](vars) + '\n'
            
        return out

    def macro_browser1_from_input_tbody_fields(self, fields:dict, indent='\t') -> str:
        out = ''
        for name, field in fields.items():
            vars = {'field': name}

            macro_name = f'browser1_from_input_tbody_{field["type"]}'

            try:
                macro_name += '_' + field['element_type']
            except KeyError:
                pass

            if 'enum' in field:
                macro_name += '_enum'

            out += self.spec['macro'][macro_name](vars) + '\n'
            
        return out

    def macro_browser1_unittest_form(self, fields:dict, indent='\t'):
        out = ''
        for name, field in fields.items():
            vars = {'field': name}
            macro_name = f'browser1_unittest_form_{field["type"]}'

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
                raise MTemplateError(f'field {name} missing macro {macro_name} for type "{field["type"]}"') from e
        return out
    
    def macro_browser1_random_fields(self, fields:dict, indent='\t\t') -> str:
        lines = []
        for name, field in fields.items():
            custom_function = field.get('random', None)
            if custom_function:
                lines.append(f"{indent}{name}: {custom_function}(),")

            else:
                vars = {'field': name}
                macro_name = f'browser1_random_{field["type"]}'
                try:
                    macro_name += '_' + field['element_type']
                except KeyError:
                    pass

                if 'enum' in field:
                    macro_name += '_enum'

                lines.append(self.spec['macro'][macro_name](vars))

        return '\n'.join(lines)
    
    def macro_browser1_verify_fields(self, fields:dict, indent='\t') -> str:
        out = ''
        for name, field in fields.items():
            vars = {'field': name}

            macro_name = f'browser1_verify_{field["type"]}'

            try:
                macro_name += '_' + field['element_type']
            except KeyError:
                pass

            if 'enum' in field:
                macro_name += '_enum'

            out += self.spec['macro'][macro_name](vars) + '\n'
            
        return out
    
    def macro_browser1_field_list(self, fields:dict) -> str:
        all_keys = ['id'] + list(fields.keys())
        keys = [f"'{name}'" for name in all_keys]
        return '[' + ', '.join(keys) + ']'
    
    def macro_browser1_enum_definitions(self, fields:dict, indent='    ') -> str:
        out = ''
        for name, field in fields.items():
            if 'enum' not in field:
                continue

            out += self.spec['macro'][f'browser1_enum_definition_begin']({'field_name': name}) + '\n'

            for option in field['enum']:
                option_value = option.replace("'", "\'")
                out += self.spec['macro'][f'browser1_enum_definition_option']({'option': option_value}) + '\n'

            out += self.spec['macro'][f'browser1_enum_definition_end']({}) + '\n'

        return out
    
    def macro_browser1_example_fields(self, fields:dict, indent='\t\t\t') -> str:

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