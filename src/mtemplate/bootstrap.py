import shutil
from pathlib import Path

from mspec.core import sample_generator_spec_dir
from mtemplate import MTemplateProject

import yaml


class MappBootstrapProject(MTemplateProject):

    app_name = 'mapp-bootstrap'
    template_dir = Path(__file__).parent.parent.parent / 'templates' / app_name
    cache_dir = Path(__file__).parent / '.cache' / app_name

    @classmethod
    def render(cls, spec_file:str, spec:dict, env_file:str|Path=None, output_dir:str|Path=None, debug:bool=False, disable_strict:bool=False, use_cache:bool=True) -> 'MappBootstrapProject':
        template_proj = super().render(spec, env_file, output_dir, debug, disable_strict, use_cache)

        # env file #

        if env_file is not None:
            env_file_out = Path(env_file) / '.env'
            shutil.copyfile(env_file, env_file_out)
            print(f'copied {env_file} to {env_file_out}')

        # copy spec file #

        mapp_file = output_dir / 'mapp.yaml'

        try:
            shutil.copyfile(spec_file, mapp_file)
            print(f'copied spec file {spec_file} to {mapp_file}')

        except FileNotFoundError:
            builtin_spec = sample_generator_spec_dir / spec_file
            try:
                shutil.copyfile(builtin_spec, mapp_file)
                print(f'copied builtin spec file {builtin_spec} to {mapp_file}')
            except FileNotFoundError:
                raise FileNotFoundError(f'Could not find spec file at {spec_file} or builtin spec file at {builtin_spec}')

        return template_proj
