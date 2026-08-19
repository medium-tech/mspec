import time

from mtester import api
from mtester.context import MTesterContext
from mtester.types import ManualFlowOptions, RegionBox, json_pprint


# def manual_flow(ctx: MTesterContext, options: ManualFlowOptions, wait_for_window: float = 0.5) -> dict:
    
#     #
#     # run program
#     #

#     launch_result = api.launch_target(
#         ctx,
#         command=['python', '-m', 'lingolib', '-v', 'display', options.spec_path],
#     )

#     if ctx.test_dir is None:
#         ctx.set_test_dir(test_name='manual_flow', reset=True)

#     # wait for window to open #

#     # if input('Press Enter after the target window opens') == '':
#     #     pass
#     time.sleep(wait_for_window)

#     #
#     # get capture region (cropping)
#     #
    
#     capture_region = None
#     windows_result = None
#     selected_window = None

#     # crop by window dimensions if --select-window is specified #
    
#     if options.select_window or options.window_title:
#         windows_result = api.list_windows(ctx)
    
#         if windows_result.ok:
#             windows = windows_result.windows

#             # interactively select a window if --select-window is specified #

#             if options.select_window:
#                 if len(windows) == 0:
#                     raise RuntimeError('No windows found to select from')
                
#                 print('\nDetected windows:')
#                 for window in windows:
#                     print(
#                         f'[{window.index}] {window.app} :: {window.title} '
#                         f'@ ({window.x}, {window.y}) {window.width}x{window.height}'
#                     )

#                 raw_index = input('Select window index (Enter for 0): ').strip()
#                 selected_index = int(raw_index) if raw_index != '' else 0
#                 try:
#                     selected_window = windows[selected_index]
#                 except IndexError:
#                     raise RuntimeError(f'Invalid window index: {selected_index}')

#                 if selected_window:
#                     capture_region = RegionBox(
#                         x=selected_window.x,
#                         y=selected_window.y,
#                         width=selected_window.width,
#                         height=selected_window.height,
#                     )

#             # select window by title if --window-title is specified #
            
#             elif options.window_title:
#                 filtered_windows = [w for w in windows if options.window_title == w.title]
#                 if len(filtered_windows) != 1:
#                     raise RuntimeError(f'Expected exactly one window matching title: {options.window_title!r}, found {len(filtered_windows)}')

#                 selected_window = filtered_windows[0]
#                 capture_region = RegionBox(
#                     x=selected_window.x,
#                     y=selected_window.y,
#                     width=selected_window.width,
#                     height=selected_window.height,
#                 )

#     elif options.capture_region:
#         capture_region = options.capture_region

#     #
#     # capture screen
#     #

#     image_path = ctx.test_dir / 'test_frame.png'
#     capture_result = api.capture_screen(ctx, output_path=image_path, region=capture_region)
    
#     #
#     # assertions
#     #

#     ocr_extract = None
#     ocr_text_assert_result = None
#     ocr_not_text_assert_result = None

#     if options.assert_ocr_text or options.assert_not_ocr_text:
#         ocr_extract = api.ocr_extract(ctx, image_path=image_path)
#         ocr_text = ocr_extract.text.lower()

#         if options.assert_ocr_text:
#             ocr_text_assert_result = []
#             for expected_ocr_text in options.assert_ocr_text:
#                 ocr_text_assert_result.append({
#                     'text': expected_ocr_text,
#                     'found': expected_ocr_text.lower() in ocr_text,
#                 })

#         if options.assert_not_ocr_text:
#             ocr_not_text_assert_result = []
#             for unexpected_ocr_text in options.assert_not_ocr_text:
#                 ocr_not_text_assert_result.append({
#                     'text': unexpected_ocr_text,
#                     'not_found': unexpected_ocr_text.lower() not in ocr_text,
#                 })

#     stdout_assert_result = None
#     stdout_not_assert_result = None
#     stderr_assert_result = None
#     stderr_not_assert_result = None

#     stop_result = api.stop_target(ctx, session_id=launch_result.session_id)

#     if options.assert_stdout_text:
#         stdout_assert_result = []
#         stdout_text = stop_result.stdout.lower()
#         for expected_stdout_text in options.assert_stdout_text:
#             stdout_assert_result.append({
#                 'text': expected_stdout_text,
#                 'found': expected_stdout_text.lower() in stdout_text,
#             })

#     if options.assert_not_stdout_text:
#         stdout_not_assert_result = []
#         stdout_text = stop_result.stdout.lower()
#         for unexpected_stdout_text in options.assert_not_stdout_text:
#             stdout_not_assert_result.append({
#                 'text': unexpected_stdout_text,
#                 'not_found': unexpected_stdout_text.lower() not in stdout_text,
#             })

#     if options.assert_stderr_text:
#         stderr_assert_result = []
#         stderr_text = stop_result.stderr.lower()
#         for expected_stderr_text in options.assert_stderr_text:
#             stderr_assert_result.append({
#                 'text': expected_stderr_text,
#                 'found': expected_stderr_text.lower() in stderr_text,
#             })

#     if options.assert_not_stderr_text:
#         stderr_not_assert_result = []
#         stderr_text = stop_result.stderr.lower()
#         for unexpected_stderr_text in options.assert_not_stderr_text:
#             stderr_not_assert_result.append({
#                 'text': unexpected_stderr_text,
#                 'not_found': unexpected_stderr_text.lower() not in stderr_text,
#             })

#     #
#     # output
#     #

#     full_output = {
#         'command': 'manual',
#         'spec_path': options.spec_path,
#         'launch': launch_result,
#         'windows': windows_result,
#         'selected_window': selected_window,
#         'capture': capture_result,
#         'ocr_extract': ocr_extract,
#         'assert_ocr_text': ocr_text_assert_result,
#         'assert_not_ocr_text': ocr_not_text_assert_result,
#         'assert_stdout': stdout_assert_result,
#         'assert_not_stdout': stdout_not_assert_result,
#         'assert_stderr': stderr_assert_result,
#         'assert_not_stderr': stderr_not_assert_result,
#         'stop': stop_result,
#     }

#     # write report to disk #

#     output_path = ctx.test_dir / 'output.json'
#     with open(output_path, 'w') as f:
#         f.write(json_pprint(full_output))

#     # return dict with results #

#     if options.verbose:
#         return full_output
#     else:
#         filtered_output = {k: v for k, v in full_output.items() if k.startswith('assert')}
#         try:
#             del filtered_output['assert_ocr_text']['ocr']['tokens']
#         except (KeyError, TypeError):
#             pass
#         try:
#             expected_ocr_text = filtered_output['assert_ocr_text']['ocr']['text']
#             filtered_output['assert_ocr_text']['ocr']['text'] = expected_ocr_text[:250] + '...' if len(expected_ocr_text) > 100 else expected_ocr_text
#         except (KeyError, TypeError):
#             pass
#         return filtered_output

