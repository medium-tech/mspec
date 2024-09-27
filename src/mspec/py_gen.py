#!/usr/bin/env python3
import mspec

def render_py():
    dist_dir = mspec.dist_dir / 'py'
    print(f'py: {dist_dir}')

"""

dist/
    py/
        pyproject.toml
        src/
            sample/
                __init__.py
                __main__.py
                server.py
                client.py
                    + create
                    + read
                    + update
                    + delete
                    + list
                db.py
                    + create
                    + read
                    + update
                    + delete
                    + list
                data.py
                    + verify
                    + from_json
                    + to_json

    html/
        src/
            style.css
            index.html
            sample/
                index.html     (list)
                create.html
                read.html      (read + delete)
"""

# entry points #

def py_server():
    pass

def py_cli():
    pass

# data #

def py_verify():
    pass

def py_from_json():
    pass

def py_to_json():
    pass

# db #

def py_db_create():
    pass

def py_db_read():
    pass

def py_db_update():
    pass

def py_db_delete():
    pass

def py_db_list():
    pass