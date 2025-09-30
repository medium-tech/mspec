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

from pathlib import Path
from mtemplate import setup_generated_app, run_server_and_app_tests

test_num = 0

QUICK_TEST = os.getenv('QUICK_TEST', '0') == '1'
TEMPLATE_TEST = os.getenv('TEMPLATE_TEST', '0') == '1'
DEV_TEST = os.getenv('DEV_TEST', '0') == '1'

def indent_lines(test, indent=2):
    '''Indent each line of a multi-line string for pretty printing'''
    indentation = '\t' * indent
    return '\n'.join(f'{indentation}{line}' for line in test.splitlines())

class BaseMSpecTest(unittest.TestCase):
    '''Test the complete app generation workflow'''

    repo_root = Path(__file__).parent.parent
    tests_tmp_dir = repo_root / 'tests' / 'tmp'

    @classmethod
    def setUpClass(cls):
        '''run before any tests in class to remove old tmp test dirs'''
        try:
            shutil.rmtree(cls.tests_tmp_dir)
        except FileNotFoundError:
            pass

        cls.tests_tmp_dir.mkdir(exist_ok=True)
    
    def setUp(self):
        '''run before each test to create unique test dir'''
        
        # create unique directory name #
        global test_num
        self.test_dir = self.tests_tmp_dir / f'test_{test_num}'
        test_num += 1
        self.test_dir.mkdir(exist_ok=True)
        self.run_cleanup = False

    def tearDown(self):
        if self.run_cleanup:
            try:
                shutil.rmtree(self.test_dir)
            except Exception as e:
                print('\t* failed to remove test directory:', self.test_dir, e)

    def _test_cache(self, spec_file:str):
        """
        ensure template caching is working by caching the apps then generating
        with and without cache and comparing the output
        """

        #
        # cache apps
        #

        result = subprocess.run([
            sys.executable, '-m', 'mtemplate', 'cache',
            '--spec', str(spec_file),
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
            '--spec', str(spec_file),
            '--output', str(no_cache_dir),
            '--no-cache',
        ], capture_output=True, text=True, cwd=str(self.repo_root),
          env=dict(os.environ, PYTHONPATH=f'{self.repo_root}/src'))
        
        # use cache #
        use_cache_dir = self.test_dir / 'use-cache'
        result = subprocess.run([
            sys.executable, '-m', 'mtemplate', 'render',
            '--spec', str(spec_file),
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

    def _test_debug_mode(self, spec_file:str):
        """
        + ensure debug mode outputs a jinja2 template for each rendered file
        + ensure the generated app is the same as without debug mode when ignoring
          the .jinja2 files
        
        """

        #
        # build apps
        #

        # normal #
        normal_dir = self.test_dir / 'normal'
        result = subprocess.run([
            sys.executable, '-m', 'mtemplate', 'render',
            '--spec', str(spec_file),
            '--output', str(normal_dir),
            '--no-cache',
        ], capture_output=True, text=True, cwd=str(self.repo_root),
          env=dict(os.environ, PYTHONPATH=f'{self.repo_root}/src'))
        
        self.assertEqual(result.returncode, 0, f'Failed to generate app without debug: {result.stderr}')

        # debug #
        debug_no_cache_dir = self.test_dir / 'debug'
        result = subprocess.run([
            sys.executable, '-m', 'mtemplate', 'render',
            '--spec', str(spec_file),
            '--output', str(debug_no_cache_dir),
            '--debug',
            '--no-cache',
        ], capture_output=True, text=True, cwd=str(self.repo_root),
          env=dict(os.environ, PYTHONPATH=f'{self.repo_root}/src'))
        
        self.assertEqual(result.returncode, 0, f'Failed to generate app with debug and no cache: {result.stderr}')

        # debug with cache #
        debug_cache_dir = self.test_dir / 'debug-cache'
        result = subprocess.run([
            sys.executable, '-m', 'mtemplate', 'render',
            '--spec', str(spec_file),
            '--output', str(debug_cache_dir),
            '--debug',
            '--use-cache',
        ], capture_output=True, text=True, cwd=str(self.repo_root),
          env=dict(os.environ, PYTHONPATH=f'{self.repo_root}/src'))
        
        self.assertEqual(result.returncode, 0, f'Failed to generate app with debug and cache: {result.stderr}')
        
        #
        # compare outputs
        #

        # get recursive file listings #
        normal_files = sorted([str(p.relative_to(normal_dir)) for p in normal_dir.rglob('*') if p.is_file() and p.name != '.env'])
        debug_no_cache_files = sorted([str(p.relative_to(debug_no_cache_dir)) for p in debug_no_cache_dir.rglob('*') if p.is_file() and p.name != '.env' and not p.name.endswith('.jinja2')])
        debug_cache_files = sorted([str(p.relative_to(debug_cache_dir)) for p in debug_cache_dir.rglob('*') if p.is_file() and p.name != '.env' and not p.name.endswith('.jinja2')])

        self.assertListEqual(normal_files, debug_no_cache_files, 'File listings differ between normal and debug builds (ignoring .jinja2 files)')
        self.assertListEqual(normal_files, debug_cache_files, 'File listings differ between normal and debug-cache builds (ignoring .jinja2 files)')

        # compare file contents to normal files #
        for file_rel_path in normal_files:
            normal_file = normal_dir / file_rel_path
            debug_no_cache_file = debug_no_cache_dir / file_rel_path
            debug_cache_file = debug_cache_dir / file_rel_path

            with open(normal_file, 'r') as f1, open(debug_no_cache_file, 'r') as f2, open(debug_cache_file, 'r') as f3:
                file_1_contents = f1.read()
                self.assertEqual(file_1_contents, f2.read(), f'File contents differ: {file_rel_path}')
                self.assertEqual(file_1_contents, f3.read(), f'File contents differ: {file_rel_path}')

        # check each debug no cache has a corresponding .jinja2 file #
        for file_rel_path in debug_no_cache_files:
            debug_no_cache_file = debug_no_cache_dir / file_rel_path
            jinja2_file = debug_no_cache_file.with_name(debug_no_cache_file.name + '.jinja2')
            self.assertTrue(jinja2_file.exists(), f'Missing .jinja2 debug file for: {file_rel_path}')

        # check each debug cache has a corresponding .jinja2 file #
        for file_rel_path in debug_cache_files:
            debug_cache_file = debug_cache_dir / file_rel_path
            jinja2_file = debug_cache_file.with_name(debug_cache_file.name + '.jinja2')
            self.assertTrue(jinja2_file.exists(), f'Missing .jinja2 debug file for: {file_rel_path}')

    def _render_spec(self, spec_file:str):
        result = subprocess.run([
            sys.executable, '-m', 'mtemplate', 'render',
            '--spec', str(spec_file),
            '--output', str(self.test_dir),
            '--debug',
            '--no-cache'
        ], capture_output=True, text=True, cwd=str(self.repo_root),
          env=dict(os.environ, PYTHONPATH=f'{self.repo_root}/src'))
        
        self.assertEqual(result.returncode, 0, f'Failed to generate apps: {result.stderr}')

    def _test_generate_and_test_both_apps(self, spec_file:str):
        self._render_spec(spec_file)
        setup_generated_app(self.test_dir)
        run_server_and_app_tests(self.test_dir)

class TestTestGenSpec(BaseMSpecTest):
    '''Test the complete app generation workflow'''

    repo_root = Path(__file__).parent.parent
    spec_file = repo_root / 'src' / 'mspec' / 'data' / 'test-gen.yaml'
    tests_tmp_dir = repo_root / 'tests' / 'tmp'

    def test_cache(self):
        self._test_cache(self.spec_file)
        self.run_cleanup = True
    
    def test_debug_mode(self):
        self._test_debug_mode(self.spec_file)
        self.run_cleanup = True

    @unittest.skipIf(QUICK_TEST or TEMPLATE_TEST, "Skipping app test")
    def test_generate_and_test_both_apps(self):
        self._test_generate_and_test_both_apps(self.spec_file)
        self.run_cleanup = True

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

        self.run_cleanup = True
    
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

        self.run_cleanup = True
    

class TestSampleStoreSpec(BaseMSpecTest):
    '''Test the complete app generation workflow'''

    repo_root = Path(__file__).parent.parent
    spec_file = repo_root / 'src' / 'mspec' / 'data' / 'my-sample-store.yaml'
    tests_tmp_dir = repo_root / 'tests' / 'tmp'

    def test_cache(self):
        self._test_cache(self.spec_file)
        self.run_cleanup = True

    def test_debug_mode(self):
        self._test_debug_mode(self.spec_file)
        self.run_cleanup = True

    @unittest.skipIf(DEV_TEST or QUICK_TEST or TEMPLATE_TEST, "Skipping app test for dev/quick/template test mode")
    def test_generate_and_test_both_apps(self):
        self._test_generate_and_test_both_apps(self.spec_file)
        self.run_cleanup = True

class TestSimpleSocialSpec(BaseMSpecTest):
    '''Test the complete app generation workflow'''

    repo_root = Path(__file__).parent.parent
    spec_file = repo_root / 'src' / 'mspec' / 'data' / 'simple-social-network.yaml'
    tests_tmp_dir = repo_root / 'tests' / 'tmp'

    def test_cache(self):
        self._test_cache(self.spec_file)
        self.run_cleanup = True

    def test_debug_mode(self):
        self._test_debug_mode(self.spec_file)
        self.run_cleanup = True

    @unittest.skipIf(DEV_TEST or QUICK_TEST or TEMPLATE_TEST, "Skipping app test for dev/quick/template test mode")
    def test_generate_and_test_both_apps(self):
        self._test_generate_and_test_both_apps(self.spec_file)
        self.run_cleanup = True

class TestTemplateSourceApps(BaseMSpecTest):

    repo_root = Path(__file__).parent.parent

    def setUp(self):
        '''run before each test to create unique test dir'''
        self.test_dir = self.repo_root / 'templates'
        self.run_cleanup = False

    @unittest.skipIf(DEV_TEST or QUICK_TEST, "Skipping app test for dev/quick test mode")
    def test_run_template_source_apps(self):
        '''Test generating and running all template source apps'''
        venv_dir = self.repo_root / '.venv'
        if not venv_dir.exists():
            raise RuntimeError(f'venv does not exist: {venv_dir.absolute()}, follow dev environment setup instructions in README.md')
        
        run_server_and_app_tests(self.test_dir, venv_dir)

        # delete server logs if they exist

        to_delete = [
            self.test_dir / 'unittest-server.log',
            self.test_dir / 'unittest-server-error.log'
        ]

        for path in to_delete:
            try:
                path.unlink()
            except FileNotFoundError:
                pass

        self.run_cleanup = False  # ensure we do not delete the templates directory

if __name__ == '__main__':
    unittest.main()
