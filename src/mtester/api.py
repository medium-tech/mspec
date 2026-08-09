#
# mtester api placeholders
#

from datetime import datetime, UTC
from pathlib import Path
import subprocess
import uuid
import os

from .types import RegionBox, PixelRGB

from typing import Any

from PIL import Image, ImageGrab
import pytesseract


_RUNNING_SESSIONS: dict[str, subprocess.Popen] = {}


def _placeholder_result(function_name: str, **kwargs) -> dict[str, Any]:
	print(f'mtester.api.{function_name} called with args: {kwargs}')
	return {
		'ok': True,
		'function': function_name,
		'args': kwargs,
	}


def launch_target(command: list[str], cwd: str | None = None, env: dict[str, str] | None = None) -> dict[str, Any]:
	print(f'mtester.api.launch_target called with args: command={command}, cwd={cwd}, env={env}')

	process = subprocess.Popen(
		command,
		cwd=cwd,
		env=env,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
		text=True,
	)

	session_id = f'mtester-session-{uuid.uuid4()}'
	_RUNNING_SESSIONS[session_id] = process

	result = {
		'ok': True,
		'function': 'launch_target',
		'args': {
			'command': command,
			'cwd': cwd,
			'env': env,
		},
		'session_id': session_id,
		'pid': process.pid,
		'start_time': datetime.now(UTC).isoformat(),
	}
	return result
	# Args: command is the process argv, cwd is optional working directory, env is optional env var overrides.
	# Does: starts the target app process for UI testing and returns a process/session descriptor.
	# Returns: dict with process metadata, such as pid, start_time, and opaque session_id.


def stop_target(session_id: str, force: bool = False) -> dict[str, Any]:
	print(f'mtester.api.stop_target called with args: session_id={session_id}, force={force}')

	process = _RUNNING_SESSIONS.get(session_id)
	if process is None:
		return {
			'ok': False,
			'function': 'stop_target',
			'args': {
				'session_id': session_id,
				'force': force,
			},
			'error': f'No running session found for session_id: {session_id}',
		}

	if process.poll() is None:
		if force:
			process.kill()
		else:
			process.terminate()

		try:
			stdout_text, stderr_text = process.communicate(timeout=2.0)
		except subprocess.TimeoutExpired:
			process.kill()
			stdout_text, stderr_text = process.communicate(timeout=2.0)
	else:
		stdout_text, stderr_text = process.communicate()

	exit_code = process.returncode
	_RUNNING_SESSIONS.pop(session_id, None)

	return {
		'ok': True,
		'function': 'stop_target',
		'args': {
			'session_id': session_id,
			'force': force,
		},
		'exit_code': exit_code,
		'stdout': stdout_text,
		'stderr': stderr_text,
	}
	# Args: session_id identifies a running target, force controls graceful vs immediate shutdown.
	# Does: stops the target app process started by launch_target.
	# Returns: dict with termination status, exit_code when available, and any shutdown notes.


def capture_screen(region: RegionBox | None = None) -> dict[str, Any]:
	print(f'mtester.api.capture_screen called with args: region={region}')

	output_dir = Path.cwd() / '.mtester'
	output_dir.mkdir(parents=True, exist_ok=True)
	output_path = output_dir / 'test_frame.png'

	try:
		if region is None:
			image = ImageGrab.grab()
		else:
			x, y, width, height = region
			bbox = (x, y, x + width, y + height)
			image = ImageGrab.grab(bbox=bbox)

		image.save(output_path, format='PNG')

		return {
			'ok': True,
			'function': 'capture_screen',
			'args': {
				'region': region,
			},
			'image_path': str(output_path),
			'width': image.width,
			'height': image.height,
			'captured_at': datetime.now(UTC).isoformat(),
		}

	except Exception as e:
		return {
			'ok': False,
			'function': 'capture_screen',
			'args': {
				'region': region,
			},
			'image_path': str(output_path),
			'error': f'{e.__class__.__name__}: {e}',
		}
	# Args: region is optional (x, y, width, height) screen crop; None captures the full primary screen.
	# Does: captures a screenshot that can be used for OCR, color checks, and layout assertions.
	# Returns: dict containing image path/bytes metadata plus width/height and timestamp.


def ocr_extract(image_path: str, region: RegionBox | None = None) -> dict[str, Any]:
	print(f'mtester.api.ocr_extract called with args: image_path={image_path!r}, region={region}')

	if not os.path.exists(image_path):
		return {
			'ok': False,
			'function': 'ocr_extract',
			'args': {
				'image_path': image_path,
				'region': region,
			},
			'error': f'Image file not found: {image_path}',
			'text': '',
			'tokens': [],
		}

	try:
		with Image.open(image_path) as source_image:
			working_image = source_image.convert('RGB')

			if region is not None:
				x, y, width, height = region
				if width <= 0 or height <= 0:
					return {
						'ok': False,
						'function': 'ocr_extract',
						'args': {
							'image_path': image_path,
							'region': region,
						},
						'error': f'Invalid region size: width={width}, height={height}',
						'text': '',
						'tokens': [],
					}

				crop_box = (x, y, x + width, y + height)
				working_image = working_image.crop(crop_box)

			ocr_text = pytesseract.image_to_string(working_image)
			ocr_data = pytesseract.image_to_data(working_image, output_type=pytesseract.Output.DICT)

		tokens = []
		conf_values = []
		for index, raw_text in enumerate(ocr_data.get('text', [])):
			text_value = raw_text.strip()
			if text_value == '':
				continue

			try:
				confidence = float(ocr_data['conf'][index])
			except (ValueError, TypeError):
				confidence = -1.0

			if confidence >= 0:
				conf_values.append(confidence)

			tokens.append({
				'text': text_value,
				'left': int(ocr_data['left'][index]),
				'top': int(ocr_data['top'][index]),
				'width': int(ocr_data['width'][index]),
				'height': int(ocr_data['height'][index]),
				'confidence': confidence,
			})

		average_confidence = (sum(conf_values) / len(conf_values)) if conf_values else -1.0

		return {
			'ok': True,
			'function': 'ocr_extract',
			'args': {
				'image_path': image_path,
				'region': region,
			},
			'text': ocr_text.strip(),
			'tokens': tokens,
			'token_count': len(tokens),
			'average_confidence': average_confidence,
		}

	except Exception as e:
		return {
			'ok': False,
			'function': 'ocr_extract',
			'args': {
				'image_path': image_path,
				'region': region,
			},
			'error': f'{e.__class__.__name__}: {e}',
			'text': '',
			'tokens': [],
		}
	# Args: image_path points to an image file, region optionally limits OCR to a crop rectangle.
	# Does: extracts text with positional metadata from the image using OCR.
	# Returns: dict with plain text plus token/line boxes and confidence scores.


def detect_colors(image_path: str, palette: dict[str, tuple[int, int, int]]) -> dict[str, Any]:
	return _placeholder_result('detect_colors', image_path=image_path, palette=palette)
	# Args: image_path points to an image file, palette maps names to target RGB values.
	# Example palette: {'red': (255, 0, 0), 'yellow': (255, 255, 0), 'green': (0, 255, 0)}
	# Does: detects approximate color matches in the image and computes summary match statistics.
	# Returns: dict keyed by palette name with hit booleans, counts, and optional bounding boxes.


def detect_widgets(image_path: str, widget_types: list[str]) -> dict[str, Any]:
	return _placeholder_result('detect_widgets', image_path=image_path, widget_types=widget_types)
	# Args: image_path points to an image file, widget_types lists expected widgets like button/input/table.
	# Does: runs lightweight detection heuristics for supported GUI widgets.
	# Returns: dict with detected widget instances, each including type, bounding box, and confidence.


def click_point(x: int, y: int, button: str = 'left') -> dict[str, Any]:
	return _placeholder_result('click_point', x=x, y=y, button=button)
	# Args: x/y are absolute screen coordinates, button selects mouse button.
	# Does: performs a click action at the given coordinates for UI interaction tests.
	# Returns: dict describing action result and any platform-level input warnings.


def type_text(text: str, submit: bool = False) -> dict[str, Any]:
	return _placeholder_result('type_text', text=text, submit=submit)
	# Args: text is keyboard input content, submit controls whether Enter is pressed after typing.
	# Does: sends keyboard input to the currently focused UI element.
	# Returns: dict with typed length, submit flag, and input delivery status.


def assert_ocr_text(expected: str, image_path: str, region: RegionBox | None = None, case_sensitive: bool = False) -> dict[str, Any]:
	print(
		'mtester.api.assert_ocr_text called with args: '
		f'expected={expected!r}, image_path={image_path!r}, region={region}, case_sensitive={case_sensitive}'
	)

	ocr_result = ocr_extract(image_path=image_path, region=region)
	ocr_text = str(ocr_result.get('text', ''))

	if not case_sensitive:
		expected_check = expected.lower()
		ocr_text_check = ocr_text.lower()
	else:
		expected_check = expected
		ocr_text_check = ocr_text

	passed = expected_check in ocr_text_check

	return {
		'ok': passed,
		'function': 'assert_ocr_text',
		'args': {
			'expected': expected,
			'image_path': image_path,
			'region': region,
			'case_sensitive': case_sensitive,
		},
		'found': passed,
		'expected': expected,
		'ocr_text': ocr_text,
		'ocr': ocr_result,
	}
	# Args: expected is required text, image_path is OCR source image, region optionally scopes the check.
	# Does: verifies expected text appears in OCR output with optional case sensitivity rules.
	# Returns: dict with pass/fail, matched spans, and diagnostic OCR excerpts.


def assert_stdout(expected: str, stdout_text: str, case_sensitive: bool = False) -> dict[str, Any]:
	print(
		'mtester.api.assert_stdout called with args: '
		f'expected={expected!r}, stdout_text=<len {len(stdout_text)}>, case_sensitive={case_sensitive}'
	)

	if not case_sensitive:
		expected_check = expected.lower()
		stdout_check = stdout_text.lower()
	else:
		expected_check = expected
		stdout_check = stdout_text

	passed = expected_check in stdout_check

	return {
		'ok': passed,
		'function': 'assert_stdout',
		'args': {
			'expected': expected,
			'case_sensitive': case_sensitive,
		},
		'found': passed,
		'expected': expected,
		'stdout_text': stdout_text,
	}
	# Args: expected is required text and stdout_text is collected process stdout from the app run.
	# Does: verifies expected text appears in stdout with optional case sensitivity.
	# Returns: dict with pass/fail and matching diagnostics for stdout assertions.


def assert_stderr(expected: str, stderr_text: str, case_sensitive: bool = False) -> dict[str, Any]:
	print(
		'mtester.api.assert_stderr called with args: '
		f'expected={expected!r}, stderr_text=<len {len(stderr_text)}>, case_sensitive={case_sensitive}'
	)

	if not case_sensitive:
		expected_check = expected.lower()
		stderr_check = stderr_text.lower()
	else:
		expected_check = expected
		stderr_check = stderr_text

	passed = expected_check in stderr_check

	return {
		'ok': passed,
		'function': 'assert_stderr',
		'args': {
			'expected': expected,
			'case_sensitive': case_sensitive,
		},
		'found': passed,
		'expected': expected,
		'stderr_text': stderr_text,
	}
	# Args: expected is required text and stderr_text is collected process stderr from the app run.
	# Does: verifies expected text appears in stderr with optional case sensitivity.
	# Returns: dict with pass/fail and matching diagnostics for stderr assertions.


def assert_color(name: str, image_path: str, rgb: PixelRGB, tolerance: int = 20) -> dict[str, Any]:
	return _placeholder_result('assert_color', name=name, image_path=image_path, rgb=rgb, tolerance=tolerance)
	# Args: name labels the color check, image_path is source image, rgb is target color, tolerance is channel delta.
	# Does: verifies whether the target color is present within tolerance in the image.
	# Returns: dict with pass/fail plus hit ratios and sampled pixel evidence.


def assert_layout(expected_items: list[dict[str, Any]], image_path: str, tolerance_px: int = 8) -> dict[str, Any]:
	return _placeholder_result(
		'assert_layout',
		expected_items=expected_items,
		image_path=image_path,
		tolerance_px=tolerance_px,
	)
	# Args: expected_items describes expected labels/widgets and approximate boxes, image_path is source image.
	# Does: compares detected/ocr positions against expected layout relationships with pixel tolerance.
	# Returns: dict with pass/fail and per-item deviations for alignment/placement debugging.


	# Args: flow_path points to a declarative test flow file, variables provides optional runtime substitutions.
	# Does: executes a multi-step scenario combining actions, captures, and assertions.
	# Returns: dict with overall pass/fail, step-by-step results, and artifact references.
