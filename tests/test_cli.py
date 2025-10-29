import unittest
import subprocess
import sys
import json
from pathlib import Path
from mspec.core import load_lingo_script_spec, sample_lingo_script_spec_dir

class TestCLI(unittest.TestCase):
    
    def _run_cli(self, args):
        """Helper method to run the CLI with given arguments"""
        cmd = [sys.executable, '-m', 'mspec'] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result
    
    #
    # specs command
    #
    
    def test_specs_command(self):
        """Test the specs command returns successfully"""
        result = self._run_cli(['specs'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('Builtin browser2 spec files:', result.stdout)
        self.assertIn('Builtin generator spec files:', result.stdout)
        self.assertIn('Builtin mspec lingo script spec files:', result.stdout)
        self.assertGreaterEqual(result.stdout.count('.json'), 4)
        self.assertGreaterEqual(result.stdout.count('.yaml'), 3)
    
    #
    # example command
    #

    def test_example_command_generator(self):
        """Test the example command with test-gen.yaml"""
        result = self._run_cli(['example', 'test-gen.yaml', '--yes'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('Copied example spec file to current directory:', result.stdout)
        
        # Clean up - remove the copied file
        copied_file = Path('test-gen.yaml')
        self.assertTrue(copied_file.exists())
        copied_file.unlink()
    
    def test_example_command_browser2(self):
        """Test the example command with test-page.json"""
        result = self._run_cli(['example', 'test-page.json', '--yes'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('Copied example spec file to current directory:', result.stdout)
        
        # Clean up - remove the copied file
        copied_file = Path('test-page.json')
        self.assertTrue(copied_file.exists())
        copied_file.unlink()

    def test_example_command_lingo_script(self):
        """Test the example command with basic_math.json"""
        result = self._run_cli(['example', 'basic_math.json', '--yes'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('Copied example spec file to current directory:', result.stdout)
        
        # Clean up - remove the copied file
        copied_file = Path('basic_math.json')
        self.assertTrue(copied_file.exists())
        copied_file.unlink()

    def test_example_command_lingo_script_test_data(self):
        """Test the example command with test_data.json"""
        result = self._run_cli(['example', 'basic_math_test_data.json', '--yes'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('Copied example spec file to current directory:', result.stdout)
        
        # Clean up - remove the copied file
        copied_file = Path('basic_math_test_data.json')
        self.assertTrue(copied_file.exists())
        copied_file.unlink()

    def test_example_command_file_exists_no(self):
        """Test the example command when file exists and --no is used"""
        # First, create a dummy file to simulate existing file
        existing_file = Path('test-gen.yaml')
        existing_file.touch()
        
        try:
            result = self._run_cli(['example', 'test-gen.yaml', '--no'])
            self.assertEqual(result.returncode, 0)
            self.assertIn('File already exists, not overwriting:', result.stdout)
            self.assertEqual(existing_file.stat().st_size, 0)

        finally:
            try:
                existing_file.unlink()
            except FileNotFoundError:
                pass

    def test_example_command_file_exists_yes(self):
        """Test the example command when file exists and --yes is used"""
        # First, create a dummy file to simulate existing file
        existing_file = Path('test-gen.yaml')
        existing_file.touch()
        
        try:
            result = self._run_cli(['example', 'test-gen.yaml', '--yes'])
            self.assertEqual(result.returncode, 0)
            self.assertIn('Copied example spec file to current directory:', result.stdout)
        finally:
            # Clean up - remove the dummy file
            try:
                existing_file.unlink()
            except FileNotFoundError:
                pass

    def test_example_command_file_exists_prompt_no(self):
        """Test the example command when file exists and user inputs 'n'"""
        # First, create a dummy file to simulate existing file
        existing_file = Path('test-gen.yaml')
        existing_file.touch()
        
        try:
            # Use subprocess to simulate user input 'n'
            cmd = [sys.executable, '-m', 'mspec', 'example', 'test-gen.yaml']
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(input='n\n')
            self.assertEqual(process.returncode, 1)
            self.assertIn('Aborting copy.', stdout)
        finally:
            # Clean up - remove the dummy file
            try:
                existing_file.unlink()
            except FileNotFoundError:
                pass

    def test_example_command_file_exists_prompt_yes(self):
        """Test the example command when file exists and user inputs 'y'"""
        # First, create a dummy file to simulate existing file
        existing_file = Path('test-gen.yaml')
        existing_file.touch()
        
        try:
            # Use subprocess to simulate user input 'y'
            cmd = [sys.executable, '-m', 'mspec', 'example', 'test-gen.yaml']
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(input='y\n')
            self.assertEqual(process.returncode, 0)
            self.assertIn('Copied example spec file to current directory:', stdout)
        finally:
            # Clean up - remove the dummy file
            try:
                existing_file.unlink()
            except FileNotFoundError:
                pass
    
    #
    # run command
    #

    def test_run_command_functions(self):
        """Test the run command with functions.json"""
        result = self._run_cli(['run', 'functions.json'])
        self.assertEqual(result.returncode, 0)
        # Should output JSON to stdout
        self.assertTrue(len(result.stdout) > 0)

    def test_run_command_return_types(self):
        """Test the run command with return-types.json"""
        result = self._run_cli(['run', 'return-types.json'])
        self.assertEqual(result.returncode, 0)
        # Should output JSON to stdout
        self.assertTrue(len(result.stdout) > 0)
    
    #
    # execute command
    #

    def test_execute_command_all_param_types(self):
        """Test the execute command with all_param_types.json"""
        test_data_path = sample_lingo_script_spec_dir / 'all_param_types_test_data.json'
        with open(test_data_path) as f:
            test_data = json.load(f)

        # test default case #

        result = self._run_cli(['execute', 'all_param_types.json'])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), test_data['results']['default'])

        # test test cases #

        for test_case in test_data['results']['test_cases']:
            params_json = json.dumps(test_case['params'])
            result = self._run_cli(['execute', 'all_param_types.json', '--params', params_json])
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout), test_case['result'])

    #
    # misc cases
    #

    def test_no_command_shows_help(self):
        """Test that running without a command shows help"""
        result = self._run_cli([])
        self.assertEqual(result.returncode, 1)
        self.assertIn('usage:', result.stdout)
    
    def test_invalid_command(self):
        """Test that an invalid command fails gracefully"""
        result = self._run_cli(['invalid'])
        self.assertNotEqual(result.returncode, 0)

if __name__ == '__main__':
    unittest.main()