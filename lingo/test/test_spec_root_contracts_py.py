import sys
import unittest
from pathlib import Path


PY_SRC = Path(__file__).resolve().parents[1] / 'interpreters' / 'py' / 'src'
if str(PY_SRC) not in sys.path:
    sys.path.insert(0, str(PY_SRC))


from lingolib.context import LingoContext, LingoInterpreterContext
from lingolib.errors import LingoSyntaxError
from lingolib.parsing import create_spec_ast_from_dict


class TestSpecRootContractsPython(unittest.TestCase):

    def _ctx(self) -> LingoContext:
        return LingoContext(
            interpreter=LingoInterpreterContext(
                file='<memory>'
            )
        )
    
    def test_exe_still_parses_with_valid_root(self):
        doc = {
            'lingo': {'spec': 'exe', 'version': '0.0.1'},
            'main': {
                'type': 'str',
                'value': 'hello.world',
            },
        }

        ast = create_spec_ast_from_dict(self._ctx(), doc)

        self.assertEqual(ast.lingo.spec, 'exe')


if __name__ == '__main__':
    unittest.main()
