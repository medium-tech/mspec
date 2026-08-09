import json

from typing import Any

from mtester import api
from mtester.api import capture_screen, launch_target, stop_target, mtester_dir


def run_flow(flow_path: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    print(f'mtester.api.run_flow called with args: flow_path={flow_path}, variables={variables}')

    variables = variables or {}
    command = variables.get('command', ['python', '-m', 'lingolib', 'display', flow_path])
    cwd = variables.get('cwd')
    env = variables.get('env')
    region = variables.get('region')
    force_stop = variables.get('force_stop', False)

    launch_result = launch_target(command=command, cwd=cwd, env=env)
    session_id = launch_result.get('session_id', '')

    capture_result = None
    stop_result = None

    try:
        capture_result = capture_screen(region=region)
    finally:
        if session_id:
            stop_result = stop_target(session_id=session_id, force=force_stop)

    return {
        'ok': True,
        'function': 'run_flow',
        'args': {
            'flow_path': flow_path,
            'variables': variables,
        },
        'launch': launch_result,
        'capture': capture_result,
        'stop': stop_result,
    }


def manual_flow(args) -> dict:
    # PoC execution flow: launch target, capture screenshot, run optional assertions, then stop target.
    launch_result = api.launch_target(
        command=['python', '-m', 'lingolib', '-v', 'display', args.spec],
    )

    mtest_dir = api.mtester_dir(reset=True)

    if input('Press Enter after the target window opens') == '':
        pass

    windows_result = api.list_windows()

    selected_window_result = None
    capture_result = None

    if windows_result.get('ok'):
        windows = windows_result.get('windows', [])
        if len(windows) > 0:
            print('\nDetected windows:')
            for window in windows:
                print(
                    f"[{window['index']}] {window['app']} :: {window['title']} "
                    f"@ ({window['x']}, {window['y']}) {window['width']}x{window['height']}"
                )

            raw_index = input('Select window index (Enter for 0): ').strip()
            selected_index = int(raw_index) if raw_index != '' else 0
            selected_window_result = api.select_window(windows=windows, index=selected_index)

            if selected_window_result.get('ok'):
                selected_window = selected_window_result['selected']
                region = (
                    selected_window['x'],
                    selected_window['y'],
                    selected_window['width'],
                    selected_window['height'],
                )
                capture_result = api.capture_screen(region=region)

    if capture_result is None:
        # Fallback for non-macOS or window-listing failures.
        capture_result = api.capture_screen()

    image_path = capture_result.get('image_path', '')

    ocr_result = None
    ocr_text_assert_result = None
    if args.assert_ocr_text:
        ocr_result = api.ocr_extract(image_path=image_path)
        ocr_text_assert_result = api.assert_ocr_text(expected=args.assert_ocr_text, image_path=image_path)

    stdout_assert_result = None

    stderr_assert_result = None
    stop_result = api.stop_target(session_id=launch_result.get('session_id', 'manual-session-1'))

    stdout_text = str(stop_result.get('stdout', ''))
    stderr_text = str(stop_result.get('stderr', ''))

    if args.assert_stdout:
        stdout_assert_result = api.assert_stdout(expected=args.assert_stdout, stdout_text=stdout_text)

    if args.assert_stderr:
        stderr_assert_result = api.assert_stderr(expected=args.assert_stderr, stderr_text=stderr_text)

    full_output = {
        'command': 'manual',
        'spec': args.spec,
        'launch': launch_result,
        'windows': windows_result,
        'selected_window': selected_window_result,
        'capture': capture_result,
        'ocr_extract': ocr_result,
        'assert_ocr_text': ocr_text_assert_result,
        'assert_stdout': stdout_assert_result,
        'assert_stderr': stderr_assert_result,
        'stop': stop_result,
    }

    output_path = mtest_dir / 'manual_flow_output.json'
    with open(output_path, 'w') as f:
        json.dump(full_output, f, indent=4, sort_keys=True)

    if args.verbose:
        return full_output
    else:
        test_keys = ['assert_ocr_text', 'assert_stdout', 'assert_stderr']
        filtered_output = {k: v for k, v in full_output.items() if k in test_keys}
        try:
            del filtered_output['assert_ocr_text']['ocr']['tokens']
        except KeyError:
            pass
        try:
            ocr_text = filtered_output['assert_ocr_text']['ocr']['text']
            filtered_output['assert_ocr_text']['ocr']['text'] = ocr_text[:250] + '...' if len(ocr_text) > 100 else ocr_text
        except KeyError:
            pass
        return filtered_output