import unittest
from pathlib import Path
from unittest.mock import patch

LINGO_ROOT = Path(__file__).resolve().parents[1]
EXE_PARAMS_SPEC = str(LINGO_ROOT / 'shared' / 'scripts' / 'exe' / 'hello-params.yaml')
GUI_PARAMS_SPEC = str(LINGO_ROOT / 'shared' / 'scripts' / 'gui' / 'hello-gui-params.yaml')

from lingolib import cli
from lingolib.api import create_ast_from_file, execute_file
from lingolib.context import LingoContext
from lingolib.errors import LingoRuntimeError
from lingolib.runtime.registry import add_params_to_registry, init_registry
from lingolib.runtime.shared import CLIHelpMenuRequested, parse_param_json, parse_params_cli_args


class TestParamsCLIArgs(unittest.TestCase):

    def test_parses_json_params_and_interactive(self):
        self.assertEqual(parse_params_cli_args(['--json', '{}']).request_body, '{}')

        parsed = parse_params_cli_args(['--params', 'a=1', 'b=2', '-i'])
        self.assertEqual((parsed.assignments, parsed.interactive), (['a=1', 'b=2'], True))

        self.assertEqual(parse_params_cli_args([]), (None, None, False))

    def test_invalid_combinations(self):
        for args in (
            ['--json', '{}', '--params', 'a=1'],
            ['--json', '{}', '-i'],
            ['--json'],
            ['--params'],
            ['--json', '{}', '--json', '{}'],
            ['--params', 'a=1', '--params', 'b=2'],
            ['-i', '-i'],
            ['--name', 'x'],
        ):
            with self.assertRaises(LingoRuntimeError, msg=str(args)):
                parse_params_cli_args(args)

    def test_help_raises(self):
        with self.assertRaises(CLIHelpMenuRequested):
            parse_params_cli_args(['--help'])


class TestParamsRuntime(unittest.TestCase):

    def _params(self, *cli_args, spec):
        ctx = LingoContext()
        ast = create_ast_from_file(ctx, spec)
        init_registry(ctx)
        add_params_to_registry(ctx, ast.params, list(cli_args))
        return ctx.registry.params

    def test_params_assignments_apply_defaults(self):
        params = self._params('--params', 'name=Ann', 'count=3', spec=EXE_PARAMS_SPEC)
        self.assertEqual((params.name, params.count, params.is_enabled), ('Ann', 3, False))

    def test_json_params(self):
        params = self._params('--json', '{"name": "Bo", "is_enabled": true}', spec=GUI_PARAMS_SPEC)
        self.assertEqual((params.name, params.is_enabled, params.count), ('Bo', True, 0))

    def test_json_validation_errors(self):
        for body in ('{"count": 1}', '{"name": 1}', '{"name": "a", "count": true}', '{"name": "a", "x": 1}', '[]', '{}', '{bad'):
            with self.assertRaises(LingoRuntimeError, msg=body):
                self._params('--json', body, spec=EXE_PARAMS_SPEC)

    def test_json_validation_is_strict_about_types(self):
        ast = create_ast_from_file(LingoContext(), EXE_PARAMS_SPEC)
        self.assertEqual(parse_param_json(ast.params.fields, 'params', '{"count": 2}'), {'count': 2})
        with self.assertRaises(LingoRuntimeError):
            parse_param_json(ast.params.fields, 'params', '{"count": 2.5}')

    def test_missing_required_param(self):
        with self.assertRaisesRegex(LingoRuntimeError, "missing required param: 'name'"):
            self._params('--params', 'count=1', spec=EXE_PARAMS_SPEC)

    def test_interactive_prompts_only_for_missing_params_without_defaults(self):
        with patch('builtins.input', return_value='Zed') as prompt:
            params = self._params('-i', spec=EXE_PARAMS_SPEC)
        self.assertEqual(params.name, 'Zed')
        prompt.assert_called_once()

    def test_exe_runs_with_params(self):
        result = execute_file(LingoContext(), EXE_PARAMS_SPEC, cli_args=['--params', 'name=Ann'])
        self.assertIn('hello, Ann', result)


class TestParamsHelp(unittest.TestCase):

    def _help(self, command, spec):
        argv = ['lingolib', command, spec, '--help']
        with patch('lingolib.cli.sys.argv', argv), patch('builtins.print') as printed:
            cli.parse_cli(LingoContext())
        return printed.call_args_list[-1].args[0]

    def test_exe_and_display_help_list_params(self):
        for command, spec in (('exe', EXE_PARAMS_SPEC), ('display', GUI_PARAMS_SPEC)):
            output = self._help(command, spec)
            self.assertTrue(output.startswith('params:'))
            self.assertIn('    is_enabled: (bool) default=False :: A test boolean value', output)
            self.assertIn('    name:       (str) :: ', output)
