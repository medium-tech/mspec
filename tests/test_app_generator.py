#!/usr/bin/env python3
'''
App Generator Tests

This test module verifies that the mtemplate app generator works correctly
by generating, setting up, and testing both py and browser1 applications
from the test-gen.yaml spec file.
'''

import unittest
import shutil
import subprocess
import os
import sys
import time
import datetime
import signal

from pathlib import Path


class TestAppGenerator(unittest.TestCase):
    '''Test the complete app generation workflow'''
    
    def setUp(self):
        '''Set up test environment'''
        self.repo_root = Path(__file__).parent.parent
        self.spec_file = self.repo_root / 'src' / 'mspec' / 'data' / 'test-gen.yaml'
        
        # create tmp directory for tests #

        self.tests_tmp_dir = self.repo_root / 'tests' / 'tmp'
        try:
            shutil.rmtree(self.tests_tmp_dir)
        except FileNotFoundError:
            pass
        self.tests_tmp_dir.mkdir(exist_ok=True)
        
        # create unique directory name #

        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        self.test_dir = self.tests_tmp_dir / f'test_{timestamp}'
        self.test_dir.mkdir(exist_ok=True)
        
    def tearDown(self):
        '''Clean up test environment'''
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_cache(self):
        """
        ensure template caching is working by caching the apps then generating
        with and without cache and comparing the output
        """

        #
        # cache apps
        #

        result = subprocess.run([
            sys.executable, '-m', 'mtemplate', 'cache',
            '--spec', str(self.spec_file),
        ], capture_output=True, text=True, cwd=str(self.repo_root),
          env=dict(os.environ, PYTHONPATH=f'{self.repo_root}/src'))
        
        self.assertEqual(result.returncode, 0, f'Failed to cache app: {result.stderr}')

        #
        # build apps
        #

        # no cache #
        no_cache_dir = self.test_dir / 'no-cache'
        result = subprocess.run([
            sys.executable, '-m', 'mtemplate', 'render',
            '--spec', str(self.spec_file),
            '--output', str(no_cache_dir),
            '--no-cache',
        ], capture_output=True, text=True, cwd=str(self.repo_root),
          env=dict(os.environ, PYTHONPATH=f'{self.repo_root}/src'))
        
        # use cache #
        use_cache_dir = self.test_dir / 'use-cache'
        result = subprocess.run([
            sys.executable, '-m', 'mtemplate', 'render',
            '--spec', str(self.spec_file),
            '--output', str(use_cache_dir),
            '--use-cache',
        ], capture_output=True, text=True, cwd=str(self.repo_root),
          env=dict(os.environ, PYTHONPATH=f'{self.repo_root}/src'))
        
        #
        # compare outputs
        #

        # get recursive file listings #
        no_cache_files = sorted([str(p.relative_to(no_cache_dir)) for p in no_cache_dir.rglob('*') if p.is_file() and p.name != '.env'])
        use_cache_files = sorted([str(p.relative_to(use_cache_dir)) for p in use_cache_dir.rglob('*') if p.is_file() and p.name != '.env'])

        self.assertListEqual(no_cache_files, use_cache_files, 'File listings differ between no-cache and use-cache builds')

        # compare file contents #
        for file_rel_path in no_cache_files:
            no_cache_file = no_cache_dir / file_rel_path
            use_cache_file = use_cache_dir / file_rel_path
            with open(no_cache_file, 'r') as f1, open(use_cache_file, 'r') as f2:
                self.assertEqual(f1.read(), f2.read(), f'File contents differ: {file_rel_path}')

    def test_generate_py_app(self):
        '''Test generating py app from test-gen.yaml and verify structure'''

        #
        # generate the py app
        #

        result = subprocess.run([
            sys.executable, '-m', 'mtemplate', 'render',
            '--app', 'py',
            '--spec', str(self.spec_file),
            '--output', str(self.test_dir),
            '--no-cache'
        ], capture_output=True, text=True, cwd=str(self.repo_root),
          env=dict(os.environ, PYTHONPATH=f'{self.repo_root}/src'))
        
        self.assertEqual(result.returncode, 0, f'Failed to generate py app: {result.stderr}')
        
        # check that key files were generated with proper structure #

        py_files = [
            'pyproject.toml',
            'test.sh',
            'server.sh',
            'src/core/__init__.py',
            'src/core/server.py',
            'src/core/models.py',
            'tests/core/test_auth.py',
            'tests/generated_module_a/test_singular_model.py',
            'tests/generated_module_a/test_plural_model.py',
            'src/generated_module_a/singular_model/model.py',
            'src/generated_module_a/plural_model/model.py'
        ]
        
        for file_path in py_files:
            full_path = Path(self.test_dir) / 'py' / file_path
            self.assertTrue(full_path.exists(), f'Expected file not found: {file_path}')
        
        # pyproject.toml #

        pyproject_path = Path(self.test_dir) / 'py' / 'pyproject.toml'
        with open(pyproject_path, 'r') as f:
            pyproject_content = f.read()
            self.assertIn('name = \'test_gen\'', pyproject_content)
            self.assertIn('uwsgi', pyproject_content)
        
        # test.sh #

        test_sh_path = Path(self.test_dir) / 'py' / 'test.sh'
        self.assertTrue(os.access(test_sh_path, os.X_OK), 'test.sh should be executable')
        with open(test_sh_path, 'r') as f:
            test_content = f.read()
            self.assertIn('python -m unittest', test_content)
        
        # server.sh #

        server_sh_path = Path(self.test_dir) / 'py' / 'server.sh'
        self.assertTrue(os.access(server_sh_path, os.X_OK), 'server.sh should be executable')
        with open(server_sh_path, 'r') as f:
            server_content = f.read()
            self.assertIn('uwsgi', server_content)
        
        # check for template syntax in generated model files #

        model_files = [
            'src/generated_module_a/singular_model/model.py',
            'src/generated_module_a/plural_model/model.py'
        ]
        
        for model_file in model_files:
            model_path = Path(self.test_dir) / 'py' / model_file
            with open(model_path, 'r') as f:
                model_content = f.read()
                self.assertIn('class ', model_content)
                self.assertNotIn('{{', model_content)
                self.assertNotIn('}}', model_content)
    
    def test_generate_browser1_app(self):
        '''Test generating browser1 app from test-gen.yaml and verify structure'''

        # generate the browser1 app #

        result = subprocess.run([
            sys.executable, '-m', 'mtemplate', 'render', 
            '--app', 'browser1',
            '--spec', str(self.spec_file),
            '--output', str(self.test_dir),
            '--no-cache'
        ], capture_output=True, text=True, cwd=str(self.repo_root),
          env=dict(os.environ, PYTHONPATH=f'{self.repo_root}/src'))
        
        self.assertEqual(result.returncode, 0, f'Failed to generate browser1 app: {result.stderr}')
        
        # check that key files were generated with proper structure #

        browser1_files = [
            'package.json',
            'playwright.config.js',
            'srv/index.html',
            'srv/index.js',
            'srv/style.css',
            'tests/generated-module-a/singularModel.spec.js',
            'tests/generated-module-a/pluralModel.spec.js',
            'srv/generated-module-a/singular-model/index.html',
            'srv/generated-module-a/plural-model/index.html'
        ]

        for file_path in browser1_files:
            full_path = Path(self.test_dir) / 'browser1' / file_path
            self.assertTrue(full_path.exists(), f'Expected file not found: {file_path}')
        
        # package.json #

        package_json_path = Path(self.test_dir) / 'browser1' / 'package.json'
        with open(package_json_path, 'r') as f:
            package_content = f.read()
            self.assertIn('"name": "test_gen"', package_content)
            self.assertIn('@playwright/test', package_content)
            self.assertIn('npx playwright test', package_content)
        
        # playwright config #

        playwright_config_path = Path(self.test_dir) / 'browser1' / 'playwright.config.js'
        with open(playwright_config_path, 'r') as f:
            playwright_content = f.read()
            self.assertIn('testDir', playwright_content)
            self.assertIn('./tests', playwright_content)
        
        # HTML files #

        html_files = [
            'srv/index.html',
            'srv/generated-module-a/singular-model/index.html'
        ]
        
        for html_file in html_files:
            html_path = Path(self.test_dir) / 'browser1' / html_file
            with open(html_path, 'r') as f:
                html_content = f.read()
                # Should be valid HTML structure
                self.assertIn('<html', html_content)
                self.assertIn('</html>', html_content)
                # Should not contain unresolved template syntax
                self.assertNotIn('{{', html_content)
                self.assertNotIn('}}', html_content)
        
        # test files #

        test_files = [
            'tests/generated-module-a/singularModel.spec.js',
            'tests/generated-module-a/pluralModel.spec.js'
        ]
        
        for test_file in test_files:
            test_path = Path(self.test_dir) / 'browser1' / test_file
            with open(test_path, 'r') as f:
                test_content = f.read()
                # Should be valid Playwright test
                self.assertIn('test(', test_content)
                self.assertIn('expect(', test_content)
                # Should not contain unresolved template syntax
                self.assertNotIn('{{', test_content)
                self.assertNotIn('}}', test_content)
    
    def test_generate_and_test_both_apps(self):
        '''Test generating both py and browser1 apps together and run their tests'''

        #
        # generate both apps
        #

        result = subprocess.run([
            sys.executable, '-m', 'mtemplate', 'render',
            '--spec', str(self.spec_file),
            '--output', str(self.test_dir),
            '--debug',
            '--no-cache'
        ], capture_output=True, text=True, cwd=str(self.repo_root),
          env=dict(os.environ, PYTHONPATH=f'{self.repo_root}/src'))
        
        self.assertEqual(result.returncode, 0, f'Failed to generate apps: {result.stderr}')
        
        # check that files from both apps were generated in their respective subdirectories #

        py_dir = self.test_dir / 'py'
        browser1_dir = self.test_dir / 'browser1'
        
        expected_files = [
            (py_dir, 'pyproject.toml'),
            (py_dir, 'test.sh'), 
            (py_dir, 'server.sh'),
            (py_dir, 'src/core/__init__.py'),
            
            (browser1_dir, 'package.json'),
            (browser1_dir, 'playwright.config.js'),
            (browser1_dir, 'srv/index.html'),
            (browser1_dir, 'srv/index.js')
        ]
        
        for base_dir, file_path in expected_files:
            full_path = base_dir / file_path
            self.assertTrue(full_path.exists(), f'Expected file not found: {base_dir.name}/{file_path}')
        #
        # app setup
        #
        
        # create virtual environment #

        venv_dir = self.test_dir / 'py' / '.venv'
        venv_result = subprocess.run([
            sys.executable, '-m', 'venv', str(venv_dir), '--upgrade-deps'
        ], capture_output=True, text=True, cwd=str(py_dir))
        
        if venv_result.returncode != 0:
            raise RuntimeError(f'Failed to create venv: {venv_result.stderr}')
        
        python_executable = str(venv_dir / 'bin' / 'python')
        
        # install py dependencies #

        pip_install_result = subprocess.run([
            python_executable, '-m', 'pip', 'install', '-e', '.'
        ], capture_output=True, text=True, cwd=str(py_dir))
        
        if pip_install_result.returncode != 0:
            raise RuntimeError(f'Failed to install Python dependencies: {pip_install_result.stderr}')
        
        # install browser1 dependencies #

        npm_install_result = subprocess.run([
            'npm', 'install'
        ], capture_output=True, text=True, cwd=str(browser1_dir))
        
        if npm_install_result.returncode != 0:
            raise RuntimeError(f'Failed to install npm dependencies: {npm_install_result.stderr}')
        
        #
        # server startup and test execution
        #
        
        server_process = None
        try:

            # check if server.sh exists #

            server_script = py_dir / 'server.sh'
            self.assertTrue(server_script.exists(), 'server.sh should exist')
            
            # create log files for server output to avoid pipe blocking #

            server_log = self.test_dir / 'server.log'
            server_err_log = self.test_dir / 'server_error.log'
            
            # start server #

            with open(server_log, 'w') as stdout_file, open(server_err_log, 'w') as stderr_file:
                server_process = subprocess.Popen([
                    'bash', '-c', server_script.as_posix()
                ], cwd=str(py_dir), 
                   stdout=stdout_file, 
                   stderr=stderr_file,
                   preexec_fn=os.setsid,  # Start in new session to make it daemon-like
                   env=dict(os.environ, VIRTUAL_ENV=venv_dir.as_posix(), PATH=f'{venv_dir / "bin"}:{os.environ.get("PATH", "")}'))

            print(f'Started server with PID {server_process.pid}')
            
            time.sleep(5)   # give the server a moment to start

            # check if the server has started successfully #

            if server_process.poll() is not None:
                with open(server_log, 'r') as f:
                    stdout_content = f.read()
                with open(server_err_log, 'r') as f:
                    stderr_content = f.read()
                raise RuntimeError(f'Server failed to start. stdout: {stdout_content}, stderr: {stderr_content}')

            # run py tests #

            test_script = py_dir / 'test.sh'
            self.assertTrue(test_script.exists(), 'test.sh should exist')
            
            print(f'Running Python tests with command: bash -c {test_script.as_posix()}')
            
            python_test_result = None
            try:
                python_test_result = subprocess.run([
                    'bash', '-c', test_script.as_posix()
                ], capture_output=True, text=True, cwd=str(py_dir), timeout=60, 
                   env=dict(os.environ, VIRTUAL_ENV=venv_dir.as_posix(), 
                           PATH=f'{venv_dir / "bin"}:{os.environ.get("PATH", "")}'))
                
                print(f'Python tests return code: {python_test_result.returncode}')
                print(f'Python tests stdout: {python_test_result.stdout}')
                print(f'Python tests stderr: {python_test_result.stderr}')
                
            except subprocess.TimeoutExpired:
                raise RuntimeError('Python tests timed out')
            
            if python_test_result.returncode != 0:
                raise RuntimeError(f'Python tests failed: {python_test_result.stderr}')
            
            # run browser1 tests #
            
            print(f'Running browser1 tests with command: npm run test')
            browser_test_result = subprocess.run([
                'npm', 'run', 'test'
            ], capture_output=True, text=True, cwd=str(browser1_dir), timeout=60, env=dict(os.environ, VIRTUAL_ENV=venv_dir.as_posix(), PATH=f'{venv_dir / "bin"}:{os.environ.get("PATH", "")}'))

            print(browser_test_result.stdout + browser_test_result.stderr)

            if browser_test_result.returncode != 0:
                raise RuntimeError(f'browser1 tests failed: {browser_test_result.stderr}')

            print('terminating server process')
            if server_process:
                # Terminate the process group to ensure all child processes are killed
                try:
                    os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
                except (OSError, ProcessLookupError):
                    # Process might have already terminated
                    pass
        
        finally:

            # cleanup #

            print('cleaning up server process')
            if server_process:
                try:
                    os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
                    server_process.wait(timeout=5)
                except (OSError, ProcessLookupError, subprocess.TimeoutExpired):
                    try:
                        os.killpg(os.getpgid(server_process.pid), signal.SIGKILL)
                    except (OSError, ProcessLookupError):
                        pass


if __name__ == '__main__':
    unittest.main()