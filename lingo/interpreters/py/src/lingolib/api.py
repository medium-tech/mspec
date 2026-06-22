import os

from lingolib.context import LingoContext, LingoInterpreterContext
from lingolib.errors import LingoSyntaxError
from lingolib.expressions import unwrap_expression
from lingolib.parsing import LingoASTSpec, create_spec_ast_from_dict, LingoASTExeSpec, YamlLocationLoader

import yaml


def parse_file_to_dict(path):

    try:
        with open(path) as f:
            doc = yaml.load(f.read(), Loader=YamlLocationLoader)
    except yaml.YAMLError as e:
        raise LingoSyntaxError(f'failed to parse YAML file {path}: {e}')
        
    return doc

def ast_from_file(ctx: LingoContext, path: str) -> LingoASTSpec:
    doc = parse_file_to_dict(path)
    parser_ctx = LingoInterpreterContext.new_from_ctx(ctx, file=os.path.abspath(path))
    return create_spec_ast_from_dict(parser_ctx, doc)

def execute_file(ctx: LingoContext, path: str):
    lingo_ast = ast_from_file(ctx, path)
    if isinstance(lingo_ast, LingoASTExeSpec):
        return execute_exe_spec(ctx, lingo_ast)
    else:
        raise LingoSyntaxError(f'unsupported spec type: {lingo_ast.lingo.spec!r}')
    
def execute_exe_spec(ctx: LingoContext, ast: LingoASTExeSpec):
    return unwrap_expression(ctx, ast.main.expr)
