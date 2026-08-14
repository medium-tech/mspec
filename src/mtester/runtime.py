import os
import json
import platform

from pathlib import Path
from unittest.mock import patch

from mtester import api
from mtester.types import RegionBox

WINDOW_TITLE_TEXT_SPEC = 'Lingo Text Spec'
WINDOW_TITLE_GUI_SPEC = 'Lingo GUI Spec'

IS_DARWIN = platform.system() == 'Darwin'
RUN_GUI_TESTS = os.environ.get('RUN_GUI_TESTS', '0') == '1'
QUICK_WINDOW = os.environ.get('QUICK_WINDOW', '0') == '1'

"""
To speed up tkinter tests you can provide QUICK_WINDOW=1 which means we'll only
query the os for the window size one time and re-use it for remaining tests.

It is less reliable but will speed up tests significantly.

It is based on the assumption that the window size and location does not change between tests.

"""

WINDOW_REGION_CACHE: RegionBox | None = None

if QUICK_WINDOW:
    config_path = Path.cwd() / '.mtester' / 'config.json'
    with open(config_path, 'r') as f:
        config_data = json.load(f)
        WINDOW_REGION_CACHE = RegionBox(**config_data['window_region'])
        
def get_window_region(ctx, window_title:str) -> RegionBox:
	global WINDOW_REGION_CACHE

	if not IS_DARWIN:
		raise RuntimeError('Window region detection is only supported on macOS.')

	# print(f'\n\tget_window_region: {WINDOW_REGION_CACHE=} {QUICK_WINDOW=} {window_title=}')
	
	if WINDOW_REGION_CACHE is None or not QUICK_WINDOW:
		# print(f'\t\tget_window_region: querying os for window region for title')
		WINDOW_REGION_CACHE = api.get_region_for_window_title(ctx, window_title=window_title)

	# print(f'\t\tget_window_region: returning window region {WINDOW_REGION_CACHE=}')
	return WINDOW_REGION_CACHE
