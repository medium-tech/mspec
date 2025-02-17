# mprotocol

### setup dev environment

    python3 -m venv .venv --upgrade-deps
    source .venv/bin/activate
    pip install -e .
    pip install -e templates/py/


# Roadmap

🔴 = not started

🟡 = started

🟢 = finished

### prototype (python backend + html browser gui)

* 🟢 python unittests passing
* 🟢 no cache for quick reloading of html files
* 🟢 javascript/browser ui
    * 🟢 pagination
    * 🟢 create
    * 🟢 read
    * 🟢 update
    * 🟢 delete
    * 🟢 standardize urls (- vs _) and naming (sample vs. msample)
    * 🟢 refactor code layout to prepare for more template projects
    * 🟢 create js ui tests
        * 🟢 refactor to:
            * templates/html
                * srv/
                    * index.html
                    * ...
                * test/
                    * ...
                * package.json
        * 🟢 create tests

* 🟢 templating
    * 🟢 refactor `src/sample/__init__.py` -> `src/sample/sample_item/__init__.py`
    * 🟢 extract templates
        * 🟢 add macro syntax
        * 🟢 add insert syntax
    * 🟢 generate py
    * 🟢 generate html
    * 🟢 generated app should have 2 modules and 3 total models, but not sample.sample_item
    * 🟢 add html/css template extraction
    * 🟢 add json template extraction
    * 🟢 refactor template apps so that module and model names are both 2 words which enables proper templating for kebab-case, etc
    * 🟢 template app and generated apps unittests are passing

    * 🟢 refactor client / db modules
    * 🟢 decouple db/client from global ns
    * 🟢 add convience classes for db/client
        * 🟢 in `sample/__init__.py` - alias db and client functions from `sample/db.py` and `sample/client.py`
        * 🟢 in `core/db.py` and `core/client.py` - alias client and db classes from `sample/__init__.py`
    * 🟢 rename example_item.age and example_item.name because those field names conflict with templating code
    * 🟡 add auth/users/profile support
        * 🟢 client/server unittests for profile/user
        * 🟢 onboarding working, new user/profile/password
        * 🟢 login workflow
        * 🔴 add root authorzation
        * 🔴 add auth to profile endpoints
        * 🔴 add salt to pw
        * 🔴 add login sessions/logout
    * 🔴 refactor sample_module to match core module
        * 🔴 remove logic from __init__.py
        * 🔴 remove random generator logic
        * 🔴 remove convenience logic (ie. sample_module_db)
    * 🔴 add cid to example_item

### guis

* 🔴 blender markup viewer
    * 🔴 heading (1 level to keep simple at first)
        * 🔴 paragraph
        * 🔴 lists
        * 🔴 model widgets
            * 🔴 create
            * 🔴 read
            * 🔴 update
            * 🔴 delete
            * 🔴 list
        * 🔴 expressions
            * 🔴 is true/false
            * 🔴 add/subtract
            * 🔴 datetime.now

* 🔴 html (browser) markup viewer
    * 🔴 heading (1 level to keep simple at first)
    * 🔴 paragraph
    * 🔴 lists
    * 🔴 model widgets
        * 🔴 create
        * 🔴 read
        * 🔴 update
        * 🔴 delete
        * 🔴 list
    * 🔴 expressions
        * 🔴 is true/false
        * 🔴 add/subtract
        * 🔴 datetime.now

* 🟡 python tkinter
    * 🟢 index
    * 🟢 module index
    * 🟢 model
        * 🟢 index
        * 🟡 instance
            * 🟡 list
            * 🟡 instance
                * 🟡 create
                * 🟡 read
                * 🟡 update
                * 🟡 delete
    * 🔴 template extraction 
    * 🔴 unittests
    * 🔴 make network requests async

    * 🔴 markup viewer
        * 🔴 heading (1 level to keep simple at first)
        * 🔴 paragraph
        * 🔴 lists
        * 🔴 model widgets
            * 🔴 create
            * 🔴 read
            * 🔴 update
            * 🔴 delete
            * 🔴 list
        * 🔴 expressions
            * 🔴 is true/false
            * 🔴 add/subtract
            * 🔴 datetime.now

* 🔴 c 
    * 🔴 index
    * 🔴 sample index
    * 🔴 sample item
        * 🔴 list
        * 🔴 instance
            * 🔴 create
            * 🔴 read
            * 🔴 update
            * 🔴 delete

* 🔴 Gio UI (go lang) https://gioui.org

* 🔴 micro controller guis
    * 🔴 razz pi pico: https://www.youtube.com/watch?v=KSYjGul84aU&t=819s

### servers
* 🔴 go
    * 🔴 index
    * 🔴 sample index
    * 🔴 sample item
        * 🔴 list
        * 🔴 instance
            * 🔴 create
            * 🔴 read
            * 🔴 update
            * 🔴 delete

## additional protocol/app features
* 🔴 content ids
* 🔴 date and time types
* 🔴 string format email
* 🔴 users / auth
* 🔴 profiles
* 🔴 files
* 🔴 sqlite