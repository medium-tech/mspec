import os
import stat
import json
import shutil
import importlib

from enum import Enum
from pathlib import Path
from collections import OrderedDict
from typing import Optional, Any, Generator

from jinja2 import Environment, FunctionLoader, StrictUndefined, UndefinedError, TemplateSyntaxError
from bson import ObjectId

__all__ = [

]

class MTemplateError(Exception):
    pass

def sort_dict_by_key_length(dictionary:dict) -> OrderedDict:
    """sort dictionary by key length in descending order, it is used when replacing template variables,
    by sorting the dictionary by key length, we can ensure that the longest keys are replaced first, so that
    shorter keys that are substrings of longer keys are not replaced prematurely"""
    return OrderedDict(sorted(dictionary.items(), key=lambda item: len(item[0]), reverse=True))


class MTemplateProject:
        
    def __init__(self, spec:dict, debug:bool=False):
        self.spec = spec
        self._init_spec()
        self.debug = debug

        loader = lambda path: MTemplateExtractor.template_from_file(path)

        self.jinja = Environment(
            autoescape=False,
            loader=FunctionLoader(loader),
            undefined=StrictUndefined,
        )
        self.jinja.globals.update(self.spec)

    def _init_spec(self):
        all_models = []
        for module in self.spec['modules'].values():
            for model in module['models'].values():
                all_models.append({'module': module, 'model': model})
        self.spec['all_models'] = all_models
        

    def write_file(self, path:Path, data:str):
        try:
            with open(path, 'w+') as f:
                f.write(data)
        except FileNotFoundError:
            os.makedirs(path.parent)
            with open(path, 'w+') as f:
                f.write(data)

    def render_template(self, template_vars:dict, template_file:Path|str, template_out_path:Path):
        template_file = Path(template_file)
        if self.debug:
            debug_output_path = template_out_path.with_name(template_out_path.name + '.jinja2')
            jinja_template = MTemplateExtractor.template_from_file(template_file)
            self.write_file(debug_output_path, jinja_template)

        jinja_template = self.jinja.get_template(template_file.as_posix())
        try:
            rendered_template = jinja_template.render(template_vars)
        except UndefinedError as e:
            raise UndefinedError(f'{e} in template {template_file}')
        
        self.write_file(template_out_path, rendered_template)

    
class MTemplateExtractor:

    def __init__(self, path:str|Path, prefix='#') -> None:
        self.path = Path(path)
        self.prefix = prefix
        self.template = ''
        self.template_lines = []
        self.template_vars = {}
        self.macros = {}

    def _parse_vars_line(self, line:str, line_no:int):
        try:
            vars_str = line.split('::')[1].strip()
            vars_decoded = json.loads(vars_str)
            if not isinstance(vars_decoded, dict):
                raise MTemplateError(f'vars must be a json object not "{type(vars_decoded).__name__}" on line {line_no}')
            
            self.template_vars.update(vars_decoded)

        except json.JSONDecodeError as e:
            raise MTemplateError(f'caught JSONDecodeError in vars definition on line {line_no} | {e}')

    def _parse_for_lines(self, definition_line:str, lines:list[str], start_line_no:int):

        # parse for loop definition #

        try:
            definition_split = definition_line.split('::')
            jinja_line = definition_split[1]

        except IndexError:
            raise MTemplateError(f'for loop definition mmissing jinja loop syntax on {start_line_no}')
        
        # parse block vars #

        try:
            block_vars = json.loads(definition_split[2].strip())

        except json.JSONDecodeError:
            try:
                block_vars = eval(definition_split[2].strip())
            except Exception as e:
                raise MTemplateError(f'error parsing block vars on line {start_line_no} of {self.path} | {e}')
        
        if not isinstance(block_vars, dict):
            raise MTemplateError(f'vars must be a dict not "{type(block_vars).__name__}" on line {start_line_no} of {self.path}')
        
        # append lines to template #

        self.template_lines.append(jinja_line.strip() + '\n')

        for line in lines:
            new_line = line 
            for key, value in sort_dict_by_key_length(block_vars).items():
                new_line = new_line.replace(key, '{{ ' + value + ' }}')
            self.template_lines.append(new_line)
        
        self.template_lines.append('{% endfor %}\n')
    
    def _parse_macro(self, macro_def_line:str, lines:list[str], start_line_no:int):
        macro_split = macro_def_line.split('::')
        macro_name = macro_split[1].strip()
        try:
            macro_vars = json.loads(macro_split[2].strip())
        except IndexError:
            macro_vars = {}
        raise NotImplementedError('macros are not yet implemented')

    def create_template(self) -> str:
        template = ''.join(self.template_lines)
        for key, value in sort_dict_by_key_length(self.template_vars).items():
            template = template.replace(key, '{{ ' + value + ' }}')
        return template

    def write(self, path:str|Path):
        with open(path, 'w+') as f:
            f.write(self.create_template())

    def parse(self):

        ignoring = False

        with open(self.path, 'r') as f:
            line_no = 0

            # iter over each line of file and parse tokens #

            for line in f:
                line_no += 1
                line_stripped = line.strip()

                # vars line #

                if line_stripped.startswith(f'{self.prefix} vars :: '):
                    self._parse_vars_line(line_stripped, line_no)

                # for loop #

                elif line_stripped.startswith(f'{self.prefix} for :: '):
                    for_lines = []
                    for_start_line_no = line_no

                    while True:

                        # seek ahead to each line in for loop #

                        try:
                            next_line = next(f)
                        except StopIteration:
                            raise MTemplateError(f'Unterminated for loop starting on line {for_start_line_no} of {self.path}')
                        
                        next_line_strippped = next_line.strip()
                        line_no += 1
                            
                        if next_line_strippped == f'{self.prefix} end for ::':
                            break

                        for_lines.append(next_line)
                    
                    self._parse_for_lines(line_stripped, for_lines, for_start_line_no)

                # end for #
                
                elif line_stripped.startswith(f'{self.prefix} end for ::'):
                    raise MTemplateError(f'end for without beginning for statement on line {line_no}')
                
                # ignore lines #

                elif line_stripped.startswith(f'{self.prefix} ignore ::'):
                    ignoring = True

                elif line_stripped.startswith(f'{self.prefix} end ignore ::'):
                    ignoring = False

                # replace lines #

                elif line_stripped.startswith(f'{self.prefix} replace ::'):
                    replace_start_line_no = line_no

                    while True:
                        
                        # parse replace statement #

                        try:
                            _, replacement_stmt = line_stripped.split('::')
                        except ValueError:
                            raise MTemplateError(f'invalid replace statement on line {line_no}')

                        # seek ahead to each line in replacement block #

                        try:
                            next_line = next(f)
                        except StopIteration:
                            raise MTemplateError(f'Unterminated replace block starting on line {replace_start_line_no} of {self.path}')
                        
                        next_line_strippped = next_line.strip()
                        line_no += 1
                        
                        # insert replacement statement #

                        if next_line_strippped == f'{self.prefix} end replace ::':
                            self.template_lines.append('{{ ' + replacement_stmt.strip() + ' }}\n')
                            break
                
                # macros #

                elif line_stripped.startswith(f'{self.prefix} macro ::'):
                    macro_start_line_no = line_no
                    macro_def_line = line_stripped
                    macro_lines = []

                    while True:
                        
                        # seek ahead to each line in macro block #
                        try:
                            next_line = next(f)
                        except StopIteration:
                            break
                        
                        next_line_strippped = next_line.strip()
                        line_no += 1

                        if next_line_strippped == f'{self.prefix} end macro ::':
                            self._parse_macro(macro_def_line, macro_lines, macro_start_line_no)
                            break
                        elif next_line_strippped.startswith(f'{self.prefix} macro ::'):
                            self._parse_macro(macro_def_line, macro_lines, macro_start_line_no)
                            macro_start_line_no = line_no
                            macro_def_line = next_line_strippped
                            macro_lines = []
                            continue
                        else:
                            macro_lines.append()
                            
                # end of loop, ignore the line or add it to template #

                elif ignoring:
                    continue
            
                else:
                    self.template_lines.append(line)

    @classmethod
    def template_from_file(cls, path:str|Path) -> str:
        path = Path(path)
        is_js = path.suffix in ['.js', '.ts']
        instance = cls(path, prefix='//' if is_js else '#')
        instance.parse()
        return instance.create_template()
    