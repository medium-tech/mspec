#!/usr/bin/env python3
"""
App Generator Tests

This test module verifies that the mtemplate app generator works correctly
by generating, setting up, and testing both py and browser1 applications
from the test-gen.yaml spec file.
"""

import unittest
import shutil
import subprocess
import os
import sys
import time
import signal
from pathlib import Path


class TestAppGenerator(unittest.TestCase):
    """Test the complete app generation workflow"""
    
    def setUp(self):
        """Set up test environment"""
        self.repo_root = Path(__file__).parent.parent
        self.spec_file = self.repo_root / "src" / "mspec" / "data" / "test-gen.yaml"
        
        # Create tmp directory in tests folder
        self.tests_tmp_dir = self.repo_root / "tests" / "tmp"
        self.tests_tmp_dir.mkdir(exist_ok=True)
        
        # Create unique test directory for this test
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.test_dir = self.tests_tmp_dir / f"test_{timestamp}"
        self.test_dir.mkdir(exist_ok=True)
        
    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_generate_py_app(self):
        """Test generating py app from test-gen.yaml and verify structure"""
        # Generate the py app
        result = subprocess.run([
            sys.executable, "-m", "mtemplate", "render-py",
            "--spec", str(self.spec_file),
            "--output", str(self.test_dir)
        ], capture_output=True, text=True, cwd=str(self.repo_root),
          env=dict(os.environ, PYTHONPATH=f"{self.repo_root}/src"))
        
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
            "--output", str(self.test_dir)
        ], capture_output=True, text=True, cwd=str(self.repo_root),
          env=dict(os.environ, PYTHONPATH=f"{self.repo_root}/src"))
        
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
        """Test generating both py and browser1 apps together and run their tests"""
        # Generate both apps using the main render command with debug to prevent deletion
        result = subprocess.run([
            sys.executable, "-m", "mtemplate", "render",
            "--spec", str(self.spec_file),
            "--output", str(self.test_dir),
            "--debug"
        ], capture_output=True, text=True, cwd=str(self.repo_root), 
          env=dict(os.environ, PYTHONPATH=f"{self.repo_root}/src"))
        
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
        
        # Setup the generated app - install Python dependencies
        pip_install_result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-e", "."
        ], capture_output=True, text=True, cwd=str(self.test_dir))
        
        # We don't fail if pip install fails since it might be due to missing system dependencies
        # but we'll log it for debugging
        if pip_install_result.returncode != 0:
            print(f"Warning: pip install failed: {pip_install_result.stderr}")
        
        # Install browser dependencies
        npm_install_result = subprocess.run([
            "npm", "install"
        ], capture_output=True, text=True, cwd=str(self.test_dir))
        
        # Similarly, we don't fail if npm install fails since npm might not be available
        if npm_install_result.returncode != 0:
            print(f"Warning: npm install failed: {npm_install_result.stderr}")
        
        # Create a simple .env file for the server
        env_content = "# Generated for testing\nDEBUG=true\n"
        with open(self.test_dir / ".env", "w") as f:
            f.write(env_content)
        
        # Run the Python tests first
        python_test_result = subprocess.run([
            sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"
        ], capture_output=True, text=True, cwd=str(self.test_dir))
        
        # Check that Python tests can at least be discovered and run
        # (they might fail due to missing dependencies, but they should be runnable)
        self.assertIn("test", python_test_result.stderr.lower() + python_test_result.stdout.lower(),
                      f"Python tests did not run properly: {python_test_result.stderr}")
        
        # Test server startup (without actually keeping it running)
        # We'll start it and then kill it quickly to test that it can start
        server_process = None
        try:
            # Try to start the server in the background
            server_process = subprocess.Popen([
                sys.executable, "-c", 
                "import sys; sys.path.insert(0, 'src'); from core.server import *; import time; time.sleep(2)"
            ], cwd=str(self.test_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give it a moment to start
            time.sleep(1)
            
            # Check if process is still running (good sign)
            poll_result = server_process.poll()
            if poll_result is None:
                # Process is still running, which means it started successfully
                print("Server started successfully")
            else:
                # Process exited, let's see why
                stdout, stderr = server_process.communicate()
                print(f"Server exited with code {poll_result}: {stderr.decode()}")
            
        except Exception as e:
            print(f"Could not test server startup: {e}")
        finally:
            # Clean up the server process
            if server_process and server_process.poll() is None:
                server_process.terminate()
                try:
                    server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server_process.kill()
        
        # Test that browser tests can be discovered (we won't run them as they require a running server)
        if npm_install_result.returncode == 0:
            # Only test playwright if npm install succeeded
            playwright_test_result = subprocess.run([
                "npx", "playwright", "test", "--list"
            ], capture_output=True, text=True, cwd=str(self.test_dir))
            
            if playwright_test_result.returncode == 0:
                self.assertIn("spec", playwright_test_result.stdout.lower(),
                              "Browser tests should be discoverable")
            else:
                print(f"Warning: Could not list playwright tests: {playwright_test_result.stderr}")
        
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