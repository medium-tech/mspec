import sys

from itertools import takewhile

from lingolib.api import execute_file, ast_from_file
from lingolib.context import LingoContext
from lingolib.expressions import L_EXPR_str, L_EXPR_handle
from lingolib.parsing import create_expression_ast, lingo_ast_to_string
from lingolib.symbols import L_SYM_str, L_SYM_handle

HELP = (
    'usage: lingolib [--help] <command> [args]\n'
    '\n'
    'commands:\n'
    '  exe <path>    load, parse, execute an exe spec and print result\n'
    '  ast <path>    load, parse, print the AST for a spec\n'
    '\n'
    'supported specs: exe\n'
)

class LingoCLIParseError(Exception):
    pass


def parse_cli(ctx: LingoContext):
    args = sys.argv[1:]
    
    # collect options, command and remaining args

    options = list(takewhile(lambda arg: arg.startswith('-'), args))
    num_options = len(options)
    
    try:
        command = args[num_options]
    except IndexError:
        raise LingoCLIParseError('no command specified')

    remaining_args = args[num_options + 1:]

    # options and help

    if '--help' in options or '-h' in options:
        print(HELP)
        sys.exit(0)
    
    if '-v' in options or '--verbose' in options:
        ctx.log.setLevel('DEBUG')
        for handler in ctx.log.handlers:
            handler.setLevel('DEBUG')

    # command
   
    if command == 'exe':
        if len(remaining_args) != 1:
            raise LingoCLIParseError('exe command requires only a path argument')
    
        result = execute_file(ctx, remaining_args[0])
        result_type = type(result).__name__
        ctx.log.debug(f'exe return type: {result_type}')
        
        if result_type == 'str':
            print(result)
            
        elif result_type == 'LingoLanguageError':
            result_symbol = L_SYM_handle(
                expr=create_expression_ast(ctx, result, f'lingolib.exe.result.expr'),
                L_SRC=f'lingolib.exe.result.handle'
            )
            
            print(L_EXPR_handle(ctx, result_symbol))
            
        else:
            result_symbol = L_SYM_str(
                object=create_expression_ast(ctx, result, f'lingolib.exe.result.object'),
                L_SRC=f'lingolib.exe.result.str'
            )
            
            print(L_EXPR_str(ctx, result_symbol).value)

    elif command == 'ast':
        if len(remaining_args) != 1:
            raise LingoCLIParseError('ast command requires only a path argument')
        try:
            ast = ast_from_file(ctx, remaining_args[0])
            print(lingo_ast_to_string(ast))

        except Exception as e:
            ctx.log.error(f'error generating AST: {e}', exc_info=True)
            sys.exit(1)
    else:
        raise LingoCLIParseError(f'unknown command: {command}')

def main(ctx: LingoContext):
    try:
        parse_cli(ctx)
    except LingoCLIParseError as e:
        ctx.log.error(f'CLI parse error: {e}')
        sys.exit(1)

if __name__ == '__main__':
    ctx = LingoContext()
    main(ctx)
