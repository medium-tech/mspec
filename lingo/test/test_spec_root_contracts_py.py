import sys
import unittest
from pathlib import Path


PY_SRC = Path(__file__).resolve().parents[1] / 'interpreters' / 'py' / 'src'
if str(PY_SRC) not in sys.path:
    sys.path.insert(0, str(PY_SRC))


from lingolib.context import LingoContext, LingoParserContext
from lingolib.errors import LingoSyntaxError
from lingolib.parsing import create_spec_ast_from_dict


class TestSpecRootContractsPython(unittest.TestCase):

    def _ctx(self) -> LingoContext:
        return LingoContext(
            parser=LingoParserContext(
                file='<memory>'
            )
        )
    
    def test_exe_well_formed_with_only_required_fields(self):
        doc = {
            'lingo': {'spec': 'exe', 'version': '0.0.1'},
            'main': {
                'type': 'str',
                'value': 'hello.world',
            },
        }

        ast = create_spec_ast_from_dict(self._ctx(), doc)

        self.assertEqual(ast.lingo.spec, 'exe')

    def test_exe_well_formed_with_all_available_fields(self):
        doc = {
            'lingo': {'spec': 'exe', 'version': '0.0.1'},
            'main': {
                'type': 'str',
                'value': 'hello.world',
            },
            'meta': {
                'name': 'hello-world',
            },
            'import': [
                {'path': './shared/lib/math.yaml'},
            ],
        }

        ast = create_spec_ast_from_dict(self._ctx(), doc)

        self.assertEqual(ast.lingo.spec, 'exe')

    def test_exe_bad_spec_unknown_root_field(self):
        doc = {
            'lingo': {'spec': 'exe', 'version': '0.0.1'},
            'main': {
                'type': 'str',
                'value': 'hello.world',
            },
            'unknown_field': 'oops',
        }

        with self.assertRaises(LingoSyntaxError) as e:
            create_spec_ast_from_dict(self._ctx(), doc)

        self.assertIn("unsupported top-level key(s) for spec 'exe': unknown_field", str(e.exception))

    def test_exe_bad_spec_missing_each_required_field(self):
        docs = {
            'missing_lingo': {
                'main': {
                    'type': 'str',
                    'value': 'hello.world',
                },
            },
            'missing_main': {
                'lingo': {'spec': 'exe', 'version': '0.0.1'},
            },
        }

        expected_errors = {
            'missing_lingo': 'missing required top-level key for all specs: lingo',
            'missing_main': "missing required top-level key(s) for spec 'exe': main",
        }

        for case_name, doc in docs.items():
            with self.subTest(case=case_name):
                with self.assertRaises(LingoSyntaxError) as e:
                    create_spec_ast_from_dict(self._ctx(), doc)

                self.assertIn(expected_errors[case_name], str(e.exception))

    def test_exe_bad_lingo_block_unknown_field(self):
        doc = {
            'lingo': {
                'spec': 'exe',
                'version': '0.0.1',
                'unknown_field': 'oops',
            },
            'main': {
                'type': 'str',
                'value': 'hello.world',
            },
        }

        with self.assertRaises(LingoSyntaxError) as e:
            create_spec_ast_from_dict(self._ctx(), doc)

        self.assertIn("unsupported key in lingo symbol: 'unknown_field'", str(e.exception))

    def test_exe_bad_lingo_block_missing_spec_field(self):
        doc = {
            'lingo': {
                'version': '0.0.1',
            },
            'main': {
                'type': 'str',
                'value': 'hello.world',
            },
        }

        with self.assertRaises(LingoSyntaxError) as e:
            create_spec_ast_from_dict(self._ctx(), doc)

        self.assertIn('error creating lingo symbol', str(e.exception))
        self.assertIn('spec', str(e.exception))

    def test_exe_bad_lingo_block_missing_version_field(self):
        doc = {
            'lingo': {
                'spec': 'exe',
            },
            'main': {
                'type': 'str',
                'value': 'hello.world',
            },
        }

        with self.assertRaises(LingoSyntaxError) as e:
            create_spec_ast_from_dict(self._ctx(), doc)

        self.assertIn('error creating lingo symbol', str(e.exception))
        self.assertIn('version', str(e.exception))

    def test_text_spec_parses_block_items(self):
        doc = {
            'lingo': {'spec': 'text', 'version': '0.0.1'},
            'block': [
                {'text': 'hello.world'},
            ],
        }

        ast = create_spec_ast_from_dict(self._ctx(), doc)

        self.assertEqual(ast.lingo.spec, 'text')
        self.assertEqual(ast.block.items[0].text.value, 'hello.world')

    def test_text_spec_bad_block(self):
        doc = {
            'lingo': {'spec': 'text', 'version': '0.0.1'},
            'block': {'text': 'hello.world'}
        }

        with self.assertRaises(LingoSyntaxError) as e:
            create_spec_ast_from_dict(self._ctx(), doc)
            self.assertIn('block symbol must be a list', str(e.exception))

    def test_text_spec_missing_block(self):
        doc = {
            'lingo': {'spec': 'text', 'version': '0.0.1'},
        }

        with self.assertRaises(LingoSyntaxError) as e:
            create_spec_ast_from_dict(self._ctx(), doc)
            self.assertIn('missing block symbol', str(e.exception))


if __name__ == '__main__':
    unittest.main()
