import os
import tkinter
import logging

from dataclasses import dataclass, field
from typing import Optional

__all__ = [
    'DEFAULT_LOG_LEVEL_NAME',
    'DEFAULT_LOG_LEVEL',

    'init_logger',

    'LingoStateRuntimeContext',
    'LingoTKRuntimeContext',
    'LingoParserContext',

    'LingoContext'
]


DEFAULT_LOG_LEVEL_NAME = os.environ.get('LINGO_LOG_LEVEL', 'INFO').upper()
DEFAULT_LOG_LEVEL = getattr(logging, DEFAULT_LOG_LEVEL_NAME)

def init_logger(level=DEFAULT_LOG_LEVEL):
    logger = logging.getLogger('lingo')
    logger.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter(':: %(levelname)s :: line %(lineno)-4d of %(filename)-15s :: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

@dataclass(slots=True)
class LingoStateRuntimeContext:
    fields: dict[str, 'L_SYM_define']
    values: dict[str, any] = field(default_factory=dict)

@dataclass(slots=True)
class LingoTKRuntimeContext:
    root: tkinter.Tk
    text_widget: tkinter.Text
    main_block_index: int = 0
    in_text_block: bool = False
    state: Optional[LingoStateRuntimeContext] = None

@dataclass(slots=True)
class LingoParserContext:
    src: str = ''
    file: str = ''
    line: int = 0
    col: int = 0

@dataclass(slots=True)
class LingoContext:
    log: logging.Logger = field(default_factory=init_logger)
    parser: Optional[LingoParserContext] = None
    tk: Optional[LingoTKRuntimeContext] = None

    @classmethod
    def add_parser_context(cls, ctx: 'LingoContext', src: str, file: str, line: int, col: int):
        parser_context = LingoParserContext(src=src, file=file, line=line, col=col)
        return cls(
            log=ctx.log,
            parser=parser_context
        )

    @classmethod
    def add_tk_runtime_context(cls, ctx: 'LingoContext', root: tkinter.Tk, text_widget: tkinter.Text, state: Optional[LingoStateRuntimeContext] = None):
        tk_runtime_context = LingoTKRuntimeContext(root=root, text_widget=text_widget, state=state)
        return cls(
            log=ctx.log,
            parser=ctx.parser,
            tk=tk_runtime_context
        )