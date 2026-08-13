import json

from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Any
from typing import NamedTuple


class RegionBox(NamedTuple):
	x: int
	y: int
	width: int
	height: int

	def __str__(self):
		return f"RegionBox(x={self.x}, y={self.y}, width={self.width}, height={self.height})"

class PixelRGB(NamedTuple):
	r: int
	g: int
	b: int

	def __str__(self):
		return f"PixelRGB(r={self.r}, g={self.g}, b={self.b})"


@dataclass(slots=True)
class ManualFlowOptions:
	spec_path: Path
	capture_region: RegionBox | None = None
	window_title: str | None = None
	select_window: bool = False
	verbose: bool = False

	assert_ocr_text: list[str] | None = None
	assert_not_ocr_text: list[str] | None = None

	assert_stdout_text: list[str] | None = None
	assert_not_stdout_text: list[str] | None = None

	assert_stderr_text: list[str] | None = None
	assert_not_stderr_text: list[str] | None = None


class MTesterJSONEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, Path):
			return str(obj)
		if is_dataclass(obj):
			return asdict(obj)
		else:
			return super().default(obj)


def json_pprint(data) -> str:
    return json.dumps(data, indent=4, sort_keys=True, cls=MTesterJSONEncoder)


@dataclass(slots=True)
class WindowInfo:
	index: int
	app: str
	title: str
	x: int
	y: int
	width: int
	height: int


@dataclass(slots=True)
class OcrToken:
	text: str
	left: int
	top: int
	width: int
	height: int
	confidence: float

	def get_region_box(self) -> RegionBox:
		return RegionBox(x=self.left, y=self.top, width=self.width, height=self.height)


@dataclass(slots=True)
class LaunchTargetResult:
	ok: bool
	function: str
	args: dict[str, Any]
	session_id: str = ''
	pid: int | None = None
	start_time: str = ''
	error: str | None = None


@dataclass(slots=True)
class StopTargetResult:
	ok: bool
	function: str
	args: dict[str, Any]
	exit_code: int | None = None
	stdout: str = ''
	stderr: str = ''
	error: str | None = None


@dataclass(slots=True)
class CaptureScreenResult:
	ok: bool
	function: str
	args: dict[str, Any]
	image_path: str
	width: int | None = None
	height: int | None = None
	captured_at: str = ''
	error: str | None = None


@dataclass(slots=True)
class SimulateClickResult:
	ok: bool
	function: str
	args: dict[str, Any]
	x: int
	y: int
	error: str | None = None


@dataclass(slots=True)
class ListWindowsResult:
	ok: bool
	function: str
	windows: list[WindowInfo] = field(default_factory=list)
	count: int = 0
	error: str | None = None


@dataclass(slots=True)
class OcrExtractResult:
	ok: bool
	function: str
	args: dict[str, Any]
	text: str = ''
	tokens: list[OcrToken] = field(default_factory=list)
	token_count: int = 0
	average_confidence: float = -1.0
	error: str | None = None
	_current_index: int = field(default=0, init=False, repr=False)

	def seek_token(self, index: int):
		"""Set the current token cursor to the specified index."""
		if index < 0 or index >= self.token_count:
			raise IndexError(f'Index out of range: {index}')
		self._current_index = index

	def next_token(self) -> OcrToken | None:
		"""Return token at current cursor and advance cursor by one."""
		if self._current_index >= self.token_count:
			return None

		token = self.tokens[self._current_index]
		self._current_index += 1
		return token

	def find_token(self, text: str, skip: int = 0) -> OcrToken | None:
		"""Search from current cursor for matching token, advancing cursor as tokens are scanned."""
		if skip < 0:
			raise ValueError(f'skip must be >= 0, got: {skip}')

		skipped = 0
		target_text = text.lower()

		while self._current_index < self.token_count:
			token = self.tokens[self._current_index]
			self._current_index += 1

			if token.text.lower() == target_text:
				if skipped == skip:
					return token
				skipped += 1

		return None


@dataclass(slots=True)
class CaptureTestFrameResult:
	capture_result: CaptureScreenResult
	ocr_result: OcrExtractResult | None = None


@dataclass(slots=True)
class ColorRegionAssertion:
	name: str
	region: RegionBox
	color: PixelRGB
	expected_present: bool
	tolerance: int = 40


@dataclass(slots=True)
class ColorRegionAssertionResult:
	name: str
	passed: bool
	expected_present: bool
	found: bool
	match_count: int
	pixel_count: int
	match_ratio: float
	region: RegionBox
	color: PixelRGB
	tolerance: int


@dataclass(slots=True)
class ColorAssertionsResult:
	ok: bool
	function: str
	image_path: str
	assertions: list[ColorRegionAssertionResult] = field(default_factory=list)
	error: str | None = None
