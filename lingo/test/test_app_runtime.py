import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


LINGO_ROOT = Path(__file__).resolve().parents[1]
APP_SPEC = LINGO_ROOT / 'shared' / 'scripts' / 'app' / 'hello-backend.yaml'
APP_SPEC_STR = str(APP_SPEC)
DB_SPEC_STR = str(LINGO_ROOT / 'shared' / 'scripts' / 'app' / 'hello-database.yaml')

from lingolib.api import execute_client_file, create_ast_from_file
from lingolib import cli
from lingolib.context import LingoContext
from lingolib.parsing import LingoASTAppSpec
from lingolib.errors import LingoRuntimeError, LingoSyntaxError
from lingolib.runtime.eval_client import ClientModelRequest, parse_cli_params, redact_secure_output
from lingolib.runtime.eval_server import create_wsgi_application
from lingolib.runtime.eval_server import evaluate_server_spec


def _invoke_wsgi_full(app, path: str, body: str = '', method: str = 'POST', query: str = ''):
    body_bytes = body.encode('utf-8')
    environ = {
        'REQUEST_METHOD': method,
        'PATH_INFO': path,
        'QUERY_STRING': query,
        'CONTENT_LENGTH': str(len(body_bytes)),
        'wsgi.input': io.BytesIO(body_bytes),
    }
    response_details = {}

    def start_response(status, headers):
        response_details['status'] = status
        response_details['headers'] = headers

    response = b''.join(app(environ, start_response))
    return response_details['status'], json.loads(response), dict(response_details['headers'])


class TestAppRuntime(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db_file = str(Path(self.tmp.name) / 'test.db')

    def _make_app(self, ctx, ast):
        return create_wsgi_application(ctx, ast, db_file=self.db_file)

    def test_client_calls_inline_and_imported_ops(self):
        ctx = LingoContext()
        ast = create_ast_from_file(ctx, APP_SPEC_STR)
        self.assertIsInstance(ast, LingoASTAppSpec)
        app = self._make_app(ctx, ast)

        goodbye_status, goodbye, _ = _invoke_wsgi_full(
            app, '/my_app/say_goodbye', '{"name": "Ada"}'
        )
        hello_status, hello, _ = _invoke_wsgi_full(app, '/my_app/say_hello', '{}')

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
        app = self._make_app(ctx, ast)
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
        status, response, _ = _invoke_wsgi_full(app, '/my_app/echo_types', request_body)

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
            'LINGO_SERVER_DB_FILE': self.db_file,
        }), patch(
            'lingolib.runtime.eval_server.shutil.which',
            return_value='/usr/bin/uwsgi',
        ), patch('lingolib.runtime.eval_server.subprocess.run') as run:
            ctx = LingoContext()
            evaluate_server_spec(ctx, create_ast_from_file(ctx, APP_SPEC_STR))

        command = run.call_args.args[0]
        self.assertIn('--http', command)
        self.assertIn('0.0.0.0:8123', command)
        self.assertIn('2', command)
        self.assertEqual(command[command.index('--log-maxsize') + 1], '2048')
        self.assertEqual(
            run.call_args.kwargs['env']['LINGO_APP_SPEC_FILE'],
            str(APP_SPEC.resolve()),
        )


class TestAppModels(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db_file = str(Path(tmp.name) / 'test.db')
        self.ctx = LingoContext()
        self.app = self._app(DB_SPEC_STR)
        self.call = lambda path, body='', method='POST', query='': _invoke_wsgi_full(
            self.app, path, body, method, query
        )[:2]

    def _app(self, spec_path):
        ctx = LingoContext()
        return create_wsgi_application(ctx, create_ast_from_file(ctx, spec_path), db_file=self.db_file)

    def _create(self, **overrides):
        data = {'title': 'a', 'priority': 1, 'done': False, 'rating': 1.5, 'secret': 's'}
        data.update(overrides)
        status, created = self.call('/notes/note', json.dumps(data))
        self.assertEqual(status, '201 Created')
        return created

    def test_create_and_read(self):
        created = self._create()
        self.assertEqual(set(created), {'id', 'title', 'priority', 'done', 'rating', 'secret'})
        self.assertEqual(self.call(f'/notes/note/{created["id"]}', method='GET'), ('200 OK', created))

    def test_create_applies_defaults(self):
        status, created = self.call('/notes/note', '{"title": "t", "rating": 2.0, "secret": "x"}')
        self.assertEqual(status, '201 Created')
        self.assertEqual(created['priority'], 0)
        self.assertEqual(created['done'], False)

    def test_create_validation_errors(self):
        cases = (
            (
                '{"title": "t", "rating": 2.0}',
                "missing field 'secret'",
            ),
            (
                '{"title": 5, "rating": 2.0, "secret": "x"}',
                "field 'title': expected 'str', got int",
            ),
            (
                '{"title": "t", "rating": 2, "secret": "x"}',
                "field 'rating': expected 'float', got int",
            ),
            (
                '{"title": "t", "rating": 2.0, "secret": "x", "extra": 1}',
                'extra fields not defined in struct: extra',
            ),
            (
                '{"title": "t", "rating": 2.0, "secret": "x", "done": 1}',
                "field 'done': expected 'bool', got int",
            ),
        )

        for body, expected_error in cases:
            with self.subTest(expected_error=expected_error):
                status, payload = self.call('/notes/note', body)
                self.assertEqual(status, '400 Bad Request')
                self.assertEqual(payload['code'], 'VALIDATION_ERROR')
                self.assertEqual(payload['error'], expected_error)

    def test_malformed_body_is_400(self):
        self.assertEqual(self.call('/notes/note', '[1]')[0], '400 Bad Request')
        self.assertEqual(self.call('/notes/note', '{nope')[0], '400 Bad Request')

    def test_list_with_paging(self):
        for index in range(3):
            self._create(title=f'n{index}')
        status, page = self.call('/notes/note', method='GET', query='offset=1&limit=1')
        self.assertEqual(status, '200 OK')
        self.assertEqual(page['total'], 3)
        self.assertEqual([item['title'] for item in page['items']], ['n1'])

    def test_list_rejects_bad_query(self):
        cases = (
            ('limit=0', 'limit must be an int between 1 and 1000, got 0'),
            ("limit=abc", "query parameter 'limit' must be an int, got 'abc'"),
            ('offset=-1', 'offset must be an int >= 0, got -1'),
            ('other=1', 'unsupported query parameter(s): other'),
            ('limit=1&limit=2', "query parameter 'limit' may only be specified once"),
        )

        for query, expected_error in cases:
            with self.subTest(query=query):
                status, payload = self.call('/notes/note', method='GET', query=query)
                self.assertEqual(status, '400 Bad Request')
                self.assertEqual(payload['error'], expected_error)

    def test_put_replaces_and_validates(self):
        created = self._create()
        path = f'/notes/note/{created["id"]}'

        # updates when full body is supplied
        body = {'title': 'new', 'priority': 9, 'done': True, 'rating': 0.5, 'secret': 'y'}
        status, replaced = self.call(path, json.dumps(body), method='PUT')
        self.assertEqual(status, '200 OK')
        self.assertEqual(replaced, {'id': created['id'], **body})
        
        # GET to confirm update
        status, got = self.call(path, method='GET')
        self.assertEqual(status, '200 OK')
        self.assertEqual(got, {'id': created['id'], **body})

        # errors for a partial update (must use PATCH for partials)
        self.assertEqual(self.call(path, '{"title": "only"}', method='PUT')[0], '400 Bad Request')

    def test_patch_updates_subset(self):
        created = self._create()
        path = f'/notes/note/{created["id"]}'
        
        # updates subset
        status, patched = self.call(path, '{"done": true}', method='PATCH')
        self.assertEqual(status, '200 OK')
        self.assertEqual(patched, {**created, 'done': True})

        # GET to confirm update
        status, got = self.call(path, method='GET')
        self.assertEqual(status, '200 OK')
        self.assertEqual(got, {**created, 'done': True})

        # invalid patches #

        # wrong type for done
        validation_error = self.call(path, '{"done": "yes"}', method='PATCH')
        self.assertEqual(validation_error[0], '400 Bad Request')
        self.assertEqual(validation_error[1], {'error': "field 'done': expected 'bool', got str", 'code': 'VALIDATION_ERROR'})

        unknown_field = self.call(path, '{"nope": 1}', method='PATCH')
        self.assertEqual(unknown_field[0], '400 Bad Request')
        self.assertEqual(unknown_field[1], {'error': 'extra fields not defined in struct: nope', 'code': 'VALIDATION_ERROR'})

        empty = self.call(path, '{}', method='PATCH')
        self.assertEqual(empty[0], '400 Bad Request')
        self.assertEqual(empty[1], {'error': 'patch requires at least one field', 'code': 'VALIDATION_ERROR'})

    def test_delete_returns_object_then_404(self):
        created = self._create()
        path = f'/notes/note/{created["id"]}'
        self.assertEqual(self.call(path, method='DELETE'), ('200 OK', created))
        for method in ('GET', 'DELETE'):
            status, payload = self.call(path, method=method)
            self.assertEqual(status, '404 Not Found')
            self.assertEqual(payload['code'], 'DB_NOT_FOUND')
        self.assertEqual(self.call(path, '{"done": true}', method='PATCH')[0], '404 Not Found')

    def test_method_and_route_errors(self):
        status, _, headers = _invoke_wsgi_full(self.app, '/notes/note', method='DELETE')
        self.assertEqual(status, '405 Method Not Allowed')
        self.assertEqual(headers['Allow'], 'GET, POST')
        self.assertEqual(self.call('/notes/create_note', method='GET')[0], '405 Method Not Allowed')
        self.assertEqual(self.call('/notes/missing', method='GET')[0], '404 Not Found')
        self.assertEqual(self.call('/notes', method='GET')[0], '404 Not Found')

    def test_db_state_persists_across_apps(self):
        created = self._create()
        other = self._app(DB_SPEC_STR)

        # uwsgi was already invoked with self.setUp, now start another to confirm db state persists
        status, payload, _ = _invoke_wsgi_full(other, f'/notes/note/{created["id"]}', method='GET')
        self.assertEqual(payload, created)

    def test_ops_reuse_db_functions(self):
        status, created = self.call('/notes/create_note', '{}')
        self.assertEqual(status, '200 OK')
        item_id = created['id']
        self.assertEqual(self.call('/notes/read_note', json.dumps({'id': item_id}))[1], created)
        self.assertEqual(self.call('/notes/list_notes', '{}')[1]['total'], 1)
        self.assertEqual(self.call('/notes/finish_note', json.dumps({'id': item_id}))[1]['done'], True)
        self.assertEqual(self.call('/notes/put_note', json.dumps({'id': item_id}))[1]['title'], 'Replaced')
        self.assertEqual(self.call('/notes/delete_note', json.dumps({'id': item_id}))[1]['id'], item_id)
        status, payload = self.call('/notes/read_note', json.dumps({'id': item_id}))
        self.assertEqual((status, payload['code']), ('404 Not Found', 'DB_NOT_FOUND'))

    def test_backend_create_sample_with_library_model(self):
        app = self._app(APP_SPEC_STR)
        status, created, _ = _invoke_wsgi_full(app, '/my_app/create_sample', '{}')
        self.assertEqual(status, '200 OK')
        self.assertEqual((created['name'], created['age']), ('Maria', 30))
        status, fetched, _ = _invoke_wsgi_full(app, f'/my_app/person/{created["id"]}', method='GET')
        self.assertEqual(fetched, created)

    def test_startup_rejects_non_scalar_model_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / 'bad.yaml'
            spec.write_text(
                "lingo:\n    spec: 'app'\n    version: '0.1.0b'\n"
                "modules:\n    m:\n        models:\n            thing:\n"
                "                define: struct\n                fields:\n"
                "                    tags:\n                        define: list\n"
                "                        element_type: str\n"
            )
            with self.assertRaisesRegex(LingoRuntimeError, 'only scalar types are supported'):
                self._app(str(spec))

    def test_lingo_spec_route_serves_original_yaml(self):
        app = self._app(APP_SPEC_STR)
        environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/lingo/spec', 'QUERY_STRING': '', 'wsgi.input': io.BytesIO(b'')}
        captured = {}
        body = b''.join(app(environ, lambda status, headers: captured.update(status=status, headers=dict(headers))))
        self.assertEqual(captured['status'], '200 OK')
        self.assertEqual(captured['headers']['Content-Type'], 'application/yaml; charset=utf-8')
        self.assertEqual(body, APP_SPEC.read_bytes())

        status, payload, headers = _invoke_wsgi_full(app, '/lingo/spec', method='POST')
        self.assertEqual((status, headers['Allow']), ('405 Method Not Allowed', 'GET'))

    def test_startup_rejects_lingo_module_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / 'bad.yaml'
            spec.write_text("lingo:\n    spec: 'app'\n    version: '0.1.0b'\nmodules:\n    lingo:\n        models: {}\n")
            with self.assertRaisesRegex(LingoRuntimeError, "module name 'lingo' is reserved"):
                self._app(str(spec))

    def test_client_fetches_and_prints_spec(self):
        argv = ['lingolib', 'client', APP_SPEC_STR, '--lingo', 'spec']
        with patch('lingolib.cli.sys.argv', argv), patch(
            'lingolib.cli.fetch_server_spec', return_value='lingo:\n'
        ), patch('builtins.print') as printed:
            cli.parse_cli(LingoContext())
        printed.assert_called_once_with('lingo:\n', end='')

    def test_startup_rejects_op_model_name_clash(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / 'bad.yaml'
            spec.write_text(
                "lingo:\n    spec: 'app'\n    version: '0.1.0b'\n"
                "modules:\n    m:\n        ops:\n            thing:\n"
                "                args: {}\n                return:\n                    define: str\n"
                "                func: 'x'\n"
                "        models:\n            thing:\n                define: struct\n"
                "                fields:\n                    a:\n                        define: str\n"
            )
            with self.assertRaisesRegex(LingoRuntimeError, "module 'm' defines both an op and a model named 'thing'"):
                self._app(str(spec))

    def test_client_model_requests(self):
        def run(model_request, **kwargs):
            response = MagicMock()
            response.read.return_value = kwargs.pop('payload', b'{}')
            context = MagicMock()
            context.__enter__.return_value = response
            context.__exit__.return_value = False
            with patch('lingolib.runtime.eval_client.urlopen', return_value=context) as open_url:
                result = execute_client_file(LingoContext(), DB_SPEC_STR, None, model_request=model_request, **kwargs)
            return result, open_url.call_args.args[0]

        result, request = run(ClientModelRequest('notes.note', 'create'), params=['title=t', 'rating=1.5', 'secret=x'])
        self.assertEqual((request.get_method(), request.full_url), ('POST', 'http://127.0.0.1:8000/notes/note'))
        self.assertEqual(json.loads(request.data), {'title': 't', 'rating': 1.5, 'secret': 'x'})
        self.assertEqual(result, {})

        result, request = run(ClientModelRequest('notes.note', 'get', item_id='abc'), payload=b'{"id": "abc", "secret": "x"}')
        self.assertEqual((request.get_method(), request.full_url), ('GET', 'http://127.0.0.1:8000/notes/note/abc'))
        self.assertEqual(result, {'id': 'abc', 'secret': 'REDACTED'})

        result, request = run(
            ClientModelRequest('notes.note', 'list', offset=2, limit=5),
            payload=b'{"items": [{"secret": "x"}], "total": 1}',
        )
        self.assertEqual(request.full_url, 'http://127.0.0.1:8000/notes/note?offset=2&limit=5')
        self.assertEqual(result['items'], [{'secret': 'REDACTED'}])

        result, request = run(ClientModelRequest('notes.note', 'patch', item_id='abc'), request_body='{"done": true}')
        self.assertEqual((request.get_method(), request.full_url), ('PATCH', 'http://127.0.0.1:8000/notes/note/abc'))
        self.assertEqual(json.loads(request.data), {'done': True})

        result, request = run(ClientModelRequest('notes.note', 'delete', item_id='abc'))
        self.assertEqual((request.get_method(), request.full_url), ('DELETE', 'http://127.0.0.1:8000/notes/note/abc'))

    def test_client_model_request_errors(self):
        ctx = LingoContext()
        with self.assertRaises(LingoSyntaxError):
            execute_client_file(ctx, DB_SPEC_STR, None, model_request=ClientModelRequest('notes.nope', 'list'))
        with self.assertRaises(LingoSyntaxError):
            execute_client_file(ctx, DB_SPEC_STR, None, model_request=ClientModelRequest('notes.note', 'get', item_id='a'), request_body='{}')
        with self.assertRaises(LingoSyntaxError):
            execute_client_file(ctx, DB_SPEC_STR, 'notes.create_note', model_request=ClientModelRequest('notes.note', 'list'))
        with self.assertRaises(LingoRuntimeError):
            execute_client_file(ctx, DB_SPEC_STR, None, model_request=ClientModelRequest('notes.note', 'create'), params=['bogus=1'])

    def test_client_help_lists_app_spec(self):
        argv = ['lingolib', 'client', APP_SPEC_STR, '--help']
        with patch('lingolib.cli.sys.argv', argv), patch('builtins.print') as printed:
            cli.parse_cli(LingoContext())
        output = printed.call_args_list[-1].args[0]
        self.assertIn('title: Hello Backend', output)
        self.assertIn('my_app.say_hello', output)
        self.assertIn('my_app.person', output)

    def _help_output(self, *args):
        argv = ['lingolib', 'client', APP_SPEC_STR, *args, '--help']
        with patch('lingolib.cli.sys.argv', argv), patch('builtins.print') as printed:
            cli.parse_cli(LingoContext())
        return printed.call_args_list[-1].args[0]

    def test_client_help_describes_op(self):
        output = self._help_output('--op', 'my_app.say_goodbye')
        self.assertIn('name: my_app.say_goodbye', output)
        self.assertIn('description: Say goodbye to a person.', output)
        self.assertIn("name: (str) default='World' :: The name to bid farewell.", output)
        self.assertIn('say_goodbye.return: (str) :: A farewell message.', output)

    def test_client_help_describes_model(self):
        output = self._help_output('--model', 'my_app.person')
        self.assertIn('name: my_app.person', output)
        self.assertIn('age: (int)', output)

    def test_client_help_unknown_op_or_missing_value(self):
        with self.assertRaisesRegex(LingoSyntaxError, "op not found in app spec: 'my_app.nope'"):
            self._help_output('--op', 'my_app.nope')
        with self.assertRaisesRegex(cli.LingoCLIParseError, '--op requires a value'):
            self._help_output('--op')

    def _parse_cli(self, *args):
        argv = ['lingolib', 'client', DB_SPEC_STR, *args]
        with patch('lingolib.cli.sys.argv', argv), patch(
            'lingolib.cli.execute_client_file', return_value='ok'
        ) as call, patch('lingolib.cli.print_response'):
            cli.parse_cli(LingoContext())
        return call.call_args

    def test_cli_model_actions(self):
        call = self._parse_cli('--model', 'notes.note', '--list', '--offset', '1', '--limit', '2')
        self.assertEqual(call.kwargs['model_request'], ClientModelRequest('notes.note', 'list', None, 1, 2))
        self.assertIsNone(call.args[2])

        call = self._parse_cli('--model', 'notes.note', '--get', 'abc')
        self.assertEqual(call.kwargs['model_request'], ClientModelRequest('notes.note', 'get', 'abc'))

        call = self._parse_cli('--model', 'notes.note', '--patch', 'abc', '--json', '{"done": true}')
        self.assertEqual(call.kwargs['model_request'].action, 'patch')

        call = self._parse_cli('--model', 'notes.note', '--create', '--params', 'title=t')
        self.assertEqual(call.kwargs['params'], ['title=t'])

    def test_cli_model_option_errors(self):
        for args in (
            ('--model', 'notes.note'),
            ('--model', 'notes.note', '--list', '--get', 'a'),
            ('--model', 'notes.note', '--create'),
            ('--model', 'notes.note', '--patch', 'a'),
            ('--model', 'notes.note', '--patch', 'a', '-i'),
            ('--model', 'notes.note', '--get', 'a', '--json', '{}'),
            ('--model', 'notes.note', '--get', 'a', '--limit', '1'),
            ('--model', 'notes.note', '--list', '--limit', 'x'),
            ('--model', 'notes.note', '--op', 'notes.create_note', '--list'),
            ('--op', 'notes.create_note', '--list'),
            ('--list',),
        ):
            with self.assertRaises(cli.LingoCLIParseError, msg=str(args)):
                self._parse_cli(*args)


if __name__ == '__main__':
    unittest.main()
