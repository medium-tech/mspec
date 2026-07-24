import lingolib.symbols as symbols

from lingolib.context import LingoContext
from lingolib.types import LingoLiteralTypes

from .ast import LingoASTExpression, LingoASTExeSpec, LingoASTLibSpec, LingoASTSpec, lingo_ast_to_string
from .envelope import YamlLocationLoader, create_spec_ast_from_dict as _create_spec_ast_from_dict, get_yaml_line
from .expr_entry import create_expression_ast as _create_expression_ast
from .expr_entry import create_expression_ast_from_dict as _create_expression_ast_from_dict


def create_spec_ast_from_dict(ctx: LingoContext, data: dict) -> LingoASTSpec:
    return _create_spec_ast_from_dict(
        ctx=ctx,
        data=data,
        create_expression_ast=create_expression_ast,
        get_yaml_line=get_yaml_line,
    )


def create_expression_ast(ctx: LingoContext, data: LingoLiteralTypes, L_SRC: str) -> symbols.ExpressionSymbols:
    return _create_expression_ast(
        ctx=ctx,
        data=data,
        L_SRC=L_SRC,
        get_yaml_line=get_yaml_line,
    )


def create_expression_ast_from_dict(ctx: LingoContext, data: dict, L_SRC: str) -> symbols.ExpressionSymbols:
    return _create_expression_ast_from_dict(
        ctx=ctx,
        data=data,
        L_SRC=L_SRC,
        create_expression_ast=create_expression_ast,
        get_yaml_line=get_yaml_line,
    )
