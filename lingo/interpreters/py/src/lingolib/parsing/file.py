import os

import yaml

from lingolib.ast import LingoASTSpec
from lingolib.context import LingoContext
from lingolib.errors import LingoSyntaxError
from lingolib.parsing.spec_lingo import create_spec_ast_from_dict
from lingolib.parsing.state import YamlLocationLoader


def create_ast_from_file(ctx: LingoContext, path: str) -> LingoASTSpec:
    try:
        with open(path) as f:
            doc = yaml.load(f.read(), Loader=YamlLocationLoader)
    except yaml.YAMLError as e:
        raise LingoSyntaxError(f'failed to parse YAML file {path}: {e}')

    parser_ctx = LingoContext.add_parser_context(ctx, src='', file=os.path.abspath(path), line=0, col=0)
    return create_spec_ast_from_dict(parser_ctx, doc)
