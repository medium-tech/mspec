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

    #
    # run program
    #

    launch_result = api.launch_target(
        command=['python', '-m', 'lingolib', '-v', 'display', args.spec],
    )

    mtest_dir = api.mtester_dir(reset=True)

    # wait for window to open #

    if input('Press Enter after the target window opens') == '':
        pass

    #
    # get capture region (cropping)
    #
    
    capture_region = None
    windows_result = None
    selected_window = None

    # crop by window dimensions if --select-window is specified #

    if args.capture_region and args.select_window:
        raise RuntimeError('Cannot supply both --capture-region and --select-window')
    elif args.select_window or args.window_title:
        windows_result = api.list_windows()
    
        if windows_result.get('ok'):
            windows = windows_result.get('windows', [])

            # interactively select a window if --select-window is specified #

            if args.select_window:
                if len(windows) == 0:
                    raise RuntimeError('No windows found to select from')
                
                print('\nDetected windows:')
                for window in windows:
                    print(
                        f"[{window['index']}] {window['app']} :: {window['title']} "
                        f"@ ({window['x']}, {window['y']}) {window['width']}x{window['height']}"
                    )

                raw_index = input('Select window index (Enter for 0): ').strip()
                selected_index = int(raw_index) if raw_index != '' else 0
                try:
                    selected_window = windows[selected_index]
                except IndexError:
                    raise RuntimeError(f'Invalid window index: {selected_index}')

                if selected_window:
                    capture_region = (
                        selected_window['x'],
                        selected_window['y'],
                        selected_window['width'],
                        selected_window['height'],
                    )

            # select window by title if --window-title is specified #
            
            elif args.window_title:
                filtered_windows = [w for w in windows if args.window_title == w['title']]
                if len(filtered_windows) != 1:
                    raise RuntimeError(f'Expected exactly one window matching title: {args.window_title!r}, found {len(filtered_windows)}')

                selected_window = filtered_windows[0]
                capture_region = (
                    selected_window['x'],
                    selected_window['y'],
                    selected_window['width'],
                    selected_window['height'],
                )

    elif args.capture_region:
        try:
            x, y, width, height = map(int, args.capture_region.split(','))
            capture_region = (x, y, width, height)
        except ValueError:
            raise RuntimeError('Invalid --capture-region format. Expected: x,y,width,height')

    #
    # capture screen
    #

    capture_result = api.capture_screen(region=capture_region)
    image_path = capture_result['image_path']

    #
    # assertions
    #

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

    #
    # output
    #

    full_output = {
        'command': 'manual',
        'spec': args.spec,
        'launch': launch_result,
        'windows': windows_result,
        'selected_window': selected_window,
        'capture': capture_result,
        'ocr_extract': ocr_result,
        'assert_ocr_text': ocr_text_assert_result,
        'assert_stdout': stdout_assert_result,
        'assert_stderr': stderr_assert_result,
        'stop': stop_result,
    }

    # write report to disk #

    output_path = mtest_dir / 'manual_flow_output.json'
    with open(output_path, 'w') as f:
        json.dump(full_output, f, indent=4, sort_keys=True)

    # return dict with results #

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