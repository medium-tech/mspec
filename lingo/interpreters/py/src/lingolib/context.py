import os
import logging

from dataclasses import dataclass, field
import tkinter
from typing import Optional


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
class LingoTKRuntimeContext:
    root: tkinter.Tk
    text_widget: tkinter.Text
    main_block_index: int = 0
    in_text_block: bool = False

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
	def add_tk_runtime_context(cls, ctx: 'LingoContext', root: tkinter.Tk, text_widget: tkinter.Text):
		tk_runtime_context = LingoTKRuntimeContext(root=root, text_widget=text_widget)
		return cls(
			log=ctx.log,
			parser=ctx.parser,
			tk=tk_runtime_context
		)