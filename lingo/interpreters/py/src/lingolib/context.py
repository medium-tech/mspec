import os
import logging

from dataclasses import dataclass, field
from typing import Optional


DEFAULT_LOG_LEVEL_NAME = os.environ.get('LINGO_LOG_LEVEL', 'DEBUG').upper()
DEFAULT_LOG_LEVEL = getattr(logging, DEFAULT_LOG_LEVEL_NAME)

def init_logger(level=DEFAULT_LOG_LEVEL):
	logger = logging.getLogger('lingo')
	logger.setLevel(level)
	ch = logging.StreamHandler()
	ch.setLevel(level)
	formatter = logging.Formatter(':: %(levelname)s :: %(message)s')
	ch.setFormatter(formatter)
	logger.addHandler(ch)
	return logger



@dataclass
class LingoContext:
	log: logging.Logger = field(default_factory=init_logger)
	interpreter: Optional['LingoInterpreterContext'] = None


@dataclass
class LingoInterpreterContext:
	src: str = ''
	file: str = ''
	line: int = 0
	col: int = 0

	@classmethod
	def new_from_ctx(cls, ctx: 'LingoContext', src: str = '', file: str = '', line: int = 0, col: int = 0) -> LingoContext:
		return LingoContext(
			log=ctx.log,
			interpreter=cls(src=src, file=file, line=line, col=col)
		)
