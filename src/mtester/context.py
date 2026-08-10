import shutil

from dataclasses import dataclass, field
from pathlib import Path

from mtester.types import RegionBox

@dataclass(slots=True)
class MTesterConfig:
	spec_path: Path
	capture_region: RegionBox | None = None
	window_title: str | None = None
	select_window: bool = False
	assert_ocr_text: str | None = None
	assert_stdout: str | None = None
	assert_stderr: str | None = None
	verbose: bool = False

	

@dataclass(slots=True)
class MTesterContext:
	test_dir: Path | None = None
	config: MTesterConfig = field(default_factory=MTesterConfig)

	def set_test_dir(self, test_name:str, reset:bool=False) -> Path:
		self.test_dir = Path.cwd() / '.mtester' / test_name
		if reset:
			try:
				shutil.rmtree(self.test_dir)
			except FileNotFoundError:
				pass
		self.test_dir.mkdir(parents=True, exist_ok=True)

		return self.test_dir