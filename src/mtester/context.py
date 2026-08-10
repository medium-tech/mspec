import shutil
import logging

from dataclasses import dataclass, field
from pathlib import Path

from mtester.types import RegionBox

from lingolib.context import init_logger


@dataclass(slots=True)
class MTesterConfig:
	spec_path: Path
	capture_region: RegionBox | None = None
	window_title: str | None = None
	select_window: bool = False
	assert_ocr_text: list[str] | None = None
	assert_stdout: list[str] | None = None
	assert_stderr: list[str] | None = None
	verbose: bool = False
	

@dataclass(slots=True)
class MTesterContext:
	test_dir: Path | None = None
	config: MTesterConfig = field(default_factory=MTesterConfig)
	log: logging.Logger = field(default_factory=init_logger)

	def set_test_dir(self, test_name:str, reset:bool=False) -> Path:
		self.test_dir = Path.cwd() / '.mtester' / test_name
		if reset:
			try:
				shutil.rmtree(self.test_dir)
			except FileNotFoundError:
				pass
		self.test_dir.mkdir(parents=True, exist_ok=True)

		return self.test_dir

	def __post_init__(self):
		if self.config.verbose:
			self.log.setLevel(logging.DEBUG)
