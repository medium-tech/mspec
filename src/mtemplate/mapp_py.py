import sys
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
        'tests/dev-app': 'ignore',
        'app': 'ignore',
        'test-results': 'ignore',
        'mapp-tests': 'ignore',
        'playwright-report': 'ignore'
    }

    @classmethod
    def render(cls, spec_path:str, output_dir:str|Path=None, debug:bool=False, disable_strict:bool=False, use_cache:bool=True, as_builtin:bool=False) -> 'MappPyProject':

        """Render a mapp-py project from a generator spec file.

        Args:
            spec_path: Path to the generator spec file to render from.
            output_dir: Directory to output the rendered project to.
            debug: If True, enable debug mode.
            disable_strict: If True, disable strict undefined behavior in Jinja templates.
            use_cache: If True, use cached templates if available.
            as_builtin: If True, treat the spec_path as a builtin spec and do not copy it to the output dir.

        Returns:
            An instance of MappPyProject representing the rendered project.

        Built in mode (as_builtin=True) means that the spec is not copied into the output directory, 
        so when the app starts up it will not find the spec and fallback to the builtin spec. This is
        useful for running or testing built in apps if you don't plan on changing the spec. 

        If a .env file does not exist in the output directory, this method will create one from the .env.example
        and fill out default values for the secret key, uwsgi static safe path, virtual environment path, and mapp spec file.
        """

        #
        # init template variables
        #

        if as_builtin:
            mapp_file = Path(spec_path)
        else:
            mapp_file = output_dir / 'mapp.yaml'
        
        spec = load_generator_spec(spec_path)
        spec['context'] = {
            'secret_key': 'change_me',
            'uwsgi_static_safe': '/absolute/path/to/parent/dir',
            'virtual_env': '/path/to/.venv',
            'mapp_cli_session_file': '/path/to/app/.mapp_session',
            'mapp_spec_file': mapp_file.name
        }

        #
        # render templates
        #

        template_proj = super().render(spec, output_dir, debug, disable_strict, use_cache)

        #
        # create .env file - if doesnt exist
        #

        dest_env_file = output_dir / '.env'
        if not dest_env_file.exists():
            if sys.executable.endswith('bin/python'):
                venv_path = Path(sys.executable).parent.parent
            else:
                venv_path = Path(sys.executable).parent

            env_template_vars = {
                'context': {
                    'secret_key': secrets.token_hex(32),
                    'uwsgi_static_safe': output_dir.absolute(),
                    'virtual_env': venv_path,
                    'mapp_cli_session_file': (output_dir / 'app' / '.mapp_session').absolute(),
                    'mapp_spec_file': mapp_file.name
                }
            }
            template_proj.render_template(env_template_vars, '.env.example', dest_env_file)
            print(':: created .env file from .env.example')

        #
        # copy spec file - if requested
        #

        if not as_builtin:
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
