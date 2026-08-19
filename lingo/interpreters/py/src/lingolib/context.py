import os
import tkinter
import logging

from dataclasses import dataclass, field
from typing import Callable, Optional, NamedTuple

from lingolib.symbols import L_SYM_define, L_SYM_func, L_SYM_value
from lingolib.errors import LingoRuntimeError

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
    fields: dict[str, L_SYM_define]
    values: dict[str, any] = field(default_factory=dict)

#
# runtime
#

class LingoRegisteredFunction(NamedTuple):
    name: str
    ast: L_SYM_func

    def __str__(self):
        return f'LingoRegisteredFunction(name={self.name})'

    def __repr__(self):
        return str(self)

class LingoRegisteredValue(NamedTuple):
    name: str
    ast: L_SYM_value

    def __str__(self):
        return f'LingoRegisteredValue(name={self.name})'

    def __repr__(self):
        return str(self)

class LingoRegisteredDefinition(NamedTuple):
    name: str
    ast: L_SYM_define

    def __str__(self):
        return f'LingoRegisteredDefinition(name={self.name})'

    def __repr__(self):
        return str(self)


@dataclass
class LingoRegistry:
    ops: dict[str, LingoRegisteredFunction] = field(default_factory=dict)
    lib: dict[str, LingoRegisteredFunction | LingoRegisteredValue | LingoRegisteredDefinition] = field(default_factory=dict)
    params: dict[str, any] = field(default_factory=dict)
    call_args_stack: list[dict] = field(default_factory=list)

def no_draw_method():
    raise LingoRuntimeError('redraw function has not been set')

@dataclass(slots=True)
class LingoTKRuntimeContext:
    root: tkinter.Tk
    text_widget: tkinter.Text
    main_block_index: int = 0
    in_text_block: bool = False
    in_value_block: bool = False	# used for lists, structs and tables
    redraw: Callable = no_draw_method
    state: Optional[LingoStateRuntimeContext] = None
    


#
# parser
#

@dataclass(slots=True)
class LingoParserContext:
    src: str = ''
    file: str = ''
    line: int = 0
    col: int = 0

#
# main context
#

@dataclass(slots=True)
class LingoContext:
    log: logging.Logger = field(default_factory=init_logger)
    parser: Optional[LingoParserContext] = None
    tk: Optional[LingoTKRuntimeContext] = None
    registry: Optional[LingoRegistry] = None

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
            tk=tk_runtime_context,
            registry=ctx.registry
        )