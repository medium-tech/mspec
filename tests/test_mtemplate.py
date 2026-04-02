import unittest
import shutil
import subprocess
import os
import sys

from pathlib import Path

from .core import REPO_ROOT, TESTS_TMP_DIR

test_num = 0

# to disable cleanup and inspect output, use: export TEST_CLEANUP=0
TEST_CLEANUP = os.getenv('TEST_CLEANUP', '1') == '1'

def should_have_jinja(filepath:str) -> bool:
    if os.path.splitext(filepath)[1] in ['.jpg', '.png', '.pdf']:
        return False
    elif filepath.endswith('mapp.yaml'):
        return False
    else:
        return True

class BaseMSpecTest(unittest.TestCase):
    '''Test the complete app generation workflow'''
    
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        '''run before any tests in class to remove old tmp test dirs'''
        try:
            shutil.rmtree(TESTS_TMP_DIR)
        except FileNotFoundError:
            pass

        TESTS_TMP_DIR.mkdir(exist_ok=True)
    
    def setUp(self):
        '''run before each test to create unique test dir'''
        
        # create unique directory name #
        global test_num
        self.test_dir = TESTS_TMP_DIR / f'test_{test_num}'
        test_num += 1
        self.test_dir.mkdir(exist_ok=True)
        self.run_cleanup = False

    def tearDown(self):
        if self.run_cleanup and TEST_CLEANUP:
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
        ], capture_output=True, text=True, cwd=str(REPO_ROOT),
          env=dict(os.environ, PYTHONPATH=f'{REPO_ROOT}/src'))
        
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
        ], capture_output=True, text=True, cwd=str(REPO_ROOT),
          env=dict(os.environ, PYTHONPATH=f'{REPO_ROOT}/src'))
        
        # use cache #
        use_cache_dir = self.test_dir / 'use-cache'
        result = subprocess.run([
            sys.executable, '-m', 'mtemplate', 'render',
            '--spec', str(spec_file),
            '--output', str(use_cache_dir),
            '--use-cache',
        ], capture_output=True, text=True, cwd=str(REPO_ROOT),
          env=dict(os.environ, PYTHONPATH=f'{REPO_ROOT}/src'))
        
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
            with open(no_cache_file, 'rb') as f1, open(use_cache_file, 'rb') as f2:
                self.assertEqual(f1.read(), f2.read(), f'File contents differ: {file_rel_path}')

    def _test_debug(self, spec_file:str):
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
        ], capture_output=True, text=True, cwd=str(REPO_ROOT),
          env=dict(os.environ, PYTHONPATH=f'{REPO_ROOT}/src'))
        
        self.assertEqual(result.returncode, 0, f'Failed to generate app without debug: {result.stderr}')

        # debug #
        debug_no_cache_dir = self.test_dir / 'debug'
        result = subprocess.run([
            sys.executable, '-m', 'mtemplate', 'render',
            '--spec', str(spec_file),
            '--output', str(debug_no_cache_dir),
            '--debug',
            '--no-cache',
        ], capture_output=True, text=True, cwd=str(REPO_ROOT),
          env=dict(os.environ, PYTHONPATH=f'{REPO_ROOT}/src'))
        
        self.assertEqual(result.returncode, 0, f'Failed to generate app with debug and no cache: {result.stderr}')

        # debug with cache #
        debug_cache_dir = self.test_dir / 'debug-cache'
        result = subprocess.run([
            sys.executable, '-m', 'mtemplate', 'render',
            '--spec', str(spec_file),
            '--output', str(debug_cache_dir),
            '--debug',
            '--use-cache',
        ], capture_output=True, text=True, cwd=str(REPO_ROOT),
          env=dict(os.environ, PYTHONPATH=f'{REPO_ROOT}/src'))
        
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

            with open(normal_file, 'rb') as f1, open(debug_no_cache_file, 'rb') as f2, open(debug_cache_file, 'rb') as f3:
                file_1_contents = f1.read()
                self.assertEqual(file_1_contents, f2.read(), f'File contents differ: {file_rel_path}')
                self.assertEqual(file_1_contents, f3.read(), f'File contents differ: {file_rel_path}')

        # check each debug no cache has a corresponding .jinja2 file #
        for file_rel_path in debug_no_cache_files:
            if not should_have_jinja(file_rel_path):
                continue

            debug_no_cache_file = debug_no_cache_dir / file_rel_path
            jinja2_file = debug_no_cache_file.with_name(debug_no_cache_file.name + '.jinja2')
            self.assertTrue(jinja2_file.exists(), f'Missing .jinja2 debug file for: {file_rel_path}')

        # check each debug cache has a corresponding .jinja2 file #
        for file_rel_path in debug_cache_files:
            if not should_have_jinja(file_rel_path):
                continue

            debug_cache_file = debug_cache_dir / file_rel_path
            jinja2_file = debug_cache_file.with_name(debug_cache_file.name + '.jinja2')
            self.assertTrue(jinja2_file.exists(), f'Missing .jinja2 debug file for: {file_rel_path}')

    def _render(self, spec_file:str):
        result = subprocess.run([
            sys.executable, '-m', 'mtemplate', 'render',
            '--spec', str(spec_file),
            '--output', str(self.test_dir),
            '--no-cache'
        ], capture_output=True, text=True, cwd=str(REPO_ROOT),
          env=dict(os.environ, PYTHONPATH=f'{REPO_ROOT}/src'))
        
        self.assertEqual(result.returncode, 0, f'Failed to generate apps: {result.stderr}')


class TestSimpleSocialSpec(BaseMSpecTest):
    '''Test the complete app generation workflow'''

    spec_file = REPO_ROOT / 'src' / 'mspec' / 'data' / 'generator' / 'sosh-net.yaml'
    
    def test_cache(self):
        self._test_cache(self.spec_file)
        self.run_cleanup = True
    
    def test_debug(self):
        self._test_debug(self.spec_file)
        self.run_cleanup = True
    
    def test_render(self):
        self._render(self.spec_file)
        self.run_cleanup = True

        expected_files = """
		seed.sh
		server.py
		tests/file_sys_and_media.spec.js
		tests/crud.spec.js
		tests/op.spec.js
		tests/README.md
		tests/samples/splash-high.jpg
		tests/samples/lorem-document.pdf
		tests/samples/splash-orig.png
		tests/samples/splash-low.jpg
		tests/auth.spec.js
		tests/fixtures.js
		tests/app.spec.js
		tests/pagination.spec.js
		playwright.config.js
		run.sh
		README.md
		server.sh
		.gitignore
		package.json
		uwsgi.yaml
		root.py
		test.sh
        mapp.yaml
		"""

        expected_files = sorted([line.strip() for line in expected_files.strip().splitlines()])
        actual_files = sorted([str(p.relative_to(self.test_dir)) for p in self.test_dir.rglob('*') if p.is_file() and p.name != '.env'])
        self.assertListEqual(expected_files, actual_files, 'Generated files do not match expected files')
