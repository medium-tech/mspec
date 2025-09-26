from mtemplate import MTemplateProject, MTemplateError
from pathlib import Path
import shutil
from copy import deepcopy


__all__ = ['MTemplatePyProject']


class MTemplatePyProject(MTemplateProject):

    app_name = 'py'
    template_dir = Path(__file__).parent.parent.parent / 'templates' / app_name
    cache_dir = Path(__file__).parent / '.cache' / app_name

    prefixes = {
        'src/template_module': 'module',
        'tests/template_module/__init__.py': 'module', 
        
        'src/template_module/single_model': 'model',
        'tests/template_module': 'model',

        'src/template_module/multi_model': 'macro_only',
        'tests/template_module/test_multi': 'macro_only',
        'tests/template_module/perf_multi': 'macro_only'
    }

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
    
    def macro_py_tk_field_table(self, fields:dict, indent='\t') -> str:
        out = ''
        column = 2
        for name, field in fields.items():
            macro_name = f'py_tk_field_table_{field["type"]}'
            if field['type'] == 'list':
                macro_name += f'_{field["element_type"]}'

            vars = deepcopy(field)
            vars['name'] = name
            vars['column'] = str(column)
            out += self.spec['macro'][macro_name](vars) + '\n'
            column += 1

        return out
          
    @classmethod
    def render(cls, spec:dict, env_file:str|Path=None, output_dir:str|Path=None, debug:bool=False, disable_strict:bool=False, use_cache:bool=True) -> 'MTemplatePyProject':
        template_proj = super().render(spec, env_file, output_dir, debug, disable_strict, use_cache)
        if env_file is not None:
            env_file_out = Path(env_file) / '.env'
            shutil.copyfile(env_file, env_file_out)
            print(f'copied {env_file} to {env_file_out}')
        return template_proj
