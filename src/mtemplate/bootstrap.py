import shutil
from pathlib import Path

from mtemplate import MTemplateProject

import yaml


class MappBootstrapProject(MTemplateProject):

    app_name = 'mapp-bootstrap'
    template_dir = Path(__file__).parent.parent.parent / 'templates' / app_name
    cache_dir = Path(__file__).parent / '.cache' / app_name

    @classmethod
    def render(cls, spec:dict, env_file:str|Path=None, output_dir:str|Path=None, debug:bool=False, disable_strict:bool=False, use_cache:bool=True) -> 'MappBootstrapProject':
        template_proj = super().render(spec, env_file, output_dir, debug, disable_strict, use_cache)

        # env file
        if env_file is not None:
            env_file_out = Path(env_file) / '.env'
            shutil.copyfile(env_file, env_file_out)
            print(f'copied {env_file} to {env_file_out}')

        # filter non-pickable keys
        keys_to_keep = ['lingo', 'project', 'server', 'client', 'modules']
        spec_out = {k: spec[k] for k in keys_to_keep if k in spec}

        # write mapp.yaml
        mapp_file = output_dir / 'mapp.yaml'
        with open(mapp_file, 'w') as f:
            yaml.dump(spec_out, f)
            print(f'wrote mapp spec to: {mapp_file}')
        
        return template_proj
