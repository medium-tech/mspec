#!/usr/bin/env python3
from pathlib import Path

raise NotImplementedError('This test is incorrectly written - see comment')
"""
it tests the output under ./build but that is not the build output for the packaging process,
it was shown to have a different structure that what ends up in the tar.gz created by the build process.
This test needs to be re-written to use the tarfile library to extract the file listing and contents 
to compare against the source files.
"""

#
# verify mspec data
#

build_mspec_data_dir = Path('./build/lib/mspec/data')
source_mspec_data_dir = Path('./src/mspec/data')

# ensure build mspec data dir exists #
assert build_mspec_data_dir.exists(), f'Build mspec data dir missing: {build_mspec_data_dir}'
assert build_mspec_data_dir.is_dir(), f'Build mspec data dir is not a directory: {build_mspec_data_dir}'

# get recursive file listings #
build_mspec_data_files = sorted([f.relative_to(build_mspec_data_dir) for f in build_mspec_data_dir.rglob('*') if f.is_file()])
source_mspec_data_files = sorted([f.relative_to(source_mspec_data_dir) for f in source_mspec_data_dir.rglob('*') if f.is_file()])

# compare file listings #
if build_mspec_data_files != source_mspec_data_files:
    missing_in_build = [str(f) for f in source_mspec_data_files if f not in build_mspec_data_files]
    extra_in_build = [str(f) for f in build_mspec_data_files if f not in source_mspec_data_files]
    error_msg = 'Mspec data files in build do not match source mspec data files.\n'
    if missing_in_build:
        error_msg += f'Missing in build: {missing_in_build}\n'
    if extra_in_build:
        error_msg += f'Extra in build: {extra_in_build}\n'
    print(error_msg)
    raise Exception('Mspec data file mismatch between build and source.')

# compare file contents #
for file_rel_path in build_mspec_data_files:
    build_file = build_mspec_data_dir / file_rel_path
    source_file = source_mspec_data_dir / file_rel_path
    with build_file.open('r') as f1, source_file.open('r') as f2:
        build_contents = f1.read()
        source_contents = f2.read()
        assert build_contents == source_contents, f'File contents differ for {file_rel_path}'

#
# verify build cache
#

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
    missing_in_build = [str(f) for f in source_cache_files if f not in build_cache_files]
    extra_in_build = [str(f) for f in build_cache_files if f not in source_cache_files]
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
