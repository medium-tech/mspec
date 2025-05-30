from mtemplate import MTemplateProject, MTemplateError, iso_format_string
from pathlib import Path
from datetime import datetime
from copy import deepcopy


__all__ = ['MTemplatePyProject']


class MTemplatePyProject(MTemplateProject):

    app_name = 'py'

    template_dir = Path(__file__).parent.parent.parent / 'templates/py'

    module_prefixes = [
        str(template_dir / 'src/test_module'),
    ]

    model_prefixes = [
        str(template_dir / 'src/test_module/test_model'),
        str(template_dir / 'tests/test_module')
    ]
    
    def init_template_vars(self):
        super().init_template_vars()
        self.spec['macro'].update({
            'py_db_create': self.macro_py_db_create,
            'py_db_read': self.macro_py_db_read,
            'py_db_update': self.macro_py_db_update,
            'py_db_delete': self.macro_py_db_delete,
            'py_db_list_lists': self.macro_py_db_list_lists,
            'py_sql_convert': self.macro_py_sql_convert,
            'py_create_tables': self.macro_py_create_tables,
            'py_test_crud_delete': self.macro_py_test_crud_delete,
            'py_post_init': self.macro_py_post_init,
            'py_example_fields': self.macro_py_example_fields,
            'py_random_fields': self.macro_py_random_fields,
            'py_verify_fields': self.macro_py_verify_fields,
            'py_field_list': self.macro_py_field_list,
            'py_field_definitions': self.macro_py_field_definitions,
            'py_enum_definitions': self.macro_py_enum_definitions,
        })

    def macro_py_db_create(self, model:dict, indent='\t\t') -> str:
        out = ''

        list_fields = []
        non_list_fields = []
        num_non_list_fields = 0

        for name, field in model['fields'].items():
            if field['type'] == 'list':
                list_fields.append(name)
            else:
                non_list_fields.append(name)
                num_non_list_fields += 1

        # non list fields #
        
        non_list_fields.sort()

        fields_py = ''
        for field_name in non_list_fields:
            if model['fields'][field_name]['type'] == 'datetime':
                fields_py += f"obj.{field_name}.isoformat(), "
            else:
                fields_py += f"obj.{field_name}, "

        if num_non_list_fields == 0:
            fields_sql = ''
            sql_values = 'DEFAULT VALUES'
        else:
            fields_sql = '(' + ', '.join([f"'{name}'" for name in non_list_fields]) + ')'

            question_marks = ', '.join(['?'] * num_non_list_fields)
            sql_values = f'VALUES({question_marks})'

        create_vars = {
            'model_name_snake_case': model['name']['snake_case'],
            'fields_sql': fields_sql,
            'sql_values': sql_values,
            'fields_py': fields_py.strip()
        }

        out += self.spec['macro']['py_sql_create'](create_vars) + '\n'

        # list fields #

        list_fields.sort()

        for field_name in list_fields:
            list_vars = {
                'model_name_snake_case': model['name']['snake_case'],
                'field_name': field_name,
            }
            macro_name = 'py_sql_create_list_' + model['fields'][field_name]['element_type']
            if 'enum' in model['fields'][field_name]:
                macro_name += '_enum'
            out += self.spec['macro'][macro_name](list_vars) + '\n'

        return out

    def macro_py_db_read(self, model:dict, indent='\t\t') -> str:
        read_vars = {'model_name_snake_case': model['name']['snake_case']}
        out = self.spec['macro']['py_sql_read'](read_vars) + '\n'

        for name, field in model['fields'].items():
            if field['type'] == 'list':
                read_list_vars = {
                    'model_name_snake_case': model['name']['snake_case'],
                    'field_name': name
                }
                macro_name = 'py_sql_read_list_' + field['element_type']
                if 'enum' in field:
                    macro_name += '_enum'
                out += self.spec['macro'][macro_name](read_list_vars) + '\n'

        return out
    
    def macro_py_db_update(self, model:dict, indent='\t\t') -> str:
        fields_sql = []
        fields_py = []
        list_updates = ''

        for field_name in sorted(model['fields'].keys()):
            field = model['fields'][field_name]
            if field['type'] == 'list':
                list_vars = {
                    'model_name_snake_case': model['name']['snake_case'],
                    'field_name': field_name,
                }

                macro_name = 'py_sql_update_list_' + field['element_type']
                if 'enum' in field:
                    macro_name += '_enum'

                list_updates += self.spec['macro'][macro_name](list_vars) + '\n'

            elif field['type'] == 'datetime':
                fields_sql.append(f"'{field_name}'=?")
                fields_py.append(f"obj.{field_name}.isoformat()")
            else:
                fields_sql.append(f"'{field_name}'=?")
                fields_py.append(f"obj.{field_name}")
        
        vars = {
            'model_name_snake_case': model['name']['snake_case'],
            'fields_sql': ', '.join(fields_sql),
            'fields_py': ', '.join(fields_py),
        }

        if len(fields_py) > 0:
            out = self.spec['macro']['py_sql_update'](vars)
        else:
            out = ''

        out += '\n' + list_updates
        return out

    def macro_py_db_delete(self, model:dict, indent='\t\t') -> str:
        vars = {'model_name_snake_case': model['name']['snake_case']}
        out = self.spec['macro']['py_sql_delete'](vars) + '\n'

        for name, field in model['fields'].items():
            if field['type'] == 'list':
                list_vars = {
                    'model_name_snake_case': model['name']['snake_case'],
                    'field_name': name,
                }
                out += self.spec['macro']['py_sql_delete_list'](list_vars) + '\n'

        return out

    def macro_py_db_list_lists(self, model:dict, indent='\t\t') -> str:
        out = ''
        for name, field in model['fields'].items():
            if field['type'] == 'list':
                list_vars = {
                    'model_name_snake_case': model['name']['snake_case'],
                    'field_name': name
                }
                macro_name = 'py_sql_list_' + field['element_type']
                if 'enum' in field:
                    macro_name += '_enum'
                out += self.spec['macro'][macro_name](list_vars) + '\n'
        return out

    def macro_py_sql_convert(self, fields:dict, indent='\t\t\t') -> str:
        out = ''
        single_field_index = 1

        for field_name in sorted(fields.keys()):
            if fields[field_name]['type'] == 'list':
                out += f"{indent}{field_name}={field_name},\n"

            else:
                macro_vars = {
                    'local_var': f'entry[{single_field_index}]',
                    'field_name': field_name,
                }
                macro_name = 'py_sql_convert_' + fields[field_name]["type"]
                if 'enum' in fields[field_name]:
                    macro_name += '_enum'
                out += self.spec['macro'][macro_name](macro_vars) + '\n'
                single_field_index += 1

        return out

    def macro_py_create_tables(self, all_models:list[dict], indent='\t') -> str:
        out = ''
        for item in all_models:

            non_list_fields = []
            list_tables = ''

            for name, field in item['model']['fields'].items():
                # list fields have their own tables
                # all other fields are added to the main table
                if field['type'] == 'list':
                    # concat list table macro
                    list_vars = {
                        'model_name_snake_case': item['model']['name']['snake_case'],
                        'field_name': name,
                    }
                    list_tables += self.spec['macro']['py_create_model_table_list'](list_vars) + '\n'
                else:
                    # append non list fields to create table macro
                    non_list_fields.append(f"'{name}'")

            if len(non_list_fields) == 0:
                field_list = ''
            else:
                field_list = ', ' + ', '.join(sorted(non_list_fields))

            table_vars = {
                'model_name_snake_case': item['model']['name']['snake_case'],
                'field_list': field_list
            }
            out += self.spec['macro']['py_create_model_table'](table_vars) + '\n'
            out += list_tables + '\n'

        return out

    def macro_py_test_crud_delete(self, model:dict, indent='\t\t') -> str:
        out = ''
        for name, field in model['fields'].items():
            if field['type'] == 'list':
                list_vars = {
                    'model_name_snake_case': model['name']['snake_case'],
                    'field_name': name,
                }
                out += self.spec['macro']['py_test_sql_delete'](list_vars) + '\n'

        return out

    def macro_py_post_init(self, fields:dict, indent='\t') -> str:
        out = ''
        for name, field in fields.items():
            if field['type'] == 'datetime':
                vars = deepcopy(field)
                vars['name'] = name
                out += self.spec['macro']['py_post_init_datetime'](vars) + '\n'

            elif field['type'] == 'list' and field['element_type'] == 'datetime':
                vars = deepcopy(field)
                vars['name'] = name
                out += self.spec['macro']['py_post_init_list_datetime'](vars) + '\n'
                
        return out
    
    def macro_py_example_fields(self, fields:dict, indent='\t\t\t') -> str:

        def convert_val(value, field_type):
            if field_type in ['bool', 'int', 'float']:
                return str(value)
            elif field_type == 'str':
                return f"'{value.replace("'", "\'")}'"
            elif field_type == 'datetime':
                return f"datetime.strptime('{value}', datetime_format_str)"

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

            lines.append(f"{indent}{name}={value}")

        return ',\n'.join(lines)

    def macro_py_random_fields(self, fields:dict, indent='\t\t\t') -> str:
        lines = []
        for name, field in fields.items():
            field_type = field['type']
            custom_function = field.get('random', None)
            # configure macro #

            if custom_function is not None:
                func_name = custom_function
                args = ''

            elif field['type'] == 'list':
                func_name = f'random_{field_type}'
                args = f"'{field['element_type']}'"

                if 'enum' in field:
                    args += f", {name}_options"

            else:
                func_name = f'random_{field_type}'
                args = ''
                if 'enum' in field:
                    func_name += '_enum'
                    args += f'{name}_options'

            # run macro #

            try:
                lines.append(f"{indent}{name}={func_name}({args})")
            except KeyError:
                raise MTemplateError(f'field {name} does not have a type')
            
        return ',\n'.join(lines)

    def macro_py_verify_fields(self, fields:dict, indent='\t') -> str:
        out = ''
        for name, field in fields.items():
            vars = deepcopy(field)
            vars['name'] = name

            if field['type'] == 'list':
                field_type = 'list_' + field['element_type']
             
            else:
                field_type = field['type']

            if 'enum' in field:
                field_type += '_enum'

            try:
                out += self.spec['macro'][f'py_verify_{field_type}'](vars) + '\n'
            except KeyError:
                raise MTemplateError(f'field {name} does not have a type')
        return out

    def macro_py_field_list(self, fields:dict) -> str:
        all_keys = ['id'] + list(fields.keys())
        keys = [f"'{name}'" for name in all_keys]
        return '[' + ', '.join(keys) + ']'

    def macro_py_field_definitions(self, fields:dict, indent='    ') -> str:
        out = ''
        for name, field in fields.items():
            if field['type'] == 'list':
                type_def = f'list[' + field['element_type'] + ']'
            else:
                type_def = field['type']
            out += f'{indent}{name}: {type_def}\n'
        return out

    def macro_py_enum_definitions(self, fields:dict, indent='    ') -> str:
        out = ''
        for name, field in fields.items():
            try:
                enum_values = field['enum']
            except KeyError:
                continue

            out += self.spec['macro'][f'py_enum_definition_begin']({'field_name': name}) + '\n'

            for option in enum_values:
                args = {'option': option.replace("'", "\'")}
                out += self.spec['macro'][f'py_enum_definition_option'](args) + '\n'

            out += self.spec['macro'][f'py_enum_definition_end']({}) + '\n'

        return out