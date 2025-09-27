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

        non_list_fields = model['non_list_fields']
        num_non_list_fields = len(non_list_fields)

        fields_py = ''
        for field in non_list_fields:
            field_name = field['name']['snake_case']
            if field['type'] == 'datetime':
                fields_py += f"obj.{field_name}.isoformat(), "
            else:
                fields_py += f"obj.{field_name}, "

        if num_non_list_fields == 0:
            fields_sql = ''
            sql_values = 'DEFAULT VALUES'
        else:
            fields_sql = '(' + ', '.join([f"'{f['name']['snake_case']}'" for f in non_list_fields]) + ')'

            question_marks = ', '.join(['?'] * num_non_list_fields)
            sql_values = f'VALUES({question_marks})'

        create_vars = {
            'model': model,
            'fields_sql': fields_sql,
            'sql_values': sql_values,
            'fields_py': fields_py.strip()
        }

        out += self.spec['macro']['py_sql_create'](create_vars) + '\n'

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

    @classmethod
    def render(cls, spec:dict, env_file:str|Path=None, output_dir:str|Path=None, debug:bool=False, disable_strict:bool=False, use_cache:bool=True) -> 'MTemplatePyProject':
        template_proj = super().render(spec, env_file, output_dir, debug, disable_strict, use_cache)
        if env_file is not None:
            env_file_out = Path(env_file) / '.env'
            shutil.copyfile(env_file, env_file_out)
            print(f'copied {env_file} to {env_file_out}')
        return template_proj
