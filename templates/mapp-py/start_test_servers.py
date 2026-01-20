#!/usr/bin/env python3
"""
Start test servers for Playwright UI testing.

This script sets up and starts the CRUD and pagination test servers
without running any tests. The servers will run until interrupted.
"""

import os
import sys
import signal
import subprocess
import shutil
import re
from pathlib import Path

# Add the mspec source to the path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / 'src'))

from mspec.core import load_generator_spec
from mapp.test import env_to_string
from dotenv import dotenv_values
import time

def start_servers(use_cache=False):
    """Start the test servers for UI testing."""
    
    test_dir = 'mapp-tests'
    spec_file = 'dev-app.yaml'
    env_file = '.env'
    cmd = ['./run.sh']
    
    # Load spec
    spec = load_generator_spec(spec_file)
    
    # Setup test directory
    if not use_cache:
        shutil.rmtree(test_dir, ignore_errors=True)
    os.makedirs(test_dir, exist_ok=True)
    
    # Database files
    crud_db_file = Path(f'{test_dir}/test_crud_db.sqlite3')
    pagination_db_file = Path(f'{test_dir}/test_pagination_db.sqlite3')
    
    # Always delete crud DB
    if crud_db_file.exists():
        crud_db_file.unlink()
    
    pagination_db_exists = pagination_db_file.exists()
    
    # Load base environment
    env_vars = dotenv_values(env_file)
    
    # Create CRUD environment
    default_host = spec['client']['default_host']
    default_port = int(default_host.split(':')[-1])
    crud_port = default_port + 1
    crud_env = dict(env_vars)
    crud_env['MAPP_SERVER_PORT'] = str(crud_port)
    crud_env['MAPP_CLIENT_HOST'] = f'http://localhost:{crud_port}'
    crud_env['MAPP_DB_URL'] = str(crud_db_file.resolve())
    crud_env.pop('DEBUG_DELAY', None)
    
    crud_envfile = Path(f'{test_dir}/crud.env')
    with open(crud_envfile, 'w') as f:
        f.write(env_to_string(crud_env))
    
    crud_ctx = os.environ.copy()
    crud_ctx['MAPP_ENV_FILE'] = str(crud_envfile.resolve())
    crud_ctx.update(crud_env)
    
    # Create pagination environment
    pagination_port = default_port + 2
    pagination_env = dict(env_vars)
    pagination_env['MAPP_SERVER_PORT'] = str(pagination_port)
    pagination_env['MAPP_CLIENT_HOST'] = f'http://localhost:{pagination_port}'
    pagination_env['MAPP_DB_URL'] = str(pagination_db_file.resolve())
    pagination_env.pop('DEBUG_DELAY', None)
    
    pagination_envfile = Path(f'{test_dir}/pagination.env')
    with open(pagination_envfile, 'w') as f:
        f.write(env_to_string(pagination_env))
    
    pagination_ctx = os.environ.copy()
    pagination_ctx['MAPP_ENV_FILE'] = str(pagination_envfile.resolve())
    pagination_ctx.update(pagination_env)
    
    print(':: Creating database tables')
    
    # Create CRUD tables
    crud_create_cmd = cmd + ['create-tables']
    result = subprocess.run(crud_create_cmd, capture_output=True, text=True, env=crud_ctx)
    if result.returncode != 0:
        print(f'Error creating CRUD tables: {result.stdout + result.stderr}')
        sys.exit(1)
    
    # Create pagination tables
    pagination_create_cmd = cmd + ['create-tables']
    result = subprocess.run(pagination_create_cmd, capture_output=True, text=True, env=pagination_ctx)
    if result.returncode != 0:
        print(f'Error creating pagination tables: {result.stdout + result.stderr}')
        sys.exit(1)
    
    print(f':: Environment files created:')
    print(f'   CRUD: {crud_envfile} ({crud_env["MAPP_CLIENT_HOST"]})')
    print(f'   Pagination: {pagination_envfile} ({pagination_env["MAPP_CLIENT_HOST"]})')
    print()
    
    # Create uwsgi config files
    print(':: Creating uwsgi config files')
    
    with open('uwsgi.yaml', 'r') as f:
        uwsgi_config = f.read()
    
    port_pattern = r'http:\s*:\d+'
    pid_file_pattern = r'safe-pidfile:\s*.+'
    stats_pattern = r'stats:\s*.+'
    logto_pattern = r'logto:\s*.+'
    
    crud_pidfile = f'{test_dir}/uwsgi_crud.pid'
    pagination_pidfile = f'{test_dir}/uwsgi_pagination.pid'
    crud_stats_socket = f'{test_dir}/stats_crud.socket'
    crud_log_file = f'{test_dir}/server_crud.log'
    crud_uwsgi_config_file = f'{test_dir}/uwsgi_crud.yaml'
    
    pagination_uwsgi_config_file = f'{test_dir}/uwsgi_pagination.yaml'
    pagination_stats_socket = f'{test_dir}/stats_pagination.socket'
    pagination_log_file = f'{test_dir}/server_pagination.log'
    
    # CRUD config
    with open(crud_uwsgi_config_file, 'w') as f:
        crud_uwsgi_config = re.sub(port_pattern, f'http: :{crud_port}', uwsgi_config)
        crud_uwsgi_config = re.sub(pid_file_pattern, f'safe-pidfile: {crud_pidfile}', crud_uwsgi_config)
        crud_uwsgi_config = re.sub(stats_pattern, f'stats: {crud_stats_socket}', crud_uwsgi_config)
        crud_uwsgi_config = re.sub(logto_pattern, f'logto: {crud_log_file}', crud_uwsgi_config)
        f.write(crud_uwsgi_config)
    
    # Pagination config
    with open(pagination_uwsgi_config_file, 'w') as f:
        pagination_uwsgi_config = re.sub(port_pattern, f'http: :{pagination_port}', uwsgi_config)
        pagination_uwsgi_config = re.sub(pid_file_pattern, f'safe-pidfile: {pagination_pidfile}', pagination_uwsgi_config)
        pagination_uwsgi_config = re.sub(stats_pattern, f'stats: {pagination_stats_socket}', pagination_uwsgi_config)
        pagination_uwsgi_config = re.sub(logto_pattern, f'logto: {pagination_log_file}', pagination_uwsgi_config)
        f.write(pagination_uwsgi_config)
    
    # Start servers
    print(':: Starting servers')
    
    # Use server.sh script with custom config files
    crud_server_cmd = ['./server.sh', '--pid-file', crud_pidfile, '--config', crud_uwsgi_config_file]
    pagination_server_cmd = ['./server.sh', '--pid-file', pagination_pidfile, '--config', pagination_uwsgi_config_file]
    
    server_processes = []
    
    crud_process = subprocess.Popen(
        crud_server_cmd, 
        env=crud_ctx,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    server_processes.append(('CRUD', crud_process, crud_env['MAPP_CLIENT_HOST']))
    print(f'   CRUD server started: {crud_env["MAPP_CLIENT_HOST"]} (PID: {crud_process.pid})')
    
    pagination_process = subprocess.Popen(
        pagination_server_cmd,
        env=pagination_ctx,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    server_processes.append(('Pagination', pagination_process, pagination_env['MAPP_CLIENT_HOST']))
    print(f'   Pagination server started: {pagination_env["MAPP_CLIENT_HOST"]} (PID: {pagination_process.pid})')
    
    print()
    print(':: Servers running. Press Ctrl+C to stop.')
    print()
    
    # Handle shutdown gracefully
    def signal_handler(sig, frame):
        print('\n:: Shutting down servers...')
        for name, process, host in server_processes:
            print(f'   Stopping {name} server (PID: {process.pid})')
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print(f'   Force killing {name} server')
                process.kill()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Wait for servers to exit
    while True:
        time.sleep(1)
        for name, process, host in server_processes:
            if process.poll() is not None:
                print(f'\n:: {name} server exited unexpectedly with code {process.returncode}')
                stdout, stderr = process.communicate()
                print(f'STDOUT:\n{stdout}')
                print(f'STDERR:\n{stderr}')
                sys.exit(1)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Start test servers for Playwright UI testing')
    parser.add_argument('--use-cache', action='store_true', help='Use cached test resources')
    args = parser.parse_args()
    
    start_servers(use_cache=args.use_cache)
