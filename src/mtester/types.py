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


@dataclass(slots=True)
class CaptureTestFrameResult:
	capture_result: CaptureScreenResult
	ocr_result: OcrExtractResult | None = None
