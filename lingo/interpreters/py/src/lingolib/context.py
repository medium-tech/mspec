import logging

from dataclasses import dataclass, field


def init_logger(level=logging.DEBUG):
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
