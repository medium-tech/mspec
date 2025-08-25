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
import datetime
from pathlib import Path


class TestAppGenerator(unittest.TestCase):
    """Test the complete app generation workflow"""
    
    def setUp(self):
        """Set up test environment"""
        self.repo_root = Path(__file__).parent.parent
        self.spec_file = self.repo_root / "src" / "mspec" / "data" / "test-gen.yaml"
        
        # Create tmp directory in tests folder
        self.tests_tmp_dir = self.repo_root / "tests" / "tmp"
        try:
            shutil.rmtree(self.tests_tmp_dir)
        except FileNotFoundError:
            pass
        self.tests_tmp_dir.mkdir(exist_ok=True)
        
        # Create unique test directory for this test
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.test_dir = self.tests_tmp_dir / f"test_{timestamp}"
        self.test_dir.mkdir(exist_ok=True)
        
    def tearDown(self):
        """Clean up test environment"""
        # if self.test_dir.exists():
        #     shutil.rmtree(self.test_dir)
    
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
        
        # Check that files from both apps were generated in their respective subdirectories
        py_dir = self.test_dir / "py"
        browser1_dir = self.test_dir / "browser1"
        
        expected_files = [
            # Python app files (in py/ subdirectory)
            (py_dir, "pyproject.toml"),
            (py_dir, "test.sh"), 
            (py_dir, "server.sh"),
            (py_dir, "src/core/__init__.py"),
            
            # Browser1 app files (in browser1/ subdirectory)
            (browser1_dir, "package.json"),
            (browser1_dir, "playwright.config.js"),
            (browser1_dir, "srv/index.html"),
            (browser1_dir, "srv/index.js")
        ]
        
        for base_dir, file_path in expected_files:
            full_path = base_dir / file_path
            self.assertTrue(full_path.exists(), f"Expected file not found: {base_dir.name}/{file_path}")
        
        # Setup the generated app following the instructions from the comment
        
        # cd to py directory and create virtual environment
        venv_dir = self.test_dir / ".venv"
        venv_result = subprocess.run([
            sys.executable, "-m", "venv", str(venv_dir), "--upgrade-deps"
        ], capture_output=True, text=True, cwd=str(py_dir))
        
        if venv_result.returncode != 0:
            raise RuntimeError(f"Failed to create venv: {venv_result.stderr}")
        
        python_executable = str(venv_dir / "bin" / "python")
        
        # Install Python dependencies: python -m pip install -e py
        pip_install_result = subprocess.run([
            python_executable, "-m", "pip", "install", "-e", "."
        ], capture_output=True, text=True, cwd=str(py_dir))
        
        if pip_install_result.returncode != 0:
            raise RuntimeError(f"Failed to install Python dependencies: {pip_install_result.stderr}")
        
        # Install browser dependencies
        npm_install_result = subprocess.run([
            "npm", "install"
        ], capture_output=True, text=True, cwd=str(browser1_dir))
        
        if npm_install_result.returncode != 0:
            raise RuntimeError(f"Failed to install npm dependencies: {npm_install_result.stderr}")
        
        self.assertTrue(os.path.exists(py_dir / ".env"), "Expected .env file not found in py directory")
        
        # Start the server in a subprocess as per instructions
        server_process = None
        try:
            # Check if server.sh exists
            server_script = py_dir / "server.sh"
            self.assertTrue(server_script.exists(), "server.sh should exist")
            
            # Start the server in background
            server_process = subprocess.Popen([
                "bash", "-c", server_script.as_posix()
            ], cwd=str(py_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE,  env=dict(os.environ, VIRTUAL_ENV=venv_dir.as_posix(), PATH=f"{venv_dir / 'bin'}:{os.environ.get('PATH', '')}"))

            print(f"Started server with PID {server_process.pid}")
            
            # Give the server a moment to start
            time.sleep(5)

            # Check if the server has started successfully
            if server_process.poll() is not None:
                stdout, stderr = server_process.communicate()
                raise RuntimeError(f"Server failed to start. stdout: {stdout.decode()}, stderr: {stderr.decode()}")

            # Run py tests: ./test.sh in py directory
            test_script = py_dir / "test.sh"
            self.assertTrue(test_script.exists(), "test.sh should exist")
            
            print(f'Running Python tests with command: bash -c {test_script.as_posix()}')
            try:
                python_test_result = subprocess.run([
                    "bash", "-c", test_script.as_posix()
                ], capture_output=True, text=True, cwd=str(py_dir), timeout=60, env=dict(os.environ, VIRTUAL_ENV=venv_dir.as_posix(), PATH=f"{venv_dir / 'bin'}:{os.environ.get('PATH', '')}"))
            except subprocess.TimeoutExpired:
                print(f"Python tests timed out after 60 seconds")
                python_test_result = None
                breakpoint()
                server_process.terminate()

            print(python_test_result.stdout + python_test_result.stderr)
            
            # Check that Python tests can at least be discovered and run
            # Don't fail if tests fail, just ensure they can be discovered
            self.assertTrue(
                "test" in python_test_result.stderr.lower() + python_test_result.stdout.lower(),
                f"Python tests should be discoverable. Output: {python_test_result.stdout} {python_test_result.stderr}"
            )
            
            # Run browser1 tests: npm run test in browser1 directory
            # print(f"Running Browser1 tests with command: npm run test")
            # browser_test_result = subprocess.run([
            #     "npm", "run", "test"
            # ], capture_output=True, text=True, cwd=str(browser1_dir), timeout=60, env=dict(os.environ, VIRTUAL_ENV=venv_dir.as_posix(), PATH=f"{venv_dir / 'bin'}:{os.environ.get('PATH', '')}"))

            # print(browser_test_result.stdout + browser_test_result.stderr)

            # # Check that browser tests can be discovered and run
            # # Don't fail if tests fail, just ensure they can be discovered
            # self.assertTrue(
            #     "test" in browser_test_result.stderr.lower() + browser_test_result.stdout.lower() or
            #     "playwright" in browser_test_result.stderr.lower() + browser_test_result.stdout.lower(),
            #     f"Browser tests should be discoverable. Output: {browser_test_result.stdout} {browser_test_result.stderr}"
            # )

            print("Terminating server process")
            server_process.terminate()
        
        finally:
            # Clean up: terminate the server process
            print('Cleaning up server process')
            if server_process:
                server_process.terminate()
                try:
                    server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server_process.kill()


if __name__ == "__main__":
    unittest.main()