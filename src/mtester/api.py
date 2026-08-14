import subprocess
import time
import uuid
import os
import platform

from datetime import datetime, UTC
from pathlib import Path

from mtester.context import MTesterContext
from mtester.types import (
    ColorAssertionsResult,
    ColorRegionAssertion,
    ColorRegionAssertionResult,
    CaptureScreenResult,
    CaptureTestFrameResult,
    LaunchTargetResult,
    ListWindowsResult,
    OcrExtractResult,
    OcrToken,
    PixelRGB,
    RegionBox,
    SimulateClickResult,
    StopTargetResult,
    WindowInfo,
    json_pprint,
)

from PIL import Image, ImageGrab
import pytesseract


_RUNNING_SESSIONS: dict[str, subprocess.Popen] = {}


#
# low level program interface
#

def launch_target(ctx: MTesterContext, command: list[str], cwd: str | None = None, env: dict[str, str] | None = None) -> LaunchTargetResult:
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

    result = LaunchTargetResult(
        ok=True,
        function='launch_target',
        args={
            'command': command,
            'cwd': cwd,
            'env': env,
        },
        session_id=session_id,
        pid=process.pid,
        start_time=datetime.now(UTC).isoformat(),
    )
    return result

def get_region_for_window_title(ctx: MTesterContext, window_title: str) -> RegionBox:
    ctx.log.debug(f'mtester.api.get_region_for_window_title called with args: window_title={window_title}')

    windows_result = list_windows(ctx)
    if not windows_result.ok:
        raise RuntimeError(f"Failed to list windows: {windows_result.error or 'Unknown error'}")

    windows = windows_result.windows
    matching_windows = [w for w in windows if w.title == window_title]

    if len(matching_windows) != 1:
        raise RuntimeError(f"Expected exactly one window matching title: {window_title!r}, found {len(matching_windows)}")

    selected_window = matching_windows[0]
    return RegionBox(
        x=selected_window.x,
        y=selected_window.y,
        width=selected_window.width,
        height=selected_window.height,
    )

def stop_target(ctx: MTesterContext, session_id: str, force: bool = False) -> StopTargetResult:
    ctx.log.debug(f'mtester.api.stop_target called with args: session_id={session_id}, force={force}')

    process = _RUNNING_SESSIONS.get(session_id)
    if process is None:
        return StopTargetResult(
            ok=False,
            function='stop_target',
            args={
                'session_id': session_id,
                'force': force,
            },
            error=f'No running session found for session_id: {session_id}',
        )

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

    return StopTargetResult(
        ok=True,
        function='stop_target',
        args={
            'session_id': session_id,
            'force': force,
        },
        exit_code=exit_code,
        stdout=stdout_text,
        stderr=stderr_text,
    )

def capture_screen(ctx: MTesterContext, output_path: Path, region: RegionBox | None = None) -> CaptureScreenResult:
    ctx.log.debug(f'mtester.api.capture_screen called with args: region={region}')

    try:
        if region is None:
            image = ImageGrab.grab()
        else:
            x, y, width, height = region
            bbox = (x, y, x + width, y + height)
            image = ImageGrab.grab(bbox=bbox)

        image.save(output_path, format='PNG')

        return CaptureScreenResult(
            ok=True,
            function='capture_screen',
            args={
                'region': region,
            },
            image_path=str(output_path),
            width=image.width,
            height=image.height,
            captured_at=datetime.now(UTC).isoformat(),
        )

    except Exception as e:
        return CaptureScreenResult(
            ok=False,
            function='capture_screen',
            args={
                'region': region,
            },
            image_path=str(output_path),
            error=f'{e.__class__.__name__}: {e}',
        )

def simulate_click(ctx: MTesterContext, x: int, y: int, double_click: bool = False) -> SimulateClickResult:
    """
    params:
        ctx: MTesterContext - the context object for logging and configuration
        x: int - the x-coordinate of the click
        y: int - the y-coordinate of the click
        double_click: bool - whether to perform a double click (default: False)
            useful for targets that require the window to be focused before the click registers
    returns:
        SimulateClickResult - the result of the click simulation, including success status and any error
    """

    ctx.log.debug(f'mtester.api.simulate_click called with args: x={x}, y={y}')

    num_clicks = 2 if double_click else 1

    try:
        # click twice since some targets require the window to be focused before the click registers
        for _ in range(num_clicks):
            proc = subprocess.run(
                ['cliclick', f'c:{x},{y}'],
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode != 0:
                break
    except Exception as e:
        return SimulateClickResult(
            ok=False,
            function='simulate_click',
            args={
                'x': x,
                'y': y,
            },
            x=x,
            y=y,
            error=f'{e.__class__.__name__}: {e}',
        )

    if proc.returncode != 0:
        return SimulateClickResult(
            ok=False,
            function='simulate_click',
            args={
                'x': x,
                'y': y,
            },
            x=x,
            y=y,
            error=(proc.stderr or proc.stdout or '').strip(),
        )

    return SimulateClickResult(
        ok=True,
        function='simulate_click',
        args={
            'x': x,
            'y': y,
        },
        x=x,
        y=y,
    )

def list_windows(ctx: MTesterContext) -> ListWindowsResult:
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

    # "every application process whose ..." is a live query; if a process launches or exits while
    # System Events is iterating it, macOS can raise a transient "Invalid index (-1719)" error.
    # retrying is the standard workaround since the enumeration itself is not reliably atomic.
    max_attempts = 3
    retry_delay = 0.3
    last_error = ''

    for attempt in range(1, max_attempts + 1):
        try:
            proc = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception as e:
            return ListWindowsResult(
                ok=False,
                function='list_windows',
                error=f'{e.__class__.__name__}: {e}',
            )

        if proc.returncode == 0:
            break

        last_error = (proc.stderr or proc.stdout or '').strip()

        if '-1719' not in last_error or attempt == max_attempts:
            return ListWindowsResult(
                ok=False,
                function='list_windows',
                error=last_error,
            )

        ctx.log.debug(f'list_windows attempt {attempt} hit a transient error, retrying: {last_error}')
        time.sleep(retry_delay)

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

        windows.append(WindowInfo(
            index=index,
            app=parts[0].strip(),
            title=parts[1].strip(),
            x=x,
            y=y,
            width=width,
            height=height,
        ))

    return ListWindowsResult(
        ok=True,
        function='list_windows',
        windows=windows,
        count=len(windows),
    )

def ocr_extract(ctx: MTesterContext, image_path: str | Path, region: RegionBox | None = None) -> OcrExtractResult:
    ctx.log.debug(f'mtester.api.ocr_extract called with args: image_path={image_path!r}, region={region}')

    image_path_str = str(image_path)

    if not os.path.exists(image_path_str):
        return OcrExtractResult(
            ok=False,
            function='ocr_extract',
            args={
                'image_path': image_path_str,
                'region': region,
            },
            error=f'Image file not found: {image_path_str}',
        )

    try:
        with Image.open(image_path_str) as source_image:
            working_image = source_image.convert('RGB')

            if region is not None:
                x, y, width, height = region
                if width <= 0 or height <= 0:
                    return OcrExtractResult(
                        ok=False,
                        function='ocr_extract',
                        args={
                            'image_path': image_path_str,
                            'region': region,
                        },
                        error=f'Invalid region size: width={width}, height={height}',
                    )

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

            tokens.append(OcrToken(
                text=text_value,
                left=int(ocr_data['left'][index]),
                top=int(ocr_data['top'][index]),
                width=int(ocr_data['width'][index]),
                height=int(ocr_data['height'][index]),
                confidence=confidence,
            ))

        average_confidence = (sum(conf_values) / len(conf_values)) if conf_values else -1.0

        return OcrExtractResult(
            ok=True,
            function='ocr_extract',
            args={
                'image_path': image_path_str,
                'region': region,
            },
            text=ocr_text.strip(),
            tokens=tokens,
            token_count=len(tokens),
            average_confidence=average_confidence,
        )

    except Exception as e:
        return OcrExtractResult(
            ok=False,
            function='ocr_extract',
            args={
                'image_path': image_path_str,
                'region': region,
            },
            error=f'{e.__class__.__name__}: {e}',
        )

#
# high level services
#

def capture_test_frame(ctx: MTesterContext, name: str | Path, region: RegionBox | None = None, **kwargs) -> CaptureTestFrameResult:

    #
    # init
    #

    extract_ocr = kwargs.get('extract_ocr', True)                      		# whether to run OCR on the captured image
    wait_for_window = kwargs.get('wait_for_window', 0.5)                    # wait this many seconds for the target window to open before capturing the screen

    # wait for window to open #

    time.sleep(wait_for_window)

    #
    # capture screen
    #

    image_path = ctx.test_dir / f'frame_{name}_capture.png'
    capture_result = capture_screen(ctx, output_path=image_path, region=region)

    if not capture_result.ok:
        raise RuntimeError(f"Failed to capture screen: {capture_result.error or 'Unknown error'}")

    if extract_ocr:
        ocr_result = ocr_extract(ctx, image_path=image_path)
        if not ocr_result.ok:
            raise RuntimeError(f"Failed to extract OCR: {ocr_result.error or 'Unknown error'}")
        ocr_debug_path = ctx.test_dir / f'frame_{name}_ocr_result.json'
        with open(ocr_debug_path, 'w+') as f:
            f.write(json_pprint(ocr_result))
    else:
        ocr_result = None

    return CaptureTestFrameResult(
        capture_result=capture_result,
        ocr_result=ocr_result,
    )

def assert_colors_in_regions(
    ctx: MTesterContext,
    image_path: str | Path,
    color_assertions: list[ColorRegionAssertion],
) -> ColorAssertionsResult:
    ctx.log.debug(
        f'mtester.api.assert_colors_in_regions called with args: '
        f'image_path={image_path!r}'
    )

    image_path_str = str(image_path)

    try:
        with Image.open(image_path_str) as source_image:
            image = source_image.convert('RGB')
            image_width, image_height = image.size
            pixels = image.load()

            assertion_results: list[ColorRegionAssertionResult] = []
            for assertion in color_assertions:
                x0 = max(0, assertion.region.x)
                y0 = max(0, assertion.region.y)
                x1 = min(image_width, assertion.region.x + assertion.region.width)
                y1 = min(image_height, assertion.region.y + assertion.region.height)

                if x1 <= x0 or y1 <= y0:
                    assertion_results.append(ColorRegionAssertionResult(
                        name=assertion.name,
                        passed=False,
                        expected_present=assertion.expected_present,
                        found=False,
                        match_count=0,
                        pixel_count=0,
                        match_ratio=0.0,
                        region=assertion.region,
                        color=assertion.color,
                        tolerance=assertion.tolerance,
                    ))
                    continue

                match_count = 0
                pixel_count = (x1 - x0) * (y1 - y0)

                target: PixelRGB = assertion.color
                tolerance = max(0, assertion.tolerance)

                for y in range(y0, y1):
                    for x in range(x0, x1):
                        r, g, b = pixels[x, y]
                        if (
                            abs(r - target.r) <= tolerance
                            and abs(g - target.g) <= tolerance
                            and abs(b - target.b) <= tolerance
                        ):
                            match_count += 1

                found = match_count > 0
                passed = (found == assertion.expected_present)
                match_ratio = (match_count / pixel_count) if pixel_count > 0 else 0.0

                assertion_results.append(ColorRegionAssertionResult(
                    name=assertion.name,
                    passed=passed,
                    expected_present=assertion.expected_present,
                    found=found,
                    match_count=match_count,
                    pixel_count=pixel_count,
                    match_ratio=match_ratio,
                    region=assertion.region,
                    color=assertion.color,
                    tolerance=tolerance,
                ))

        return ColorAssertionsResult(
            ok=all(item.passed for item in assertion_results),
            function='assert_colors_in_regions',
            image_path=image_path_str,
            assertions=assertion_results,
        )

    except Exception as e:
        return ColorAssertionsResult(
            ok=False,
            function='assert_colors_in_regions',
            image_path=image_path_str,
            error=f'{e.__class__.__name__}: {e}',
        )
