from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent
TESTS_TMP_DIR = REPO_ROOT / 'tests' / 'tmp'

if __name__ == '__main__':
	print('hello.world')