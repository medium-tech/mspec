import os

#
# funcs
#

def extract_text_via_ocr(source: str) -> str:
	# placeholder implementation #
	return 'placeholder text extracted from OCR'

def detect_colors(source: str) -> dict:
	# placeholder implementation #
	return {
		'green': True,
		'yellow': False,
		'red': False
	}

#
# ops
#

def identify(source: str) -> dict:

	# default results #

	file_exists = os.path.exists(source)
	file_extension = os.path.splitext(source)[1][1:].lower()

	result = {
		'file': {
			'source': source,
			'exists': file_exists,
			'extension': file_extension
		},
		'text': '',
		'colors': {
			'green': False,
			'yellow': False,
			'red': False
		},
		'problems': [],
		'over_all_status': False
	}

	# file details #

	if not file_exists:
		result['problems'].append(f'File not found: {source}')
		return result
	
	if not file_extension in ['png', 'jpg', 'jpeg', 'bmp', 'gif']:
		result['problems'].append(f'Unsupported file type: {file_extension}')
		return result

	# file identification #

	try:
		result['text'] = extract_text_via_ocr(source)
	except Exception as e:
		result['problems'].append(f'OCR extraction failed: {str(e)}')
		
	# color detection #
	try:
		result['colors'] = detect_colors(source)
	except Exception as e:
		result['problems'].append(f'Color detection failed: {str(e)}')


	# analyze results #
	status_color_problem = sum([result['colors']['green'], result['colors']['yellow'], result['colors']['red']]) > 1

	if status_color_problem:
		colors_detected = [color for color, detected in result['colors'].items() if detected]
		err_msg = 'Multiple status colors detected: ' + ', '.join(colors_detected)
		result['problems'].append(err_msg)

	# overall status #
	result['over_all_status'] = len(result['problems']) == 0

	# return results #
	return result
