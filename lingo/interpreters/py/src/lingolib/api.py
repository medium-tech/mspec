import yaml

from lingolib.context import LingoContext
from lingolib.errors import LingoSyntaxError
from lingolib.expressions import execute_expression
from lingolib.parsing import LingoASTSpec, create_spec_ast_from_dict, LingoASTExeSpec


def parse_file_to_dict(path):
    try:
        with open(path) as f:
            doc = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise LingoSyntaxError(f'failed to parse YAML file {path}: {e}')
        
    return doc

def ast_from_file(ctx: LingoContext, path: str) -> LingoASTSpec:
    doc = parse_file_to_dict(path)
    return create_spec_ast_from_dict(ctx, doc)

def execute_file(ctx: LingoContext, path: str):
    lingo_ast = ast_from_file(ctx, path)
    if isinstance(lingo_ast, LingoASTExeSpec):
        return execute_exe_spec(ctx, lingo_ast)
    else:
        raise LingoSyntaxError(f'unsupported spec type: {lingo_ast.lingo.spec!r}')
    
def execute_exe_spec(ctx: LingoContext, ast: LingoASTExeSpec):
    return execute_expression(ctx, ast.main.expr)

