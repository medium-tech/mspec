import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


LINGO_ROOT = Path(__file__).resolve().parents[1]
APP_SPEC = LINGO_ROOT / 'shared' / 'scripts' / 'app' / 'hello-backend.yaml'
APP_SPEC_STR = str(APP_SPEC)

from lingolib.api import execute_client_file, create_ast_from_file
from lingolib import cli
from lingolib.context import LingoContext
from lingolib.parsing import LingoASTAppSpec
from lingolib.runtime.eval_client import parse_cli_params, redact_secure_output
from lingolib.runtime.eval_server import create_wsgi_application
from lingolib.runtime.eval_server import run_server


class TestAppRuntime(unittest.TestCase):

    def test_client_calls_inline_and_imported_ops(self):
        ctx = LingoContext()
        ast = create_ast_from_file(ctx, APP_SPEC_STR)
        self.assertIsInstance(ast, LingoASTAppSpec)
        app = create_wsgi_application(ctx, ast)

        goodbye_status, goodbye = self._invoke_wsgi(
            app, '/my_app/say_goodbye', '{"name": "Ada"}'
        )
        hello_status, hello = self._invoke_wsgi(app, '/my_app/say_hello', '{}')

        self.assertEqual(goodbye_status, '200 OK')
        self.assertEqual(hello_status, '200 OK')
        self.assertEqual(goodbye, 'Goodbye, Ada! See you next time in the world of Lingo.')
        self.assertEqual(hello, 'Hello, World! Welcome to the world of Lingo.')

    def test_client_sends_json_and_decodes_response(self):
        response = MagicMock()
        response.read.return_value = b'"Hello, Ada!"'
        response_context = MagicMock()
        response_context.__enter__.return_value = response
        response_context.__exit__.return_value = False

        with patch('lingolib.runtime.eval_client.urlopen', return_value=response_context) as open_url:
            result = execute_client_file(
                LingoContext(),
                APP_SPEC_STR,
                'my_app.say_hello',
                '{"name": "Ada"}',
            )

        self.assertEqual(result, 'Hello, Ada!')
        request = open_url.call_args.args[0]
        self.assertEqual(request.full_url, 'http://127.0.0.1:8000/my_app/say_hello')
        self.assertEqual(request.data, b'{"name": "Ada"}')

    def test_params_convert_declared_types_and_run_op(self):
        ctx = LingoContext()
        ast = create_ast_from_file(ctx, APP_SPEC_STR)
        app = create_wsgi_application(ctx, ast)
        params = ['enabled=true', 'count=42', 'ratio=3.5', 'label=hello']
        parsed_params = parse_cli_params(
            ast.modules.members['my_app'].ops.funcs['echo_types'],
            params,
        )
        self.assertEqual(parsed_params, {
            'enabled': True,
            'count': 42,
            'ratio': 3.5,
            'label': 'hello',
        })
        request_body = json.dumps(parsed_params)
        status, response = self._invoke_wsgi(app, '/my_app/echo_types', request_body)

        self.assertEqual(status, '200 OK')
        self.assertEqual(response, 'true|42|3.5|hello')

    def test_params_convert_imported_op_signature(self):
        response = MagicMock()
        response.read.return_value = b'"Hello, Ada! Welcome to the world of Lingo."'
        response_context = MagicMock()
        response_context.__enter__.return_value = response
        response_context.__exit__.return_value = False

        with patch('lingolib.runtime.eval_client.urlopen', return_value=response_context) as open_url:
            execute_client_file(
                LingoContext(),
                APP_SPEC_STR,
                'my_app.say_hello',
                params=['name=Ada'],
            )

        request = open_url.call_args.args[0]
        self.assertEqual(request.data, b'{"name": "Ada"}')

    def test_interactive_params_use_input(self):
        ast = create_ast_from_file(LingoContext(), APP_SPEC_STR)
        func = ast.modules.members['my_app'].ops.funcs['echo_types']
        with patch('builtins.input', side_effect=['yes', '7', '2.5', 'hi']) as prompt, patch(
            'lingolib.runtime.eval_client.getpass'
        ) as secure_prompt:
            params = parse_cli_params(func, [], interactive=True)

        self.assertEqual(params, {
            'enabled': True,
            'count': 7,
            'ratio': 2.5,
            'label': 'hi',
        })
        self.assertEqual(prompt.call_count, 4)
        secure_prompt.assert_not_called()

    def test_interactive_secure_params_use_getpass(self):
        ast = create_ast_from_file(LingoContext(), APP_SPEC_STR)
        func = ast.modules.members['my_app'].ops.funcs['secure_test']
        with patch('builtins.input') as prompt, patch(
            'lingolib.runtime.eval_client.getpass', return_value='hidden-value'
        ) as secure_prompt:
            params = parse_cli_params(func, [], interactive=True)

        self.assertEqual(params, {'name': 'hidden-value'})
        secure_prompt.assert_called_once()
        prompt.assert_not_called()

    def test_invalid_secure_prompt_value_is_not_echoed(self):

        ast = create_ast_from_file(LingoContext(), APP_SPEC_STR)
        func = ast.modules.members['my_app'].ops.funcs['echo_types']
        func = func._replace(args=[func.args[0]._replace(secure=True), *func.args[1:]])

        with patch('builtins.input', side_effect=['7', '2.5', 'hi']), patch(
            'lingolib.runtime.eval_client.getpass',
            side_effect=['not-a-bool', 'yes'],
        ), patch('builtins.print') as print_output:
            params = parse_cli_params(func, [], interactive=True)

        # not-a-bool is an invalid value, but also secure
        # make sure that we don't print it in the error message
        self.assertTrue(params['enabled'])
        self.assertNotIn('not-a-bool', str(print_output.call_args_list))

    def test_secure_response_fields_are_redacted_by_default(self):
        ctx = LingoContext()
        ast = create_ast_from_file(ctx, APP_SPEC_STR)
        func = ast.modules.members['my_app'].ops.funcs['secure_test']
        response = {'name': 'Ada', 'token': 'private-token'}

        self.assertEqual(
            redact_secure_output(response, func.return_),
            {'name': 'Ada', 'token': 'REDACTED'},
        )
        self.assertEqual(
            redact_secure_output(response, func.return_, show=True),
            {'name': 'Ada', 'token': 'private-token'},
        )

    def test_api_redacts_secure_output_unless_show_requested(self):
        raw_profile = {'name': 'Ada', 'token': 'private-token'}
        with patch('lingolib.runtime.eval_client.call_op', return_value=raw_profile):
            redacted = execute_client_file(
                LingoContext(),
                APP_SPEC_STR,
                'my_app.secure_test',
                request_body='{}',
            )
            shown = execute_client_file(
                LingoContext(),
                APP_SPEC_STR,
                'my_app.secure_test',
                request_body='{}',
                show_secure=True,
            )

        self.assertEqual(redacted, {'name': 'Ada', 'token': 'REDACTED'})
        self.assertEqual(shown, {'name': 'Ada', 'token': 'private-token'})

    def test_client_cli_accepts_individual_params(self):
        argv = [
            'lingolib', 'client', APP_SPEC_STR,
            '--op', 'my_app.echo_types',
            '--params', 'enabled=yes', 'count=4', 'ratio=0.25', 'label=hello',
        ]
        with patch('lingolib.cli.sys.argv', argv), patch(
            'lingolib.cli.execute_client_file', return_value='ok'
        ) as call, patch('lingolib.cli.print_response'):
            cli.parse_cli(LingoContext())

        self.assertEqual(
            call.call_args.kwargs['params'], 
            ['enabled=yes', 'count=4', 'ratio=0.25', 'label=hello']
        )

    def test_client_cli_accepts_interactive_and_show_flags(self):
        argv = [
            'lingolib', 'client', APP_SPEC_STR,
            '--op', 'my_app.echo_types', '-i', '--show',
        ]
        with patch('lingolib.cli.sys.argv', argv), patch(
            'lingolib.cli.execute_client_file', return_value='ok'
        ) as call, patch('lingolib.cli.print_response'):
            cli.parse_cli(LingoContext())

        self.assertIsNone(call.call_args.kwargs['params'])
        self.assertTrue(call.call_args.kwargs['interactive'])
        self.assertTrue(call.call_args.kwargs['show_secure'])

    def test_server_launcher_uses_environment_configuration(self):
        with patch.dict(os.environ, {
            'LINGO_SERVER_HOST': '0.0.0.0',
            'LINGO_SERVER_PORT': '8123',
            'LINGO_SERVER_PROCESSES': '2',
            'LINGO_SERVER_LOG_MAX_SIZE': '2048',
        }), patch(
            'lingolib.runtime.eval_server.shutil.which',
            return_value='/usr/bin/uwsgi',
        ), patch('lingolib.runtime.eval_server.subprocess.run') as run:
            run_server(APP_SPEC_STR)

        command = run.call_args.args[0]
        self.assertIn('--http', command)
        self.assertIn('0.0.0.0:8123', command)
        self.assertIn('2', command)
        self.assertEqual(command[command.index('--log-maxsize') + 1], '2048')
        self.assertEqual(
            run.call_args.kwargs['env']['LINGO_APP_SPEC_FILE'],
            str(APP_SPEC.resolve()),
        )

    @staticmethod
    def _invoke_wsgi(app, path: str, body: str):
        body_bytes = body.encode('utf-8')
        environ = {
            'REQUEST_METHOD': 'POST',
            'PATH_INFO': path,
            'CONTENT_LENGTH': str(len(body_bytes)),
            'wsgi.input': io.BytesIO(body_bytes),
        }
        response_details = {}

        def start_response(status, headers):
            response_details['status'] = status
            response_details['headers'] = headers

        response = b''.join(app(environ, start_response))
        return response_details['status'], json.loads(response)


if __name__ == '__main__':
    unittest.main()
