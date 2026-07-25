import json
import unittest
import subprocess

class TestMTester(unittest.TestCase):
	"""
	unittests for mtester python module cli.
	"""

	def _cli(self, args, exit_code=0, decode_json=True):
		result = subprocess.run(['python', '-m', 'mtester'] + args, capture_output=True, text=True)
		self.assertEqual(result.returncode, exit_code, f'Expected exit code {exit_code}, got {result.returncode}. Stderr: {result.stderr}')
		if decode_json:
			return json.loads(result.stdout)
		else:
			return result.stdout
		
	def test_cli_help(self):
		result = self._cli(['--help'], exit_code=0, decode_json=False)
		self.assertIn('usage:', result)
		
	def test_cli_identify_nonexistent_file(self):
		result = self._cli(['identify', 'nonexistent.png'], exit_code=0)
		self.assertFalse(result['file']['exists'])
		self.assertIn('File not found', result['problems'][0])

	def test_cli_identify_text_dark_green(self):
		sources = [
			# 'src/mtester/samples/txt/dark/GREEN.jpg',
			'src/mtester/samples/txt/dark/GREEN.png'
		]
		for source in sources:
			with self.subTest(source=source):
				result = self._cli(['identify', source], exit_code=0)

				self.assertTrue(result['file']['exists'])
				self.assertEqual(result['file']['extension'], source.split('.')[-1])

				self.assertIn('this text has the color', result['text'])

				self.assertTrue(result['colors']['green'])
				self.assertFalse(result['colors']['yellow'])
				self.assertFalse(result['colors']['red'])

				self.assertTrue(len(result['problems']) == 0)
				self.assertTrue(result['over_all_status'])

	def test_cli_identify_text_dark_yellow(self):
		sources = [
			# 'src/mtester/samples/txt/dark/YELLOW.jpg',
			'src/mtester/samples/txt/dark/YELLOW.png'
		]
		for source in sources:
			with self.subTest(source=source):
				result = self._cli(['identify', source], exit_code=0)

				self.assertTrue(result['file']['exists'])
				self.assertEqual(result['file']['extension'], source.split('.')[-1])

				self.assertIn('this text has the color', result['text'])

				self.assertFalse(result['colors']['green'])
				self.assertTrue(result['colors']['yellow'])
				self.assertFalse(result['colors']['red'])

				self.assertTrue(len(result['problems']) == 0)
				self.assertTrue(result['over_all_status'])

	def test_cli_identify_text_dark_red(self):
		sources = [
			# 'src/mtester/samples/txt/dark/RED.jpg',
			'src/mtester/samples/txt/dark/RED.png'
		]
		for source in sources:
			with self.subTest(source=source):
				result = self._cli(['identify', source], exit_code=0)

				self.assertTrue(result['file']['exists'])
				self.assertEqual(result['file']['extension'], source.split('.')[-1])

				self.assertIn('this text has the color', result['text'])

				self.assertFalse(result['colors']['green'])
				self.assertFalse(result['colors']['yellow'])
				self.assertTrue(result['colors']['red'])

				self.assertTrue(len(result['problems']) == 0)
				self.assertTrue(result['over_all_status'])

	def test_cli_identify_text_dark_text(self):
		sources = [
			'src/mtester/samples/txt/dark/TEXT.jpg',
			'src/mtester/samples/txt/dark/TEXT.png'
		]
		for source in sources:
			with self.subTest(source=source):
				result = self._cli(['identify', source], exit_code=0)

				self.assertTrue(result['file']['exists'])
				self.assertEqual(result['file']['extension'], source.split('.')[-1])

				self.assertIn('this is a rendering with text.', result['text'])

				self.assertTrue(len(result['problems']) == 0)
				self.assertTrue(result['over_all_status'])

	def test_cli_identify_txt_dark_problem(self):
		sources = [
			'src/mtester/samples/txt/dark/PROBLEM.jpg',
			'src/mtester/samples/txt/dark/PROBLEM.png'
		]
		expected_txt = 'oh-no! the ui shouldn\'t render more than 1 of the status colors:'
		for source in sources:
			with self.subTest(source=source):
				result = self._cli(['identify', source], exit_code=0)

				self.assertTrue(result['file']['exists'])
				self.assertEqual(result['file']['extension'], source.split('.')[-1])

				self.assertIn(expected_txt, result['text'])

				self.assertTrue(result['colors']['green'])
				self.assertTrue(result['colors']['yellow'])
				self.assertTrue(result['colors']['red'])

				self.assertTrue(len(result['problems']) > 0)
				self.assertEqual(result['problems'][0], 'Multiple status colors detected: red, green, yellow')
				self.assertFalse(result['over_all_status'])