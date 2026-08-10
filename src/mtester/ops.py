import json

from typing import Any

from mtester import api
from mtester.context import MTesterContext, MTesterConfig
from mtester.types import RegionBox, json_pprint


def manual_flow(ctx: MTesterContext) -> dict:

    config: MTesterConfig = ctx.config
    
    #
    # run program
    #

    launch_result = api.launch_target(
        command=['python', '-m', 'lingolib', '-v', 'display', config.spec_path],
    )

    mtest_dir = ctx.set_test_dir(test_name='manual_flow', reset=True)

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
    
    if config.select_window or config.window_title:
        windows_result = api.list_windows()
    
        if windows_result.get('ok'):
            windows = windows_result.get('windows', [])

            # interactively select a window if --select-window is specified #

            if config.select_window:
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
                    capture_region = RegionBox(
                        x=selected_window['x'],
                        y=selected_window['y'],
                        width=selected_window['width'],
                        height=selected_window['height'],
                    )

            # select window by title if --window-title is specified #
            
            elif config.window_title:
                filtered_windows = [w for w in windows if config.window_title == w['title']]
                if len(filtered_windows) != 1:
                    raise RuntimeError(f'Expected exactly one window matching title: {config.window_title!r}, found {len(filtered_windows)}')

                selected_window = filtered_windows[0]
                capture_region = RegionBox(
                    x=selected_window['x'],
                    y=selected_window['y'],
                    width=selected_window['width'],
                    height=selected_window['height'],
                )

    elif config.capture_region:
        capture_region = config.capture_region

    #
    # capture screen
    #

    image_path = ctx.test_dir / 'test_frame.png'
    capture_result = api.capture_screen(ctx, output_path=image_path, region=capture_region)
    

    #
    # assertions
    #

    ocr_result = None
    ocr_text_assert_result = None
    if config.assert_ocr_text:
        ocr_result = api.ocr_extract(image_path=image_path)
        ocr_text_assert_result = api.assert_ocr_text(expected=config.assert_ocr_text, image_path=image_path)

    stdout_assert_result = None

    stderr_assert_result = None
    stop_result = api.stop_target(session_id=launch_result.get('session_id', 'manual-session-1'))

    stdout_text = str(stop_result.get('stdout', ''))
    stderr_text = str(stop_result.get('stderr', ''))

    if config.assert_stdout:
        stdout_assert_result = api.assert_stdout(expected=config.assert_stdout, stdout_text=stdout_text)

    if config.assert_stderr:
        stderr_assert_result = api.assert_stderr(expected=config.assert_stderr, stderr_text=stderr_text)

    #
    # output
    #

    full_output = {
        'command': 'manual',
        'spec_path': config.spec_path,
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

    output_path = ctx.test_dir / 'manual_flow_output.json'
    with open(output_path, 'w') as f:
        f.write(json_pprint(full_output))

    # return dict with results #

    if config.verbose:
        return full_output
    else:
        test_keys = ['assert_ocr_text', 'assert_stdout', 'assert_stderr']
        filtered_output = {k: v for k, v in full_output.items() if k in test_keys}
        try:
            del filtered_output['assert_ocr_text']['ocr']['tokens']
        except (KeyError, TypeError):
            pass
        try:
            ocr_text = filtered_output['assert_ocr_text']['ocr']['text']
            filtered_output['assert_ocr_text']['ocr']['text'] = ocr_text[:250] + '...' if len(ocr_text) > 100 else ocr_text
        except (KeyError, TypeError):
            pass
        return filtered_output