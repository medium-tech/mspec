import os

import pytesseract
from PIL import Image

#
# funcs
#

def extract_text_via_ocr(image) -> str:
	"""pass in a pillow image and return the extracted text"""
	return pytesseract.image_to_string(image).lower().strip()

def detect_colors(image) -> dict:
    """Detects if the image contains green, yellow, or red (with shade tolerance)."""
    # Downsample for speed
    small_img = image.convert('RGB').resize((64, 64))
    pixels = list(small_img.getdata())

    found = {'red': False, 'green': False, 'yellow': False}

    for r, g, b in pixels:
        # Red: high R, low G/B
        if r > 150 and g < 100 and b < 100:
            found['red'] = True
        # Green: high G, low R/B
        elif g > 150 and r < 100 and b < 100:
            found['green'] = True
        # Yellow: high R and G, low B
        elif r > 150 and g > 150 and b < 100:
            found['yellow'] = True

        # Early exit if all found
        if all(found.values()):
            break

    return found

#
# ops
#

def identify(source: str) -> dict:

	# default results #

	result = {
		'file': {
			'source': source,
			'exists': False,
			'extension': ''
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
	try:
		result['file']['exists'] = os.path.exists(source)
	except Exception as e:
		result['problems'].append(f'Error stating file: {e.__class__.__name__}: {e}')
		return result

	if not result['file']['exists']:
		result['problems'].append(f'File not found: {source}')
		return result
	
	file_extension = os.path.splitext(source)[1][1:].lower()
	result['file']['extension'] = file_extension
	
	if not file_extension in ['png', 'jpg', 'jpeg', 'bmp', 'gif']:
		result['problems'].append(f'Unsupported file type: {file_extension}')
		return result
	
	# load image #
	try:
		image = Image.open(source)
	except Exception as e:
		result['problems'].append(f'Failed to load image: {e.__class__.__name__}: {e}')
		return result

	# text extraction #
	try:
		result['text'] = extract_text_via_ocr(image)
	except Exception as e:
		result['problems'].append(f'OCR extraction failed: {e.__class__.__name__}: {e}')
		
	# color detection #
	try:
		result['colors'] = detect_colors(image)
	except Exception as e:
		result['problems'].append(f'Color detection failed: {e.__class__.__name__}: {e}')


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
