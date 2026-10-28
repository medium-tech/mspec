import subprocess
import sys
import unittest
from pathlib import Path


LINGO_ROOT = Path(__file__).resolve().parents[1]
APP_SPEC = LINGO_ROOT / 'shared' / 'scripts' / 'app' / 'hello-backend.yaml'
APP_SPEC_STR = str(APP_SPEC)

from lingolib.api import create_ast_from_file
from lingolib.ast import LingoASTAppSpec
from lingolib.context import LingoContext
from lingolib.symbols import L_SYM_define, L_SYM_func


class TestAppSpecParsing(unittest.TestCase):

    def test_hello_database_app_spec(self):
        path = LINGO_ROOT / 'shared' / 'scripts' / 'app' / 'hello-database.yaml'
        ast = create_ast_from_file(LingoContext(), str(path))

        module = ast.modules.members['notes']
        self.assertEqual(
            set(module.ops.funcs),
            {'create_note', 'read_note', 'list_notes', 'put_note', 'finish_note', 'delete_note'},
        )
        self.assertEqual(
            {op.func.L_SYM_NAME for op in module.ops.funcs.values()},
            {'db_create', 'db_read', 'db_list', 'db_put', 'db_patch', 'db_delete'},
        )
        note = module.models['note']
        self.assertEqual(set(note.fields), {'title', 'priority', 'done', 'rating', 'secret'})
        self.assertTrue(note.fields['secret'].secure)

    def test_hello_backend_app_spec(self):
        ast = create_ast_from_file(LingoContext(), APP_SPEC_STR)

        self.assertIsInstance(ast, LingoASTAppSpec)
        self.assertEqual(ast.imports.paths, ['../lib/hello-library.yaml'])

        module = ast.modules.members['my_app']
        say_hello = module.ops.funcs['say_hello']
        self.assertIsInstance(say_hello, L_SYM_func)
        self.assertEqual(say_hello.reference, 'hello_ns.say_hello')
        self.assertIsNone(say_hello.func)

        say_goodbye = module.ops.funcs['say_goodbye']
        self.assertIsInstance(say_goodbye, L_SYM_func)
        self.assertEqual(say_goodbye.reference, None)
        self.assertEqual(say_goodbye.args[0].name, 'name')
        self.assertEqual(say_goodbye.args[0].L_SRC, 'modules.my_app.ops.say_goodbye.args.name.define')
        self.assertIsNotNone(say_goodbye.func)
        self.assertEqual(say_goodbye.return_.type, 'str')

        person = module.models['person']
        self.assertIsInstance(person, L_SYM_define)
        self.assertEqual(person.reference, 'hello_ns.person')
        self.assertIsNone(person.type)

        post = module.models['post']
        self.assertIsInstance(post, L_SYM_define)
        self.assertEqual(post.type, 'struct')
        self.assertEqual(post.fields['title'].type, 'str')
        self.assertEqual(post.fields['message'].type, 'int')

    def test_debug_command_dumps_app_ast(self):
        result = subprocess.run(
            [sys.executable, '-m', 'lingolib', 'debug', APP_SPEC_STR],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn('L_SYM_app_module', result.stdout)
        self.assertIn("reference: 'hello_ns.say_hello'", result.stdout)
        self.assertIn("reference: 'hello_ns.person'", result.stdout)
        self.assertIn("name: 'post'", result.stdout)


if __name__ == '__main__':
    unittest.main()
