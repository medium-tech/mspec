import os
import json
import shutil
import stat

from copy import copy
from pathlib import Path
from collections import OrderedDict
from dataclasses import dataclass, asdict

from jinja2 import Environment, FunctionLoader, StrictUndefined, TemplateError, Undefined

__all__ = [
    'iso_format_string',
    'MTemplateProject',
    'MTemplateExtractor',
    'MTemplateMacro',
    'MTemplateError',
    'sort_dict_by_key_length'
]

iso_format_string = '%Y-%m-%dT%H:%M:%S.%f'

class MTemplateError(Exception):
    pass

class MTemplateCacheMiss(MTemplateError):
    pass

def sort_dict_by_key_length(dictionary:dict) -> OrderedDict:
    """sort dictionary by key length in descending order, it is used when replacing template variables,
    by sorting the dictionary by key length, we can ensure that the longest keys are replaced first, so that
    shorter keys that are substrings of longer keys are not replaced prematurely"""
    return OrderedDict(sorted(dictionary.items(), key=lambda item: len(item[0]), reverse=True))


class MTemplateProject:
    """
    a project represents a single mtemplate project, it is responsible for loading the spec,
    loading the templates, caching and rendering the templates
    """

    app_name = '-'

    template_dir = Path(__file__).parent.parent.parent / 'templates' / app_name
    cache_dir = Path(__file__).parent / '.cache' / app_name

    prefixes = {}

    def __init__(self, spec:dict, debug:bool=False, disable_strict:bool=False) -> None:
        self.spec = spec
        self.spec['macro'] = {}
        self.debug = debug
        self.template_paths:dict[str, list[dict[str, str]]] = {}
        self.templates:dict[str, MTemplateExtractor] = {}

        self.jinja = Environment(
            autoescape=False,
            loader=FunctionLoader(self.jinja_loader),
            undefined=Undefined if disable_strict else StrictUndefined,
        )

    def default_output_dir(self) -> Path:
        parent_dir = Path(__file__).parent.parent.parent
        try:
            return parent_dir / 'out' / self.spec['project']['name']['kebab_case'] / self.app_name
        except KeyError:
            raise MTemplateError('spec must define project.name.kebab_case')

    #
    # templates
    #

    # get from disk #

    def load_template_paths(self, use_cache:bool=False, templatize_paths:bool=True) -> dict[str, list[dict[str, str]]]:
        paths = {
            'app': [],
            'module': [],
            'model': [],
            'macro_only': []
        }

        prefixes_by_key_len = sort_dict_by_key_length(self.prefixes)

        source_path_dir = self.cache_dir if use_cache else self.template_dir

        for root, _, files in os.walk(source_path_dir):
            if 'node_modules' in root:
                continue
            
            if '__pycache__' in root:
                    continue
            
            if '.egg-info' in root:
                continue

            if 'playwright-report' in root:
                continue
            
            if 'test-results' in root:
                continue

            for name in files:
                if name == '.DS_Store':
                    continue

                if name.endswith('.sqlite3'):
                    continue

                src = os.path.join(root, name)

                rel_path = os.path.relpath(src, source_path_dir)

                rel_path_template = rel_path.replace('single-model', '{{ model.name.kebab_case }}')
                rel_path_template = rel_path_template.replace('single_model', '{{ model.name.snake_case }}')
                rel_path_template = rel_path_template.replace('singleModel', '{{ model.name.camel_case }}')
                rel_path_template = rel_path_template.replace('SingleModel', '{{ model.name.pascal_case }}')

                rel_path_template = rel_path_template.replace('template-module', '{{ module.name.kebab_case }}')
                rel_path_template = rel_path_template.replace('template_module', '{{ module.name.snake_case }}')
                rel_path_template = rel_path_template.replace('templateModule', '{{ module.name.camel_case }}')
                rel_path_template = rel_path_template.replace('TemplateModule', '{{ module.name.pascal_case }}')

                template = {'src': src, 'rel': rel_path, 'rel_template': rel_path_template}

                for prefix, template_type in prefixes_by_key_len.items():
                    if rel_path.startswith(prefix):
                        paths[template_type].append(template)
                        break
                else:
                    paths['app'].append(template)

                # if any([rel_path.startswith(prefix) for prefix in self.macro_only_prefixes]):
                #     paths['macro_only'].append(template)
                # elif any([rel_path.startswith(prefix) for prefix in self.model_prefixes]):
                #     paths['model'].append(template)
                # elif any([rel_path.startswith(prefix) for prefix in self.module_prefixes]):
                #     paths['module'].append(template)
                # else:
                #     paths['app'].append(template)

        self.template_paths = paths
        return paths

    def extract_templates(self, templatize_paths:bool=True) -> dict:
        template_paths = self.load_template_paths(templatize_paths=templatize_paths)
        try:
            paths = template_paths['app'] + template_paths['module'] + template_paths['model'] + template_paths['macro_only']
        except KeyError:
            raise MTemplateError('template_paths must contain app, module and model keys')
        
        for path in paths:
            try:
                template = MTemplateExtractor.template_from_file(path['src'])
                self.templates[path['rel']] = template
            except Exception as exc:
                print(path['src'])
                raise

        return self.templates

    def load_cached_templates(self) -> dict:
        """Load cached jinja2 template files from disk"""
        #
        # init
        #

        cache_dir = Path(__file__).parent / '.cache' / self.app_name
        
        if not cache_dir.exists():
            raise MTemplateCacheMiss(f'Cache directory not found: {cache_dir}. Run cache command first.')

        print(f':: loading cached templates :: {cache_dir}')

        #
        # self.spec['macro'] - load from cache
        #

        macros_file = cache_dir / 'macro.json'
        
        try:
            with open(macros_file, 'r') as f:
                for macro_name, macro_data in json.load(f).items():
                    self.spec['macro'][macro_name] = MTemplateMacro(**macro_data)

        except FileNotFoundError:
            print(f':: WARNING :: macro.json not found in cache')
            raise MTemplateCacheMiss(f'macro.json not found in cache: {macros_file}. Run cache command first.')

        #
        # self.template_paths - load from cache
        #

        template_paths_file = cache_dir / 'template_paths.json'

        try:
            with open(template_paths_file, 'r') as f:
                self.template_paths = json.load(f)

        except FileNotFoundError:
            print(f':: WARNING :: template_paths.json not found in cache')
            raise MTemplateCacheMiss(f'template_paths.json not found in cache: {template_paths_file}. Run cache command first.')

        #
        # self.templates - load cached jinja templates
        #

        for template_type in self.template_paths.keys():
            for template_info in self.template_paths[template_type]:
                rel_path = template_info['rel']
                
                if rel_path.endswith('/.env') or rel_path == '.env':
                    print(f':: WARNING :: ignoring .env file: {rel_path}')
                    continue

                cache_file_path = cache_dir / f'{rel_path}.jinja2'

                try:
                    with open(cache_file_path, 'r') as f:
                        self.templates[rel_path] = f.read()
                except FileNotFoundError:
                    raise MTemplateCacheMiss(f'Cached template not found: {cache_file_path}')

                print(f'    loaded from cache :: {rel_path}')
        
        print(f':: done loading cache :: {self.app_name} :: {len(self.templates)} templates')
        return self.templates

    # jinja templating #

    def jinja_loader(self, rel_path:str) -> str:
        try:

            return self.templates[rel_path].create_template()   # MTemplateExtractor obj when extracting

        except AttributeError:                                  # str when loading from cache
            assert isinstance(self.templates[rel_path], str)
            return self.templates[rel_path]
        
        except KeyError: 
            raise MTemplateError(f'template {rel_path} not found')
        
    def init_template_vars(self):
        
        # all model list #
        all_models = []
        for module in self.spec['modules'].values():
            for model in module['models'].values():
                all_models.append({'module': module, 'model': model})

        self.spec['all_models'] = all_models
        
        # macros from templates #
        for template in self.templates.values():
            if isinstance(template, str):
                """ignore str values, this means we're loading from cache, load_cached_templates already did this"""
            else:
                # extracting from templates, add macros to spec
                self.spec['macro'].update(template.macros)
        
        # macros from mtemplate classes #
        for attr in dir(self):
            if attr.startswith('macro_'):
                macro_name = attr[6:]
                self.spec['macro'][macro_name] = getattr(self, attr)

        self.jinja.globals.update(self.spec)

    # cache #

    def write_cache(self):

        print(f':: cache_state - resetting {self.cache_dir}')
        shutil.rmtree(self.cache_dir, ignore_errors=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        #
        # cache macros
        #

        print(':: cache_state | spec.macro')
        macro_dict = {key: asdict(macro) for key, macro in self.spec['macro'].items() if isinstance(macro, MTemplateMacro)}
        macro_json_data = json.dumps(macro_dict, sort_keys=True, indent=4)

        if self.debug:
            for line in macro_json_data.splitlines():
                print('\t', line[0:135], '[...]' if len(line) > 135 else '')

        macro_cache_path = self.cache_dir / 'macro.json'
        with open(macro_cache_path, 'w+') as f:
            f.write(macro_json_data)

        print(f'\twrote {macro_cache_path}')

        #
        # cache template paths
        #

        print(':: cache_state | self.template_paths')
        
        template_paths_cache_data = copy(self.template_paths)

        # rm src key from model dicts #
        rm_src_key_from_dict = lambda m: {k: v for k, v in m.items() if k != 'src'}
        cleaned_models = map(rm_src_key_from_dict, self.template_paths['model'])
        template_paths_cache_data['model'] = list(cleaned_models)

        # filter .env file
        app = filter(lambda x: x['rel'] != '.env', self.template_paths['app'])
        template_paths_cache_data['app'] = list(app)

        json_template_paths_data = json.dumps(template_paths_cache_data, sort_keys=True, indent=4)

        if self.debug:
            for line in json_template_paths_data.splitlines():
                print('\t', line[0:135], '[...]' if len(line) > 135 else '')

        template_paths_cache_path = self.cache_dir / 'template_paths.json'
        with open(template_paths_cache_path, 'w+') as f:
            f.write(json_template_paths_data)

        print(f'\twrote {template_paths_cache_path}')


        #
        # cache jinja templates
        #

        print(':: cache_state | self.templates')

        for rel_path, template in self.templates.items():
            if rel_path.endswith('/.env') or rel_path == '.env':
                print(f'\n\t:: WARNING :: NOT CACHING: {rel_path}\n')
                continue

            cache_file_path = self.cache_dir / (rel_path + '.jinja2')
            cache_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                template.write(cache_file_path)
                print(f'\twrote -> {cache_file_path}')
            except Exception as exc:
                print(f':: error caching :: {rel_path}: {exc}')
                raise

        print(':: cache done')
    
    #
    # rendering
    #

    def write_file(self, path:Path, data:str):
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

    def render_template(self, vars:dict, rel_path:str, out_path:Path|str, rel_template:str):

        out_path = Path(out_path)
        if self.debug:
            debug_output_path = out_path.with_name(out_path.name + '.jinja2')
            self.write_file(debug_output_path, self.templates[rel_path].create_template())

        try:
            jinja_template = self.jinja.get_template(rel_path)
            rendered_template = jinja_template.render(vars)
        except TemplateError as e:
            raise TemplateError(f'{e.__class__.__name__}:{e} in template {out_path}')
        except MTemplateError as e:
            raise MTemplateError(f'{e.__class__.__name__}:{e} in template {out_path}')
        
        self.write_file(out_path, rendered_template)

    def render_templates(self, output_dir:str|Path):

        print(f':: rendering :: {self.spec["project"]["name"]["kebab_case"]} :: {self.app_name}')

        if not self.debug:
            print(f':: removing old output dir: {output_dir}')
            try:
                shutil.rmtree(output_dir, ignore_errors=True)
            except TypeError:
                raise ValueError(f'Invalid output dir')
            
        cwd = Path.cwd()
        def output_path(path:str) -> Path:
            try:
                return Path(path).relative_to(cwd)
            except ValueError:
                return Path(path)
            
        print(':: app')
        for template in self.template_paths['app']:
            app_output = output_dir / template['rel']

            print('  ', output_path(app_output))
            self.render_template({}, template['rel'], app_output, template['rel_template'])

        print(':: modules')
        for module in self.spec['modules'].values():
            print('  ', module['name']['lower_case'])
            
            for template in self.template_paths['module']:
                module_output = (output_dir / template['rel_template']).as_posix()
                module_output = module_output.replace('{{ module.name.snake_case }}', module['name']['snake_case'])
                module_output = module_output.replace('{{ module.name.kebab_case }}', module['name']['kebab_case'])
                module_output = module_output.replace('{{ module.name.pascal_case }}', module['name']['pascal_case'])
                module_output = module_output.replace('{{ module.name.camel_case }}', module['name']['camel_case'])

                print('    ', output_path(module_output))
                self.render_template({'module': module}, template['rel'], module_output, template['rel_template'])

            print('\n     models')
            for model in module['models'].values():
                print('      ', model['name']['lower_case'])

                for template in self.template_paths['model']:
                    model_output = (output_dir / template['rel_template']).as_posix()
                    model_output = model_output.replace('{{ model.name.snake_case }}', model['name']['snake_case'])
                    model_output = model_output.replace('{{ model.name.kebab_case }}', model['name']['kebab_case'])
                    model_output = model_output.replace('{{ model.name.pascal_case }}', model['name']['pascal_case'])
                    model_output = model_output.replace('{{ model.name.camel_case }}', model['name']['camel_case'])

                    model_output = model_output.replace('{{ module.name.snake_case }}', module['name']['snake_case'])
                    model_output = model_output.replace('{{ module.name.kebab_case }}', module['name']['kebab_case'])
                    model_output = model_output.replace('{{ module.name.pascal_case }}', module['name']['pascal_case'])
                    model_output = model_output.replace('{{ module.name.camel_case }}', module['name']['camel_case'])

                    print('        ', output_path(model_output))
                    self.render_template({'module': module, 'model': model}, template['rel'], model_output, template['rel_template'])

        print(f':: done :: {self.spec["project"]["name"]["kebab_case"]} :: {self.app_name}')

    #
    # ops
    #

    @classmethod
    def render(cls, spec:dict, env_file:str|Path=None, output_dir:str|Path=None, debug:bool=False, disable_strict:bool=False, use_cache:bool=True) -> 'MTemplateProject':
        """
        Render the project templates based on the provided specification.

        Parameters:
        - spec              (dict)                  The project specification.
        - env_file          (str|Path, optional)    Ignored in base class, may be implemented in a subclass.
        - output_dir        (str|Path, optional)    Directory to output the rendered templates.
        - debug             (bool, optional)        Enable debug mode.
        - disable_strict    (bool, optional)        Disable strict mode in jinja templates, only recommended for debugging.
        - use_cache         (bool, optional)        Use cached templates if available.    

        Returns:
        - MTemplateProject: The project instance
        """

        template_proj = cls(spec, debug=debug, disable_strict=disable_strict)
        
        # load tempaltes #

        if use_cache:
            template_proj.load_cached_templates()
        else:
            template_proj.extract_templates()

        template_proj.init_template_vars()

        # output #

        template_proj.render_templates(output_dir or template_proj.default_output_dir())
        return template_proj
    
    @classmethod
    def build_cache(cls, spec:dict) -> 'MTemplateProject':
        template_proj = cls(spec)
        
        # load tempaltes #
        template_proj.extract_templates()
        template_proj.init_template_vars()

        # cache state #
        template_proj.write_cache()
        return template_proj


@dataclass
class MTemplateMacro:
    """a macro extracted by the MTemplateExtractor"""

    name:str
    text:str
    vars:dict

    def __call__(self, *args, **kwargs):
        return self.render(*args, **kwargs)
    
    def render(self, values:dict) -> str:
        # the keys in self.vars are the string in the template that will be replaced by the 
        # variable/macro arg which is defined in the value of the dict
        output = copy(self.text)
        for template_value, input_key in sort_dict_by_key_length(self.vars).items():
            try:
                output = output.replace(template_value, values[input_key])
            except KeyError:
                raise MTemplateError(f'{input_key} not given to macro {self.name}')
        return output


class MTemplateExtractor:
    """extract a jinja template from a source file"""

    def __init__(self, path:str|Path, prefix='#', postfix='', single_quotes=False, emit_syntax=False) -> None:
        self.path = Path(path)
        self.prefix = prefix
        self.postfix = postfix
        self.single_quotes = single_quotes
        self.template = ''
        self.template_lines = []
        self.template_vars = {}
        self.macros = {}
        self.emit_syntax = emit_syntax

    def _load_json(self, data:str):
        if self.single_quotes:
            return json.loads(data.replace("'", '"'))
        else:
            return json.loads(data)

    def _parse_vars_line(self, line:str):
        try:
            vars_str = line.split('::')[1].strip()
            vars_decoded = self._load_json(vars_str)
            if not isinstance(vars_decoded, dict):
                raise MTemplateError(f'vars must be a object not "{type(vars_decoded).__name__}"')
            
            self.template_vars.update(vars_decoded)

        except json.JSONDecodeError as e:
            raise MTemplateError(f'JSONDecodeError:{e} in vars definition')

    def _parse_for_lines(self, definition_line:str, lines:list[str], end_for_mods:list[str]):

        # parse for loop definition #

        try:
            definition_split = definition_line.split('::')
            jinja_line = definition_split[1]

        except IndexError:
            raise MTemplateError(f'for loop definition missing jinja loop syntax')
        
        # parse block vars #

        try:
            block_vars = self._load_json(definition_split[2].strip())

        except json.JSONDecodeError:
            try:
                block_vars = eval(definition_split[2].strip())
            except Exception as e:
                raise MTemplateError(f'{e.__class__.__name__}:{e} parsing block vars')
        
        if not isinstance(block_vars, dict):
            raise MTemplateError(f'vars must be a dict not {type(block_vars).__name__}')
        
        # append lines to template #

        self.template_lines.append(jinja_line.strip() + '\n')

        for line in lines:
            new_line = line 
            for key, value in sort_dict_by_key_length(block_vars).items():
                new_line = new_line.replace(key, '{{ ' + value + ' }}')
            self.template_lines.append(new_line)
        end_for = '{% endfor %}' if 'rstrip' in end_for_mods else '{% endfor %}\n'
        self.template_lines.append(end_for)
    
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

    def create_template(self) -> str:
        template = ''.join(self.template_lines)
        for key, value in sort_dict_by_key_length(self.template_vars).items():
            template = template.replace(key, '{{ ' + value + ' }}')
        return template

    def write(self, path:str|Path):
        with open(path, 'w+') as f:
            f.write(self.create_template())

    def _emit_syntax_line(self, line:str):
        if self.emit_syntax:
            self.template_lines.append(line.replace('{%', '{::').replace('%}', '::}'))

    def parse(self):

        ignoring = False

        with open(self.path, 'r') as f:
            line_no = 0

            # iter over each line of file and parse tokens #

            for line in f:
                line_no += 1
                line_stripped = line.replace(self.postfix, '').strip()

                # vars line #

                if line_stripped.startswith(f'{self.prefix} vars :: '):
                    self._emit_syntax_line(line)
                    try:
                        self._parse_vars_line(line_stripped)
                    except MTemplateError as e:
                        raise MTemplateError(f'{e} on line {line_no} of {self.path}')

                # for loop #

                elif line_stripped.startswith(f'{self.prefix} for :: '):
                    self._emit_syntax_line(line)
                    for_lines = []
                    for_start_line_no = line_no
                    end_for_mods = []
                    end_for_line = ''

                    while True:

                        # seek ahead to each line in for loop #

                        try:
                            next_line = next(f)
                        except StopIteration:
                            raise MTemplateError(f'Unterminated for loop starting on line {for_start_line_no} of {self.path}')
                        
                        next_line_strippped = next_line.replace(self.postfix, '').strip()
                        line_no += 1
                        
                        if next_line_strippped.startswith(f'{self.prefix} end for ::'):
                            end_for_line = next_line
                            try:
                                _, mods = next_line_strippped.split('::')
                            except ValueError:
                                raise MTemplateError(f'invalid end for statement on line {line_no} of {self.path}')
                            end_for_mods.extend(mods.strip().split())
                            break

                        for_lines.append(next_line)
                    
                    try:
                        self._parse_for_lines(line_stripped, for_lines, end_for_mods)
                    except MTemplateError as e:
                        raise MTemplateError(f'{e} on line {line_no} of {self.path}')
                    
                    if end_for_line:
                        self._emit_syntax_line(end_for_line)
                
                # end for #
                
                elif line_stripped.startswith(f'{self.prefix} end for ::'):
                    raise MTemplateError(f'end for without beginning for statement on line {line_no}')
                
                # ignore lines #

                elif line_stripped.startswith(f'{self.prefix} ignore ::'):
                    self._emit_syntax_line(line)
                    ignoring = True

                elif line_stripped.startswith(f'{self.prefix} end ignore ::'):
                    self._emit_syntax_line(line)
                    ignoring = False

                # insert line #

                elif line_stripped.startswith(f'{self.prefix} insert ::'): 
                    self._emit_syntax_line(line)
                    try:
                        _, insert_stmt = line_stripped.split('::')
                    except ValueError:
                        raise MTemplateError(f'invalid insert statement on line {line_no}')
                    
                    self.template_lines.append('{{ ' + insert_stmt.strip() + ' }}\n')

                # replace lines #

                elif line_stripped.startswith(f'{self.prefix} replace ::'):
                    self._emit_syntax_line(line)
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
                        
                        next_line_strippped = next_line.replace(self.postfix, '').strip()
                        line_no += 1
                        
                        # insert replacement statement #

                        if next_line_strippped == f'{self.prefix} end replace ::':
                            self._emit_syntax_line(next_line)
                            self.template_lines.append('{{ ' + replacement_stmt.strip() + ' }}\n')
                            break
                
                # macros #

                elif line_stripped.startswith(f'{self.prefix} macro ::'):
                    self._emit_syntax_line(line)
                    macro_start_line_no = line_no
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
                                self._emit_syntax_line(next_line)
                                self._parse_macro(macro_def_line, macro_lines)
                                break
                            elif next_line_strippped.startswith(f'{self.prefix} macro ::'):
                                self._emit_syntax_line(next_line)
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
                    self._emit_syntax_line(line)
                    continue
            
                else:
                    self.template_lines.append(line)

    @classmethod
    def template_from_file(cls, path:str|Path, emit_syntax:bool=False) -> 'MTemplateExtractor':
        path = Path(path)

        if path.suffix in ['.js', '.ts']:
            prefix = '//'
            postfix = ''
            single_quotes = False
        elif path.suffix in ['.html', '.htm']:
            prefix = '<!--'
            postfix = '-->'
            single_quotes = False
        elif path.suffix == '.css':
            prefix = '/*'
            postfix = '*/'
            single_quotes = False
        elif path.suffix == '.json':
            prefix = '"_": "'
            postfix = '",'
            single_quotes = True
        else:
            prefix = '#'
            postfix = ''
            single_quotes = False

        instance = cls(path, prefix=prefix, postfix=postfix, single_quotes=single_quotes, emit_syntax=emit_syntax)
        instance.parse()
        return instance
