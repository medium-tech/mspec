import json
from pathlib import Path
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
        else:
            return super().default(obj)


def json_pprint(data) -> str:
    return json.dumps(data, indent=4, sort_keys=True, cls=MTesterJSONEncoder)
