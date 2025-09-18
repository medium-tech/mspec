#!/usr/bin/env python3
from pathlib import Path

build_cache_dir = Path('./build/lib/mtemplate/.cache')
source_cache_dir = Path('./src/mtemplate/.cache')

# ensure build cache dir exists #
assert build_cache_dir.exists(), f'Build cache dir missing: {build_cache_dir}'
assert build_cache_dir.is_dir(), f'Build cache dir is not a directory: {build_cache_dir}'

# get recursive file listings #
build_cache_files = sorted([f.relative_to(build_cache_dir) for f in build_cache_dir.rglob('*') if f.is_file()])
source_cache_files = sorted([f.relative_to(source_cache_dir) for f in source_cache_dir.rglob('*') if f.is_file()])

# ensure none are .env files #
for file_path in build_cache_files:
    assert not file_path.name == '.env', f'Build cache contains .env file: {file_path}'

for file_path in source_cache_files:
    assert not file_path.name == '.env', f'Source cache contains .env file: {file_path}'

# compare file listings #
if build_cache_files != source_cache_files:
    missing_in_build = [f for f in source_cache_files if f not in build_cache_files]
    extra_in_build = [f for f in build_cache_files if f not in source_cache_files]
    error_msg = 'Cache files in build do not match source cache files.\n'
    if missing_in_build:
        error_msg += f'Missing in build: {missing_in_build}\n'
    if extra_in_build:
        error_msg += f'Extra in build: {extra_in_build}\n'
    print(error_msg)
    raise Exception('Cache file mismatch between build and source.')

# compare file contents #
for file_rel_path in build_cache_files:
    build_file = build_cache_dir / file_rel_path
    source_file = source_cache_dir / file_rel_path
    with build_file.open('r') as f1, source_file.open('r') as f2:
        build_contents = f1.read()
        source_contents = f2.read()
        assert build_contents == source_contents, f'File contents differ for {file_rel_path}'

print('build test: PASSED')
