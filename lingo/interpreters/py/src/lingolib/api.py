import os

from lingolib.context import LingoContext, LingoInterpreterContext
from lingolib.errors import LingoSyntaxError
from lingolib.parsing import (
    lingo_ast_to_string,
	create_spec_ast_from_dict, 
    YamlLocationLoader,
    LingoASTSpec, 
	LingoASTExeSpec, 
	LingoASTAppSpec, 
	LingoASTUISpec,
	LingoASTLibSpec
)
from lingolib.runtime.evaluate import evaluate_exe_spec

import yaml


def create_ast_from_file(ctx: LingoContext, path: str) -> LingoASTSpec:
    try:
        with open(path) as f:
            doc = yaml.load(f.read(), Loader=YamlLocationLoader)
    except yaml.YAMLError as e:
        raise LingoSyntaxError(f'failed to parse YAML file {path}: {e}')
    
    parser_ctx = LingoInterpreterContext.new_from_ctx(ctx, file=os.path.abspath(path))
    return create_spec_ast_from_dict(parser_ctx, doc)

# file wrappers #

def debug_file(ctx: LingoContext, path: str):
    lingo_ast = create_ast_from_file(ctx, path)
    debug_ast(ctx, lingo_ast)

def execute_file(ctx: LingoContext, path: str):
    lingo_ast = create_ast_from_file(ctx, path)
    return execute_ast(ctx, lingo_ast)

# ast commands #

def debug_ast(ctx: LingoContext, ast: LingoASTSpec):
    if isinstance(ast, LingoASTSpec):
        print(lingo_ast_to_string(ast))
    else:
        raise LingoSyntaxError(f'Cannot debug spec type: {ast.lingo.spec!r}')
    
def execute_ast(ctx: LingoContext, ast: LingoASTSpec):
    if isinstance(ast, LingoASTExeSpec):
        return evaluate_exe_spec(ctx, ast)
    else:
        raise LingoSyntaxError(f'Cannot execute spec type: {ast.lingo.spec!r}')
    
def serve_ast(ctx: LingoContext, ast: LingoASTSpec):
    if isinstance(ast, LingoASTAppSpec):
        raise NotImplementedError('app spec execution not yet implemented')
    else:
        raise LingoSyntaxError(f'Cannot serve spec type: {ast.lingo.spec!r}')

def display_ast(ctx: LingoContext, ast: LingoASTSpec):
    if isinstance(ast, LingoASTUISpec):
        raise NotImplementedError('ui spec execution not yet implemented')
    else:
        raise LingoSyntaxError(f'Cannot display spec type: {ast.lingo.spec!r}')
