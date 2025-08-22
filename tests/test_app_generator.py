#!/usr/bin/env python3
"""
App Generator Tests

This test module verifies that the mtemplate app generator works correctly
by generating, setting up, and testing both py and browser1 applications
from the test-gen.yaml spec file.
"""

import unittest
import tempfile
import shutil
import subprocess
import os
import sys
from pathlib import Path


class TestAppGenerator(unittest.TestCase):
    """Test the complete app generation workflow"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.repo_root = Path(__file__).parent.parent
        self.spec_file = self.repo_root / "src" / "mspec" / "data" / "test-gen.yaml"
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_generate_py_app(self):
        """Test generating py app from test-gen.yaml and verify structure"""
        # Generate the py app
        result = subprocess.run([
            sys.executable, "-m", "mtemplate", "render-py",
            "--spec", str(self.spec_file),
            "--output", self.test_dir
        ], capture_output=True, text=True, cwd=str(self.repo_root))
        
        self.assertEqual(result.returncode, 0, f"Failed to generate py app: {result.stderr}")
        
        # Check that key files were generated with proper structure
        py_files = [
            "pyproject.toml",
            "test.sh",
            "server.sh",
            "src/core/__init__.py",
            "src/core/server.py",
            "src/core/models.py",
            "tests/core/test_auth.py",
            "tests/generated_module_a/test_singular_model.py",
            "tests/generated_module_a/test_plural_model.py",
            "src/generated_module_a/singular_model/model.py",
            "src/generated_module_a/plural_model/model.py"
        ]
        
        for file_path in py_files:
            full_path = Path(self.test_dir) / file_path
            self.assertTrue(full_path.exists(), f"Expected file not found: {file_path}")
        
        # Verify pyproject.toml has correct structure
        pyproject_path = Path(self.test_dir) / "pyproject.toml"
        with open(pyproject_path, 'r') as f:
            pyproject_content = f.read()
            self.assertIn('name = \'test_gen\'', pyproject_content)
            self.assertIn('uwsgi', pyproject_content)
        
        # Verify test.sh is executable and has correct content
        test_sh_path = Path(self.test_dir) / "test.sh"
        self.assertTrue(os.access(test_sh_path, os.X_OK), "test.sh should be executable")
        with open(test_sh_path, 'r') as f:
            test_content = f.read()
            self.assertIn('python -m unittest', test_content)
        
        # Verify server.sh is executable and has correct content
        server_sh_path = Path(self.test_dir) / "server.sh"
        self.assertTrue(os.access(server_sh_path, os.X_OK), "server.sh should be executable")
        with open(server_sh_path, 'r') as f:
            server_content = f.read()
            self.assertIn('uwsgi', server_content)
        
        # Verify generated model files have proper Python syntax
        model_files = [
            "src/generated_module_a/singular_model/model.py",
            "src/generated_module_a/plural_model/model.py"
        ]
        
        for model_file in model_files:
            model_path = Path(self.test_dir) / model_file
            with open(model_path, 'r') as f:
                model_content = f.read()
                # Basic syntax check - should contain class definitions
                self.assertIn('class ', model_content)
                # Should not contain template syntax (should be resolved)
                self.assertNotIn('{{', model_content)
                self.assertNotIn('}}', model_content)
    
    def test_generate_browser1_app(self):
        """Test generating browser1 app from test-gen.yaml and verify structure"""
        # Generate the browser1 app
        result = subprocess.run([
            sys.executable, "-m", "mtemplate", "render-browser1", 
            "--spec", str(self.spec_file),
            "--output", self.test_dir
        ], capture_output=True, text=True, cwd=str(self.repo_root))
        
        self.assertEqual(result.returncode, 0, f"Failed to generate browser1 app: {result.stderr}")
        
        # Check that key files were generated with proper structure
        browser1_files = [
            "package.json",
            "playwright.config.js",
            "srv/index.html",
            "srv/index.js",
            "srv/style.css",
            "tests/generated-module-a/singularModel.spec.js",
            "tests/generated-module-a/pluralModel.spec.js",
            "srv/generated-module-a/singular-model/index.html",
            "srv/generated-module-a/plural-model/index.html"
        ]
        
        for file_path in browser1_files:
            full_path = Path(self.test_dir) / file_path
            self.assertTrue(full_path.exists(), f"Expected file not found: {file_path}")
        
        # Verify package.json has correct structure
        package_json_path = Path(self.test_dir) / "package.json"
        with open(package_json_path, 'r') as f:
            package_content = f.read()
            self.assertIn('"name": "test_gen"', package_content)
            self.assertIn('@playwright/test', package_content)
            self.assertIn('npx playwright test', package_content)
        
        # Verify playwright config exists and has proper structure
        playwright_config_path = Path(self.test_dir) / "playwright.config.js"
        with open(playwright_config_path, 'r') as f:
            playwright_content = f.read()
            self.assertIn('testDir', playwright_content)
            self.assertIn('./tests', playwright_content)
        
        # Verify generated HTML files have proper structure
        html_files = [
            "srv/index.html",
            "srv/generated-module-a/singular-model/index.html"
        ]
        
        for html_file in html_files:
            html_path = Path(self.test_dir) / html_file
            with open(html_path, 'r') as f:
                html_content = f.read()
                # Should be valid HTML structure
                self.assertIn('<html', html_content)
                self.assertIn('</html>', html_content)
                # Should not contain unresolved template syntax
                self.assertNotIn('{{', html_content)
                self.assertNotIn('}}', html_content)
        
        # Verify generated test files have proper structure
        test_files = [
            "tests/generated-module-a/singularModel.spec.js",
            "tests/generated-module-a/pluralModel.spec.js"
        ]
        
        for test_file in test_files:
            test_path = Path(self.test_dir) / test_file
            with open(test_path, 'r') as f:
                test_content = f.read()
                # Should be valid Playwright test
                self.assertIn('test(', test_content)
                self.assertIn('expect(', test_content)
                # Should not contain unresolved template syntax
                self.assertNotIn('{{', test_content)
                self.assertNotIn('}}', test_content)
    
    def test_generate_both_apps(self):
        """Test generating both py and browser1 apps together"""
        # Generate both apps using the main render command with debug to prevent deletion
        result = subprocess.run([
            sys.executable, "-m", "mtemplate", "render",
            "--spec", str(self.spec_file),
            "--output", self.test_dir,
            "--debug"
        ], capture_output=True, text=True, cwd=str(self.repo_root))
        
        self.assertEqual(result.returncode, 0, f"Failed to generate apps: {result.stderr}")
        
        # Check that files from both apps were generated
        expected_files = [
            # Python app files
            "pyproject.toml",
            "test.sh", 
            "server.sh",
            "src/core/__init__.py",
            
            # Browser1 app files
            "package.json",
            "playwright.config.js",
            "srv/index.html",
            "srv/index.js"
        ]
        
        for file_path in expected_files:
            full_path = Path(self.test_dir) / file_path
            self.assertTrue(full_path.exists(), f"Expected file not found: {file_path}")
        
        # Verify that both .jinja2 template files exist (debug mode creates them)
        debug_template_files = [
            "pyproject.toml.jinja2",
            "package.json.jinja2"
        ]
        
        for file_path in debug_template_files:
            full_path = Path(self.test_dir) / file_path
            self.assertTrue(full_path.exists(), f"Expected debug template file not found: {file_path}")


if __name__ == "__main__":
    unittest.main()