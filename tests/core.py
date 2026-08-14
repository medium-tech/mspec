import json
import platform
import sys
import time

from pathlib import Path

from mtester import api
from mtester.context import MTesterContext


REPO_ROOT = Path(__file__).parent.parent
TESTS_TMP_DIR = REPO_ROOT / 'tests' / 'tmp'
MTESTER_CONFIG_PATH = REPO_ROOT / '.mtester' / 'config.json'
WINDOW_TITLE_GUI_SPEC = 'Lingo GUI Spec'
WINDOW_SETUP_SPEC = REPO_ROOT / 'lingo' / 'shared' / 'scripts' / 'gui' / 'hello-gui.yaml'


def setup_window_config() -> None:
	if platform.system() != 'Darwin':
		raise RuntimeError('Window setup is only supported on macOS.')

	ctx = MTesterContext(verbose=True)
	ctx.set_test_dir(test_name='window_setup', reset=True)
	launch_result = api.launch_target(
		ctx,
		command=[sys.executable, '-m', 'lingolib', '-v', 'display', str(WINDOW_SETUP_SPEC)],
	)

	time.sleep(1)

	print(f'launch_result: {launch_result}')

	if not launch_result.ok:
		raise RuntimeError(f'Failed to launch window setup target: {launch_result.error}')

	window_region = None
	last_error = None

	try:
		deadline = time.monotonic() + 10.0
		
		while time.monotonic() < deadline:
			try:
				window_region = api.get_region_for_window_title(ctx, window_title=WINDOW_TITLE_GUI_SPEC)
				break
			except RuntimeError as error:
				last_error = error
				time.sleep(0.25)
		
		
	finally:
		stop_result = api.stop_target(ctx, session_id=launch_result.session_id)
		
		if not stop_result.ok:
			raise RuntimeError(f'Failed to stop window setup target: {stop_result.error}')

	if window_region is None:
		print(stop_result.stdout)
		print(stop_result.stderr)
		raise RuntimeError(f'Failed to find window region for title "{WINDOW_TITLE_GUI_SPEC}": {last_error}')

	MTESTER_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
	config = {
		'window_title': WINDOW_TITLE_GUI_SPEC,
		'window_region': {
			'x': window_region.x,
			'y': window_region.y,
			'width': window_region.width,
			'height': window_region.height,
		},
	}
	MTESTER_CONFIG_PATH.write_text(json.dumps(config, indent=4, sort_keys=True) + '\n')
	print(f'Cached window configuration in {MTESTER_CONFIG_PATH}')

if __name__ == '__main__':
	setup_window_config()