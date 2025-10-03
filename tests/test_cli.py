import unittest
import subprocess
import sys
from pathlib import Path

class TestCLI(unittest.TestCase):
    
    def _run_cli(self, args):
        """Helper method to run the CLI with given arguments"""
        cmd = [sys.executable, '-m', 'mspec'] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result
    
    def test_specs_command(self):
        """Test the specs command returns successfully"""
        result = self._run_cli(['specs'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('Builtin browser2 spec files:', result.stdout)
        self.assertIn('Builtin mspec template app spec files:', result.stdout)
        self.assertGreaterEqual(result.stdout.count('.json'), 3)
        self.assertGreaterEqual(result.stdout.count('.yaml'), 3)
    
    def test_show_command_yaml(self):
        """Test the show command with test-gen.yaml"""
        result = self._run_cli(['show', 'test-gen.yaml'])
        self.assertEqual(result.returncode, 0)
        # Should output JSON to stdout
        self.assertTrue(len(result.stdout) > 0)
    
    def test_show_command_json(self):
        """Test the show command with test-page.json"""
        result = self._run_cli(['show', 'test-page.json'])
        self.assertEqual(result.returncode, 0)
        # Should output JSON to stdout
        self.assertTrue(len(result.stdout) > 0)
    
    def test_example_command_yaml(self):
        """Test the example command with test-gen.yaml"""
        result = self._run_cli(['example', 'test-gen.yaml'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('Copied example spec file to current directory:', result.stdout)
        
        # Clean up - remove the copied file
        copied_file = Path('test-gen.yaml')
        self.assertTrue(copied_file.exists())
        copied_file.unlink()
    
    def test_example_command_json(self):
        """Test the example command with test-page.json"""
        result = self._run_cli(['example', 'test-page.json'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('Copied example spec file to current directory:', result.stdout)
        
        # Clean up - remove the copied file
        copied_file = Path('test-page.json')
        self.assertTrue(copied_file.exists())
        copied_file.unlink()
    
    def test_run_command_functions(self):
        """Test the run command with functions.json"""
        result = self._run_cli(['run', 'functions.json'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('Running run command with spec:', result.stdout)
        # Should output JSON to stdout
        self.assertTrue(len(result.stdout) > 0)

    def test_run_command_return_types(self):
        """Test the run command with return-types.json"""
        result = self._run_cli(['run', 'return-types.json'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('Running run command with spec:', result.stdout)
        # Should output JSON to stdout
        self.assertTrue(len(result.stdout) > 0)
    
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