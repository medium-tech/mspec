import os
import re
import json
import stat

from copy import copy
from pathlib import Path
from typing import Optional
from functools import reduce
from collections import OrderedDict
from dataclasses import dataclass

from jinja2 import FunctionLoader, StrictUndefined, TemplateError, Undefined, UndefinedError
from jinja2 import Environment as JinjaEnv


__all__ = [
    'iso_format_string',
    'MTemplateError',

    'MTemplateMacro',
    'MTemplate',
    
    'sort_dict_by_key_length',
    'py_escape_single_quote',
    'indent_lines',

    'NoParentDefinedError',
    'apply_template_slots'
]

#
# types
#

iso_format_string = '%Y-%m-%dT%H:%M:%S.%f'

class MTemplateError(Exception):
    pass

@dataclass
class MTemplateMacro:
    """a macro extracted by the MTemplateExtractor"""

    name:str
    text:str
    vars:dict

    def __call__(self, values=None, **kwargs):
        if values is None:
            values = {}

        if not isinstance(values, dict):
            raise TypeError(f"Expected dict for values, got {type(values).__name__}")
        
        values.update(kwargs)
        return self.render(values)
    
    def render(self, values:dict) -> str:
        # the keys in self.vars are the string in the template that will be replaced by the 
        # variable/macro arg which is defined in the value of the dict
        output = copy(self.text)
        for template_value, input_key in sort_dict_by_key_length(self.vars).items():
            data_key, post_processor = self.parse_key(input_key)
            try:
                output_value = post_processor(self._get_value(values, data_key))
                output = output.replace(template_value, output_value)
            except KeyError as e:
                raise MTemplateError(f'Unknown key {e} given to macro {self.name}, input key: {input_key}')
        return output
    
    def parse_key(self, key:str) -> tuple[str, callable]:
        """parse a data key and check for registered functions to return as post processors"""
        if key.startswith('py_escape_single_quote(') and key.endswith(')'):
            return key[23:-1], py_escape_single_quote
        else:
            return key, lambda x: x
        
    @staticmethod
    def _get_value(data:dict, key:str) -> str:
        """
        get value from dict, if key not found return empty string
            key can be a dot separated path to a nested value
            e.g. 'model.name.kebab_case'
        """
        sub_keys = key.split('.')
        current_data = data

        for sub_key in sub_keys:
            try:
                current_data = current_data[sub_key]

            except TypeError as e:
                if sub_key.isnumeric():
                    try:
                        index = int(sub_key)
                        current_data = current_data[index]
                    except (IndexError, TypeError) as e:
                        raise KeyError(f'IndexError: {e} looking for index "{sub_key}" in data: {current_data}')
                else:
                    raise KeyError(sub_key)
        return str(current_data)


class MTemplate:
    """extract a jinja template from a source file"""

    def __init__(self, path:str|Path, **kwargs) -> 'MTemplate':
        self.path = Path(path)
        self.debug = kwargs.get('debug', False)
        self.disable_strict = kwargs.get('disable_strict', False)

        # self.jinja = jinja

        if path.suffix in ['.js', '.ts']:
            self.prefix = '//'
            self.postfix = ''
            self.single_quotes = False
        elif path.suffix in ['.html', '.htm']:
            self.prefix = '<!--'
            self.postfix = '-->'
            self.single_quotes = False
        elif path.suffix == '.css':
            self.prefix = '/*'
            self.postfix = '*/'
            self.single_quotes = False
        elif path.suffix == '.json':
            self.prefix = '"_": "'
            self.postfix = '",'
            self.single_quotes = True
        else:
            self.prefix = kwargs.get('prefix', '#')
            self.postfix = kwargs.get('postfix', '')
            self.single_quotes = kwargs.get('single_quotes', False)

        self.template_lines = []
        self.template_vars = {}
        self.macros = {}

    #
    # util methods
    #

    def _load_json(self, data:str):
        if self.single_quotes:
            return json.loads(data.replace("'", '"'))
        else:
            return json.loads(data)

    def _write_file(self, path:Path, data:str):
        try:
            with open(path, 'w+') as f:
                f.write(data)
        except FileNotFoundError:
            os.makedirs(path.parent)
            with open(path, 'w+') as f:
                f.write(data)

        if path.suffix == '.sh':
            out_stat = path.stat()
            os.chmod(path.as_posix(), out_stat.st_mode | stat.S_IEXEC)

    #
    # parsing methods
    #

    def _parse_vars_line(self, line:str):
        try:
            vars_str = line.split('::')[1].strip()
            vars_decoded = self._load_json(vars_str)
            if not isinstance(vars_decoded, dict):
                raise MTemplateError(f'vars must be a object not "{type(vars_decoded).__name__}"')
            
            self.template_vars.update(vars_decoded)

        except json.JSONDecodeError as e:
            raise MTemplateError(f'JSONDecodeError:{e} in vars definition')
    
    def _parse_macro(self, macro_def_line:str, lines:list[str]):
        macro_split = macro_def_line.split('::')
        try:
            macro_name = macro_split[1].strip()
        except IndexError:
            raise MTemplateError(f'macro definition missing name')
        
        try:
            macro_vars = self._load_json(macro_split[2].strip())
        except json.JSONDecodeError as e:
            raise MTemplateError(f'JSONDecodeError:{e} parsing macro vars')
        except IndexError:
            macro_vars = {}

        macro_text = ''.join(lines)

        self.macros[macro_name] = MTemplateMacro(macro_name, macro_text, macro_vars)

    def _parse_insert_line(self, line:str, line_no:int) -> str:
        try:
            _, insert_stmt = line.split('::')
        except ValueError:
            raise MTemplateError(f'invalid insert statement on line {line_no}')
        
        return '{{ ' + insert_stmt.strip() + ' }}\n'

    #
    # api
    #
    
    def parse(self):

        ignoring = False
        open_for_loops = 0
        for_loop_replacements = []
        open_if_statements = 0

        with open(self.path, 'r') as f:
            line_no = 0

            # iter over each line of file and parse tokens #

            for line in f:

                leading_whitespace = lambda: re.match(r'^\s*', line).group(0)

                line_no += 1
                line_stripped = line.replace(self.postfix, '').strip()

                #
                # vars line
                #

                if line_stripped.startswith(f'{self.prefix} vars :: '):
                    try:
                        self._parse_vars_line(line_stripped)
                    except MTemplateError as e:
                        raise MTemplateError(f'{e} on line {line_no} of {self.path}')

                #
                # for loop
                #

                # open for loop #
                
                elif line_stripped.startswith(f'{self.prefix} for :: '):
                    open_for_loops += 1

                    # parse for loop definition #

                    try:
                        definition_split = line_stripped.split('::')
                        jinja_for_line = definition_split[1]

                    except IndexError:
                        raise MTemplateError(f'for loop definition missing jinja loop syntax')
                    
                    # parse block vars #

                    try:
                        for_block_vars = self._load_json(definition_split[2].strip())

                    except json.JSONDecodeError:
                        try:
                            for_block_vars = eval(definition_split[2].strip())
                        except Exception as e:
                            raise MTemplateError(f'Caught while parsing block vars :: {e.__class__.__name__}:{e}')
                    
                    if not isinstance(for_block_vars, dict):
                        raise MTemplateError(f'vars must be a dict not {type(for_block_vars).__name__}')
                    
                    for_loop_replacements.append(for_block_vars)
                    
                    # append lines to template #

                    self.template_lines.append(leading_whitespace() + jinja_for_line.strip() + '\n')
                
                # close for loop #

                elif line_stripped.startswith(f'{self.prefix} end for ::'):
                    if open_for_loops < 1:
                        raise MTemplateError(f'end for without beginning for statement on line {line_no} of {self.path}')
                    
                    try:
                        _, mods = line_stripped.split('::')
                    except ValueError:
                        raise MTemplateError(f'invalid end for statement on line {line_no} of {self.path}')
                    
                    end_for_mods = mods.strip().split()
                    end_for = '{% endfor %}' if 'rstrip' in end_for_mods else '{% endfor %}\n'

                    self.template_lines.append(leading_whitespace() + end_for)
                    del for_loop_replacements[-1]
                    open_for_loops -= 1

                #
                # branching - if / elif / else
                #

                elif line_stripped.startswith(f'{self.prefix} if ::'):
                    if_statement = line_stripped.split('::')[1].strip()
                    self.template_lines.append(leading_whitespace() + f'{{% if {if_statement} %}}\n')
                    open_if_statements += 1

                elif line_stripped.startswith(f'{self.prefix} elif ::'):
                    if open_if_statements < 1:
                        raise MTemplateError(f'elif without beginning if statement on line {line_no}')
                    elif_statement = line_stripped.split('::')[1].strip()
                    self.template_lines.append(leading_whitespace() + f'{{% elif {elif_statement} %}}\n')

                elif line_stripped.startswith(f'{self.prefix} else ::'):
                    if open_if_statements < 1:
                        raise MTemplateError(f'else without beginning if statement on line {line_no}')
                    self.template_lines.append(leading_whitespace() + '{% else %}\n')

                elif line_stripped.startswith(f'{self.prefix} end if ::'):
                    if open_if_statements < 1:
                        raise MTemplateError(f'endif without beginning if statement on line {line_no}')
                    self.template_lines.append(leading_whitespace() + '{% endif %}\n')
                    open_if_statements -= 1

                #
                # ignore lines
                #

                elif line_stripped.startswith(f'{self.prefix} ignore ::'):
                    ignoring = True

                elif line_stripped.startswith(f'{self.prefix} end ignore ::'):
                    ignoring = False

                #
                # insert line
                #

                elif line_stripped.startswith(f'{self.prefix} insert ::'): 
                    self.template_lines.append(self._parse_insert_line(line_stripped, line_no))

                #
                # replace lines
                #

                elif line_stripped.startswith(f'{self.prefix} replace ::'):
                    replace_start_line_no = line_no

                    # parse replace statement #

                    try:
                        _, replacement_stmt = line_stripped.split('::')
                    except ValueError:
                        raise MTemplateError(f'invalid replace statement on line {line_no}')

                    while True:

                        # seek ahead to each line in replacement block #

                        try:
                            next_line = next(f)
                        except StopIteration:
                            raise MTemplateError(f'Unterminated replace block starting on line {replace_start_line_no} of {self.path}')
                        
                        next_line_strippped = next_line.replace(self.postfix, '').strip()
                        line_no += 1
                        
                        # insert replacement statement #

                        if next_line_strippped == f'{self.prefix} end replace ::':
                            self.template_lines.append('{{ ' + replacement_stmt.strip() + ' }}\n')
                            break
                
                # macros #

                elif line_stripped.startswith(f'{self.prefix} macro ::'):
                    macro_def_line = line_stripped
                    macro_lines = []

                    while True:
                        
                        # seek ahead to each line in macro block #
                        try:
                            next_line = next(f)
                        except StopIteration:
                            break
                        
                        next_line_strippped = next_line.replace(self.postfix, '').strip()
                        line_no += 1

                        try:
                            if next_line_strippped == f'{self.prefix} end macro ::':
                                self._parse_macro(macro_def_line, macro_lines)
                                break
                            elif next_line_strippped.startswith(f'{self.prefix} macro ::'):
                                self._parse_macro(macro_def_line, macro_lines)
                                macro_def_line = next_line_strippped
                                macro_lines = []
                                continue
                            else:
                                macro_lines.append(next_line)
                        except MTemplateError as e:
                            raise MTemplateError(f'{e} on line {line_no} of {self.path}')
                            
                # end of loop, ignore the line or add it to template #

                elif ignoring:
                    continue
            
                else:
                    if open_for_loops == 0:
                        self.template_lines.append(line)
                    else:
                        # inside for loop, replace for loop vars
                        for_vars = reduce(lambda acc, entry: {**acc, **entry}, for_loop_replacements, {})
                        new_line = line
                        for key, value in sort_dict_by_key_length(for_vars).items():
                            new_line = new_line.replace(key, '{{ ' + value + ' }}')
                        self.template_lines.append(new_line)

            if open_for_loops > 0:
                raise MTemplateError(f'Unterminated for loop in file {self.path}')
            if open_if_statements > 0:
                raise MTemplateError(f'Unterminated if statement in file {self.path}')

        return self

    def template_string(self) -> str:
        """create template string for jinja"""
        template = ''.join(self.template_lines)
        for key, value in sort_dict_by_key_length(self.template_vars).items():
            template = template.replace(key, '{{ ' + value + ' }}')
        return template

@dataclass
class MTemplateExtractor:
    template_paths: list[Path]

    templates: dict[str, str]
    template_objects: dict[str, MTemplate]
    jinja: JinjaEnv

    debug: bool = False
    disable_strict: bool = False

    @classmethod
    def init_from_dir(cls, source:str|Path, **kwargs):
        
        src_dir = Path(source)
        disable_strict = kwargs.get('disable_strict', False)


        # recursively collect all files from source
        template_paths = [p for p in src_dir.rglob('*') if p.is_file()]
        
        # store in templates lookup, keys are relative paths to source directory
        template_objs: dict[str, MTemplate] = {str(p.relative_to(src_dir)): MTemplate(p).parse() for p in template_paths}
        template_strs = {}
        macros = {}

        # compile macros #
        for template_name, template in template_objs.items():
            for macro_name, macro in template.macros.items():
                if macro_name in macros:
                    raise ValueError(f'Duplicate macro "{macro_name}" found in template "{template_name}"')
                else:
                    macros[macro_name] = macro
            template_strs[template_name] = template.template_string()

        # jinja #

        jinja_env = JinjaEnv(
            autoescape=False,
            loader=FunctionLoader(lambda path: template_strs[path]),
            undefined=Undefined if disable_strict else StrictUndefined,
            comment_start_string='/*--', 
            comment_end_string='--*/',
        )
        jinja_env.globals.update({'macro': macros})
        
        # return instance #

        return cls(
            template_paths=template_paths, 
            debug=kwargs.get('debug', False),
            disable_strict=disable_strict,
            templates=template_strs,
            template_objects=template_objs,
            jinja=jinja_env
        )

    def render_template(self, name:str, vars: Optional[dict]=None, output:Optional[Path|str]=None) -> str:
    
        #
        # render template
        #

        try:
            jinja_template = self.jinja.get_template(name)
            rendered_template = jinja_template.render(vars or dict())
        except KeyError as exc:
            if name is None:
                raise TemplateError(f'Template name is required')
            else:
                raise TemplateError(f'Template "{name}" not found: {exc}')

        except UndefinedError as e:
            raise TemplateError(f'{e} in template "{name}"')
        except TemplateError as e:
            raise TemplateError(f'{e.__class__.__name__}:{e} in template "{name}"')
        except MTemplateError as e:
            raise MTemplateError(f'{e.__class__.__name__}:{e} in template "{name}"')

        
        # write file (if requested) #

        if output is not None:
            out_path = Path(output)

            # write jinja template in debug mode #

            if self.debug:
                debug_output_path = out_path.with_name(out_path.name + '.jinja2')
                try:
                    self._write_file(debug_output_path, self.template_str)
                    
                except Exception as e:
                    print(f':: error writing debug template :: {debug_output_path}: {e}')
                raise

        return rendered_template if not self.debug else self.template_str

#
# utility functions
#

def sort_dict_by_key_length(dictionary:dict) -> OrderedDict:
    """sort dictionary by key length in descending order, it is used when replacing template variables,
    by sorting the dictionary by key length, we can ensure that the longest keys are replaced first, so that
    shorter keys that are substrings of longer keys are not replaced prematurely"""
    return OrderedDict(sorted(dictionary.items(), key=lambda item: len(item[0]), reverse=True))

def py_escape_single_quote(s:str) -> str:
    return s.replace("'", "\'")

def indent_lines(lines:str, indent:int=2) -> str:
    '''Indent each line of a multi-line string for pretty printing'''
    return '\n'.join(f'{"\t" * indent}{line}' for line in lines.splitlines())


#
# slots - old feature, doesn't work after refactor
#          designed to keep two separate files in sync
#

# class NoParentDefinedError(Exception):
#     pass


# def apply_slots_to_children(cls, debug:bool=False):
#     raise NotImplementedError(f'not implemented for new MTemplate class after refactor')
#     template_proj = cls({}, debug=debug)
#     paths = template_proj.load_template_paths()
#     for macro in paths['macro_only']:
#         try:
#             new_template_content = apply_template_slots(macro['src'])
#         except NoParentDefinedError:
#             if debug:
#                 print(f'Warning no parent defined in macro template: {macro["src"]}')
#             continue
        
#         if debug:
#             print(f'Would have applied slots to macro template: {macro["src"]}')
#         else:
#             with open(macro['src'], 'w') as f:
#                 f.write(new_template_content)
#             print(f'Applied slots to macro template: {macro["src"]}')


# def apply_template_slots(child_path: Path | str) -> str:
    """Given a child template path, regenerate the child template
    by replacing the slot commands in the parent template with the
    corresponding slot content from the child template.

    args:
        child_path: Path or str - path to the child template file

    returns:
        str - the generated child template content
    """

    #
    # init
    #

    child_template_path = Path(child_path)

    with open(child_template_path) as f:
        child_content = f.readlines()

    #
    # parse child template
    #

    parent_commands = []
    child_template_lines = []
    slots_in_child = []
    all_slot_content = {}
    inside_slot = False
    current_slot_name = None
    parent_line = None

    for line in child_content:
        if line.strip().startswith('# parent ::'):
            if inside_slot:
                raise ValueError(f'parent command not allowed inside slot: {current_slot_name}')
            
            parent_commands.append(line)
            parent_line = line

        elif line.strip().startswith('# slot ::'):
            if inside_slot:
                raise ValueError(f'Nested slots are not supported (slot: {slot_name})')
            
            inside_slot = True

            child_slot_name = line.strip().split('::')[1].strip()
            current_slot_name = child_slot_name
            slots_in_child.append(current_slot_name)
            all_slot_content[current_slot_name] = [line]
        
        elif inside_slot and line.strip().startswith('# end slot'):
            if not inside_slot:
                raise ValueError(f'End slot found without matching start slot (slot: {current_slot_name})')
            all_slot_content[current_slot_name].append(line)
            current_slot_name = None
            inside_slot = False
        
        elif inside_slot:
            all_slot_content[current_slot_name].append(line)

        else:
            child_template_lines.append(line)

    if not parent_commands:
        raise NoParentDefinedError(f'No parent defined in child template: {child_template_path}')

    elif len(parent_commands) > 1:
        raise ValueError('Multiple parent templates found, only one parent template is supported.')
    
    # get parent template path #

    parent_line = parent_commands[0]

    try:
        parent_path_str = parent_line.strip().split('::')[1].strip()
    except IndexError:
        raise ValueError('Invalid parent template command format.')
    
    parent_template = child_template_path.parent / parent_path_str

    with open(parent_template) as f:
        parent_content = f.readlines()

    #
    # generate child template from parent
    #

    output_lines = []
    slots_replaced = []

    for line in parent_content:
        if line.strip().startswith('# slot ::'):
            try:
                slot_name = line.strip().split('::')[1].strip()
            except IndexError:
                raise ValueError('Invalid slot command format.')
            try:
                slot_content = all_slot_content[slot_name]
            except KeyError:
                raise ValueError(f'Slot "{slot_name}" in parent not found in child')

            output_lines.extend(slot_content)
            slots_replaced.append(slot_name)

        else:
            output_lines.append(line)

    output_lines.append(f'\n{parent_line}')

    if not slots_replaced:
        raise ValueError('No slots were replaced; ensure slot names match between parent and child templates.')

    if sorted(list(set(slots_replaced))) != sorted(slots_in_child):
        slots_not_used = set(slots_in_child) - set(slots_replaced)
        raise ValueError(f'Some slots in child template were not used in parent template: {slots_not_used}')

    return ''.join(output_lines)