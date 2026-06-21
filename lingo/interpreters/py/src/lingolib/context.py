import os
import logging

from dataclasses import dataclass, field


DEFAULT_LOG_LEVEL_NAME = os.environ.get('LINGO_LOG_LEVEL', 'INFO').upper()
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
