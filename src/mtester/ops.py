from mtester import api
from mtester.api import capture_screen, launch_target, stop_target


from typing import Any


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

    if input('Press Enter when window is ready to capture') == '':
        pass

    capture_result = api.capture_screen()
    image_path = capture_result.get('image_path', '')

    ocr_result = None
    text_assert_result = None
    if args.ocr_extract:
        ocr_result = api.ocr_extract(image_path=image_path)
        text_assert_result = api.assert_text(expected=args.ocr_extract, image_path=image_path)

    stdout_assert_result = None
    if args.assert_stdout:
        stdout_assert_result = api.assert_stdout(expected=args.assert_stdout, stdout_text='')

    stderr_assert_result = None
    if args.assert_stderr:
        stderr_assert_result = api.assert_stderr(expected=args.assert_stderr, stderr_text='')

    stop_result = api.stop_target(session_id=launch_result.get('session_id', 'manual-session-1'))

    return {
        'command': 'manual',
        'spec': args.spec,
        'launch': launch_result,
        'capture': capture_result,
        'ocr_extract': ocr_result,
        'assert_text': text_assert_result,
        'assert_stdout': stdout_assert_result,
        'assert_stderr': stderr_assert_result,
        'stop': stop_result,
    }