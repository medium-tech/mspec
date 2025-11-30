import shutil
import secrets

from pathlib import Path

from mspec.core import SAMPLE_GENERATOR_SPEC_DIR
from mtemplate import MTemplateProject

import yaml


class MappPyProject(MTemplateProject):

    app_name = 'mapp-py'
    template_dir = Path(__file__).parent.parent.parent / 'templates' / app_name
    cache_dir = Path(__file__).parent / '.cache' / app_name

    @classmethod
    def render(cls, spec:dict, env_file:str|Path=None, output_dir:str|Path=None, debug:bool=False, disable_strict:bool=False, use_cache:bool=True, **kwargs) -> 'MappPyProject':
        spec['context'] = {
            'secret_key': secrets.token_hex(32),
            'uwsgi_static_safe': output_dir.absolute().parent
        }
        template_proj = super().render(spec, env_file, output_dir, debug, disable_strict, use_cache)

        try:
            spec_file = kwargs['spec_file']
        except KeyError:
            raise ValueError('spec_file argument is required for MappBootstrapProject.render()')

        # env file #

        # if env_file is not None:
        #     env_file_out = Path(env_file)
        #     shutil.copyfile(env_file, env_file_out)
        #     print(f'copied {env_file} to {env_file_out}')

        # copy spec file #

        (output_dir / '.env.example').rename(output_dir / '.env')
        print(f':: moved .env.example to .env')

        mapp_file = output_dir / 'mapp.yaml'

        try:
            shutil.copyfile(spec_file, mapp_file)
            print(f':: copied spec file {spec_file} to {mapp_file}')

        except FileNotFoundError:
            builtin_spec = SAMPLE_GENERATOR_SPEC_DIR / spec_file
            try:
                shutil.copyfile(builtin_spec, mapp_file)
                print(f':: copied builtin spec file {builtin_spec} to {mapp_file}')
            except FileNotFoundError:
                raise
                # raise FileNotFoundError(f'Could not find spec file at {spec_file} or builtin spec file at {builtin_spec}')

        return template_proj
