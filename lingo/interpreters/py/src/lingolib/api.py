from lingolib.context import LingoContext
from lingolib.errors import LingoSyntaxError
from lingolib.parsing import (
    lingo_ast_to_string,
    create_ast_from_file,
    LingoASTSpec, 
    LingoASTExeSpec, 
    LingoASTAppSpec, 
    LingoASTGUISpec,
    LingoASTTextSpec
)

from lingolib.runtime.eval_lingo import (
    evaluate_exe_spec,
    evaluate_text_spec,
    evaluate_gui_spec,
    evaluate_client_spec,
    evaluate_server_spec
)

from lingolib.runtime.eval_client import ClientModelRequest

# file wrappers #

def debug_file(ctx: LingoContext, path: str):
    lingo_ast = create_ast_from_file(ctx, path)
    debug_ast(ctx, lingo_ast)

def execute_file(ctx: LingoContext, path: str, cli_args: list[str] = []):
    lingo_ast = create_ast_from_file(ctx, path)
    return execute_ast(ctx, lingo_ast, cli_args=cli_args)

def display_file(ctx: LingoContext, path: str, cli_args: list[str] = []):
    lingo_ast = create_ast_from_file(ctx, path)
    return display_ast(ctx, lingo_ast, cli_args=cli_args)

def serve_file(ctx: LingoContext, path: str):
    app_ast = create_ast_from_file(ctx, path)
    return serve_ast(ctx, app_ast)

def execute_client_file(
    ctx: LingoContext,
    path: str,
    op_reference: str | None,
    request_body: str | None = None,
    params: list[str] | None = None,
    interactive: bool = False,
    show_secure: bool = False,
    model_request: ClientModelRequest | None = None,
):
    app_ast = create_ast_from_file(ctx, path)
    return execute_client_ast(
        ctx,
        app_ast,
        op_reference,
        request_body=request_body,
        params=params,
        interactive=interactive,
        show_secure=show_secure,
        model_request=model_request,
    )

# ast commands #

def debug_ast(ctx: LingoContext, ast: LingoASTSpec):
    if isinstance(ast, LingoASTSpec):
        print(lingo_ast_to_string(ast))
    else:
        raise LingoSyntaxError(f'Cannot debug spec type: {ast.lingo.spec!r}')
    
def execute_ast(ctx: LingoContext, ast: LingoASTSpec, cli_args: list[str] = []):
    if isinstance(ast, LingoASTExeSpec):
        return evaluate_exe_spec(ctx, ast, cli_args=cli_args)
    else:
        raise LingoSyntaxError(f'Cannot execute spec type: {ast.lingo.spec!r}')
    
def serve_ast(ctx: LingoContext, ast: LingoASTSpec):
    if isinstance(ast, LingoASTAppSpec):
        return evaluate_server_spec(ctx, ast)
    else:
        raise LingoSyntaxError(f'Cannot serve spec type: {ast.lingo.spec!r}')

def execute_client_ast(
    ctx: LingoContext,
    ast: LingoASTSpec,
    op_reference: str | None,
    request_body: str | None = None,
    params: list[str] | None = None,
    interactive: bool = False,
    show_secure: bool = False,
    model_request: ClientModelRequest | None = None,
):
    if isinstance(ast, LingoASTAppSpec):
        return evaluate_client_spec(
            ctx,
            ast,
            op_reference,
            request_body=request_body,
            params=params,
            interactive=interactive,
            show_secure=show_secure,
            model_request=model_request,
        )
    else:
        raise LingoSyntaxError(f'Cannot run client for spec type: {ast.lingo.spec!r}')

def display_ast(ctx: LingoContext, ast: LingoASTSpec, cli_args: list[str] = []):
    if isinstance(ast, LingoASTTextSpec):
        evaluate_text_spec(ctx, ast)
    elif isinstance(ast, LingoASTGUISpec):
        evaluate_gui_spec(ctx, ast, cli_args)
    else:
        raise LingoSyntaxError(f'Cannot display spec type: {ast.lingo.spec!r}')
