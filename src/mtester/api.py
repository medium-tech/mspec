import subprocess
import time
import uuid
import os
import platform

from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from mtester.context import MTesterContext, MTesterConfig
from mtester.types import RegionBox

from PIL import Image, ImageGrab
import pytesseract


_RUNNING_SESSIONS: dict[str, subprocess.Popen] = {}


#
# low level program interface
#

def launch_target(ctx: MTesterContext, command: list[str], cwd: str | None = None, env: dict[str, str] | None = None) -> dict[str, Any]:
    ctx.log.debug(f'mtester.api.launch_target called with args: command={command}, cwd={cwd}, env={env}')

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

def get_region_for_window_title(ctx: MTesterContext, window_title: str) -> RegionBox:
    ctx.log.debug(f'mtester.api.get_region_for_window_title called with args: window_title={window_title}')

    windows_result = list_windows(ctx)
    if not windows_result.get('ok', False):
        raise RuntimeError(f"Failed to list windows: {windows_result.get('error', 'Unknown error')}")

    windows = windows_result.get('windows', [])
    matching_windows = [w for w in windows if w['title'] == window_title]

    if len(matching_windows) != 1:
        raise RuntimeError(f"Expected exactly one window matching title: {window_title!r}, found {len(matching_windows)}")

    selected_window = matching_windows[0]
    return RegionBox(
        x=selected_window['x'],
        y=selected_window['y'],
        width=selected_window['width'],
        height=selected_window['height'],
    )


def stop_target(ctx: MTesterContext, session_id: str, force: bool = False) -> dict[str, Any]:
    ctx.log.debug(f'mtester.api.stop_target called with args: session_id={session_id}, force={force}')

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
            ctx.log.debug(f'Forcefully killing process with PID {process.pid} for session_id {session_id}')
            process.kill()
        else:
            ctx.log.debug(f'Terminating process with PID {process.pid} for session_id {session_id}')
            process.terminate()

        try:
            stdout_text, stderr_text = process.communicate(timeout=15.0)
        except subprocess.TimeoutExpired:
            ctx.log.warning(f'Process with PID {process.pid} did not terminate in time, forcefully killing it.')
            process.kill()
            stdout_text, stderr_text = process.communicate(timeout=15.0)
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


def capture_screen(ctx: MTesterContext, output_path: Path, region: RegionBox | None = None) -> dict[str, Any]:
    ctx.log.debug(f'mtester.api.capture_screen called with args: region={region}')

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


def list_windows(ctx: MTesterContext) -> dict[str, Any]:
    ctx.log.debug('mtester.api.list_windows called')

    if platform.system() != 'Darwin':
        raise RuntimeError('list_windows is only supported on macOS currently.')

    script = r'''
tell application "System Events"
    set output_text to ""
    repeat with p in (application processes whose background only is false)
        set app_name to name of p
        repeat with w in windows of p
            try
                set win_name to name of w
                set win_pos to position of w
                set win_size to size of w
                set entry_text to app_name & "\t" & win_name & "\t" & (item 1 of win_pos as text) & "\t" & (item 2 of win_pos as text) & "\t" & (item 1 of win_size as text) & "\t" & (item 2 of win_size as text)
                if output_text is not "" then
                    set output_text to output_text & linefeed
                end if
                set output_text to output_text & entry_text
            end try
        end repeat
    end repeat
    return output_text
end tell
'''

    try:
        proc = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as e:
        return {
            'ok': False,
            'function': 'list_windows',
            'error': f'{e.__class__.__name__}: {e}',
            'windows': [],
        }

    if proc.returncode != 0:
        return {
            'ok': False,
            'function': 'list_windows',
            'error': (proc.stderr or proc.stdout or '').strip(),
            'windows': [],
        }

    windows = []
    for index, line in enumerate(proc.stdout.splitlines()):
        parts = line.split('\t')
        if len(parts) != 6:
            continue

        try:
            x = int(parts[2].strip())
            y = int(parts[3].strip())
            width = int(parts[4].strip())
            height = int(parts[5].strip())
        except ValueError:
            continue

        windows.append({
            'index': index,
            'app': parts[0].strip(),
            'title': parts[1].strip(),
            'x': x,
            'y': y,
            'width': width,
            'height': height,
        })

    return {
        'ok': True,
        'function': 'list_windows',
        'windows': windows,
        'count': len(windows),
    }


def ocr_extract(ctx: MTesterContext, image_path: str, region: RegionBox | None = None) -> dict[str, Any]:
    ctx.log.debug(f'mtester.api.ocr_extract called with args: image_path={image_path!r}, region={region}')

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


#
# high level services
#

def capture_test_frame(ctx: MTesterContext, name: str | Path, region: RegionBox | None = None, **kwargs) -> dict[str, Any]:

    #
    # init
    #

    config: MTesterConfig = ctx.config

    extract_ocr = kwargs.get('extract_ocr', True)                      		# whether to run OCR on the captured image
    wait_for_window = kwargs.get('wait_for_window', 0.5)                    # wait this many seconds for the target window to open before capturing the screen

    # wait for window to open #

    time.sleep(wait_for_window)

    #
    # capture screen
    #

    image_path = ctx.test_dir / f'frame_{name}.png'
    capture_result = capture_screen(ctx, output_path=image_path, region=region)

    if not capture_result.get('ok', False):
        raise RuntimeError(f"Failed to capture screen: {capture_result.get('error', 'Unknown error')}")

    if extract_ocr:
        ocr_result = ocr_extract(ctx, image_path=image_path)
        if not ocr_result.get('ok', False):
            raise RuntimeError(f"Failed to extract OCR: {ocr_result.get('error', 'Unknown error')}")
    else:
        ocr_result = None

    return {
        'capture_result': capture_result,
        'ocr_result': ocr_result,
    }