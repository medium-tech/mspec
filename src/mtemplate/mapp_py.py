import shutil
import secrets

from pathlib import Path

from mspec.core import SAMPLE_GENERATOR_SPEC_DIR, load_generator_spec
from mtemplate.core import MTemplateProject


class MappPyProject(MTemplateProject):

    app_name = 'mapp-py'
    template_dir = Path(__file__).parent.parent.parent / 'templates' / app_name
    cache_dir = Path(__file__).parent / '.cache' / app_name

    prefixes = {
        'tests/samples': 'binary',
        'app': 'ignore',
        'test-results': 'ignore',
        'mapp-tests': 'ignore',
        'playwright-report': 'ignore'
    }

    @classmethod
    def render(cls, spec_path:str, output_dir:str|Path=None, debug:bool=False, disable_strict:bool=False, use_cache:bool=True) -> 'MappPyProject':
                
        mapp_file = output_dir / 'mapp.yaml'
        
        spec = load_generator_spec(spec_path)
        spec['context'] = {
            'secret_key': secrets.token_hex(32),
            'uwsgi_static_safe': output_dir.absolute().parent,
            'mapp_spec_file': mapp_file.name
        }
        template_proj = super().render(spec, output_dir, debug, disable_strict, use_cache)

        (output_dir / '.env.example').rename(output_dir / '.env')
        print(f':: moved .env.example to .env')

        try:
            shutil.copyfile(spec_path, mapp_file)
            print(f':: copied spec file {spec_path} to {mapp_file}')

        except FileNotFoundError:
            builtin_spec = SAMPLE_GENERATOR_SPEC_DIR / spec_path
            try:
                shutil.copyfile(builtin_spec, mapp_file)
                print(f':: copied builtin spec file {builtin_spec} to {mapp_file}')
            except FileNotFoundError:
                print(f'ERROR: Could not find spec file at {spec_path} or builtin spec file at {builtin_spec}')
                raise SystemExit(1)

        return template_proj
