#!/usr/bin/env python3
import os

"""
a find and replace tool that looks for strings to replace in both file paths and file contents
"""

terms = {
    'test model': 'single model',
    'test_model': 'single_model',
    'test-model': 'single-model',
    'testModel': 'singleModel',
    'TestModel': 'SingleModel'
}

def replace_terms(s:str) -> str:
    for old, new in terms.items():
        s = s.replace(old, new)
    return s

def main(root:str, dry_run:bool):
    for dirpath, dirnames, filenames in os.walk(root):
        if '__pycache__' in dirpath:
            continue

        if 'egg-info' in dirpath:
            continue

        if 'node_modules' in dirpath:
            continue

        if 'playwright-report' in dirpath:
            continue

        if 'test-results' in dirpath:
            continue

        for filename in filenames:
            if filename == '.DS_Store':
                continue
            if filename.endswith('.sqlite3'):
                continue
            if filename == 'renamer.py':
                continue
            if filename == '.env':
                continue

            filepath = os.path.join(dirpath, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
                raise

            # perform find and replace
            new_content = replace_terms(content)
            if dry_run:
                if new_content != content:
                    print(f'replace:   {filepath}')
                else:
                    print(f'no change: {filepath}')
            else:
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(new_content)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Find and replace tool')
    parser.add_argument('--root', help='Root directory to start renaming from', default='.')
    parser.add_argument('--dry-run', action='store_true', help='Show changes that would be made')
    args = parser.parse_args()

    main(args.root, args.dry_run)