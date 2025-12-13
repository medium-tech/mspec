# Roadmap

## projects

* [main prototype](#main-template-prototype)
* [python template app](#python-template-app)
* [browser1 template app](#browser-1-template-app)
* [go template app](#go-template-app)
* [c template app](#c-template-app)
* [haskell template app](#haskell-template-app)
* [browser 2.0 clients](#browser-20-clients)
* [low code node based gui](#low-code-node-based-gui)

### status colors
|not started|in progress|finished|
|--|--|--|
|🔴|🟡|🟢|

## mapp framework
* 🟢 create tests for auth via cli
* 🟢 all unittests passing
* 🟡 auth - finish integration + tests
    * 🟢 server auth
    * 🟢 cli db auth
    * 🟢 cli http auth
    * 🟢 create 2 users for crud ctx during setup
        * 🟢 ensure user a cannot delete/update items from user b
    * 🔴 max models tests
        * 🔴 add test case of max of 0 models
* 🔴 serve hello world lingo page from server
    * 🔴 lingo index page
        * 🔴 lingo module page
            * 🔴 lingo model page
                * 🔴 create
                * 🔴 read
                * 🔴 update
                * 🔴 delete
                * 🔴 list
            * 🔴 lingo op page
                * 🔴 run
* 🔴 export static site
* 🔴 lingo model (see below)

## main template prototype
The main prototype are the python + browser 1 browser template apps.

### lingo
* 🟢 move sample apps from bl-mspec-dev
    * 🟢 add tests to ensure correct outputs are generated
* 🟢 add lists
    * 🟢 map
    * 🟢 slice
    * 🟢 filter
    * 🟢 count
    * 🟢 drop while
    * 🟢 take while
* 🔴 models
    * 🔴 read
    * 🔴 list / paginate
    * 🔴 ui forms for create/update/delete
* 🟡 refactor internal api
    * 🟢 rename mspec/markup.py to lingo.py
    * 🔴 rename `render_output` to `lingo_render`
    * 🔴 rename remaining `render_*` functions to `execute_*`
    * 🟡 separate pages and scripts, currenlty both use `output` to define their result, but execute should use `main` and render should use `output`
    * 🔴 migrate `mtemplate/__init__.py` logic to `mtemplate/core.py`
* 🔴 add background tasks 
    * 🔴 timers similar to blender's app timers
    * 🔴 scheduled (cron style)
* 🔴 add hook functions
    * 🔴 startup
    * 🔴 after_first_render
    * 🔴 shutdown
 
### template app phase 1
* 🟡 python full featured template app
    * 🟡 auth for models
        * 🟡 require login to create a model
        * 🟡 limit number of models created by user in spec file (ie. user can only create 1 profile)
        * 🔴 model read op can be public or private
            * 🔴 hardcoded in spec file
            * 🔴 user can choose if model is public or private
            * 🔴 user can create acl for read ops
        * 🔴 revist python password implementation
            * `bcrypt` 5.0 broke implementation, migrate stdlib alternatives (https://docs.python.org/3/library/hashlib.html#hashlib.scrypt) as described in description: https://pypi.org/project/bcrypt/
        * 🔴 implement oauth

    * 🔴 add foreign key id as model field type
    * 🔴 add meta to models
    * 🔴 add file ingest/upload
        * 🔴 file sql table
        * 🔴 add model field type: file
        * 🔴 ingest
            * 🔴 py client
            * 🔴 py server/http client
            * 🔴 browser 1
        * 🔴 read
            * 🔴 py client
            * 🔴 py server/http client
            * 🔴 browser 1
        * 🔴 add multipart uploads
    * 🔴 implement cids
        * 🔴 template apps
            * 🔴 add cid sql table
                * 🔴 row contains foreign key to file
                * 🔴 row can contain foreign key to model table
        * 🔴 browser2
            * 🔴 page to page links
            * 🔴 retrieving/viewing files
            * 🔴 retrieving/viewing model data
    * 🔴 more types
        * 🔴 multi-dimensional arrays
        * 🔴 date and time
            * 🔴 date
            * 🔴 time
            * 🔴 any of datetime, date or time
* 🟢 browser 1 app
    * 🟢 gui
        * 🟢 crud/list
        * 🟢 auth

* 🔴 go app
    * 🔴 sqlite interface
    * 🔴 server
        * 🔴 db wrapper
        * 🔴 auth
        * 🔴 serve browser1 html

### phase 2
* 🟡 python app
    * 🟡 refactor python vs. templating logic
        * 🟢 enable nested loops and if branching
        * 🟢 add macro by type function for calling a macro dynamically
        * 🟡 migrate macros written in python to template syntax
            * 🟡 py app
            * 🟡 browser1 app
        * 🔴 revist python template app, re: single_model vs. multi_model, templates and macros
        * 🟡 create system to sync template changes to macro only templates (ex: copy changes from `./single_model/db.py` to `./mutlti_model/db.py`)
            * load files `./single_model/db.py` and `./mutlti_model/db.py` (if exists)
            * the parent template is used to render a child based on a yaml model
                * render everything except for undefined macros (existing macros in `./mutlti_model/db.py` should be undefined at this point)

### phase 3

* 🔴 haskell template app
* 🔴 c template app



### misc
* 🟡 performance testing
* 🔴 clean up whitespace in generated apps

## python template app
* 🟢 sqlite3 client
    * 🟢 core   (`templates/py/src/core/db.py`)
        * 🟢 create tables
        * 🟢 user crud ops
        * 🟢 profile crud ops
    * 🟢 model (`templates/py/src/test_module/test_model/db.py`)
        * 🟢 list
        * 🟢 instance
            * 🟢 create
            * 🟢 read
            * 🟢 update
            * 🟢 delete
    * 🟢 tests

* 🟢 cli
    * 🟢 core (`templates/py/src/core/__main__.py`)
        * 🟢 setup tables
    * 🟢 model (`templates/py/src/test_module/test_model/__main__.py`)
        * 🟢 db client crud/list ops
        * 🟢 http client crud/list ops
    * 🔴 tests

* 🟢 server
    * 🟢 core (`templates/py/src/core/server.py`)
        * 🟢 auth
        * 🟢 user 
        * 🟢 profile  
    * 🟢 model (`templates/py/src/test_module/test_model/server.py`)
        * 🟢 list
        * 🟢 instance
            * 🟢 create
            * 🟢 read
            * 🟢 update
            * 🟢 delete
    * 🟢 tests
    * 🔴 improve auth
        * 🔴 add salt to pw
        * 🔴 reset password by email code
        * 🔴 add login sessions/logout
        * 🔴 add acls to endpoints/models
    * 🟢 get rid of `__post_init__` and use type conversion explicitly where needed

* 🟢 http client
    * 🟢 core (`templates/py/src/core/client.py`)
        * 🟢 auth
        * 🟢 user 
        * 🟢 profile  
    * 🟢 model (`templates/py/src/test_module/test_model/client.py`)
        * 🟢 list
        * 🟢 instance
            * 🟢 create
            * 🟢 read
            * 🟢 update
            * 🟢 delete
    * 🟢 tests

* 🟡 gui (tkinter)
    * 🟡 index (`templates/py/src/core/gui.py`)
        * 🟢 list modules
        * 🔴 create user/profile
        * 🔴 login
        * 🔴 user/profile page
            * 🔴 read
            * 🔴 edit
    * 🟢 module index (`templates/py/src/test_module/gui.py`)
    * 🟢 model  (`templates/py/src/test_module/test_model/gui.py`)
        * 🟢 list
        * 🟡 instance
            * 🟡 create
            * 🟢 read
            * 🟡 update
            * 🟡 delete
    * 🟡 template extraction 
    * 🔴 tests
    * 🔴 make network requests async

## browser 1 template app
* 🟢 html/js
    * 🟢 index (`templates/browser 1/srv/index.html`)
        * 🟢 list modules
        * 🟡 create user
            * 🟢 login
            * 🔴 reset password
        * 🟢 user page (w logout button)
            * 🟢 view user
            * 🔴 edit profile
            * 🔴 edit profile of logged in user
        * 🔴 profiles
            * 🔴 list profiles
            * 🔴 view profile
    * 🟢 module index (`templates/browser 1/srv/test-module/index.html`)
    * 🟢 model
        * 🟢 list (`templates/browser 1/srv/test-module/test-model/index.html`)
        * 🟢 create (`templates/browser 1/srv/test-module/test-model/index.html`)
        * 🟢 instance
            * 🟢 instance (`templates/browser 1/srv/test-module/test-model/instance.html`)
                * 🟢 read
                * 🟢 update
                * 🟢 delete
    * 🟢 template extraction 
    * 🟢 unittests (`templates/browser 1/tests/test-module/testModel.spec.js`)

## go template app
* 🔴 sqlite3 client
    * 🔴 core
        * 🔴 create tables
        * 🔴 user crud ops
        * 🔴 profile crud ops
    * 🔴 model
        * 🔴 list
        * 🔴 instance
            * 🔴 create
            * 🔴 read
            * 🔴 update
            * 🔴 delete
    * 🔴 tests

* 🔴 cli
    * 🔴 core
        * 🔴 setup tables
    * 🔴 model
        * 🔴 db client crud/list ops
        * 🔴 http client crud/list ops
    * 🔴 tests

* 🔴 server
    * 🔴 core
        * 🔴 auth
        * 🔴 user 
        * 🔴 profile  
    * 🔴 model
        * 🔴 list
        * 🔴 instance
            * 🔴 create
            * 🔴 read
            * 🔴 update
            * 🔴 delete
    * 🔴 tests

* 🔴 http client
    * 🔴 core
        * 🔴 auth
        * 🔴 user 
        * 🔴 profile  
    * 🔴 model
        * 🔴 list
        * 🔴 instance
            * 🔴 create
            * 🔴 read
            * 🔴 update
            * 🔴 delete
    * 🔴 tests

* 🔴 gui
    * 🔴 index
        * 🔴 list modules
        * 🔴 create user/profile
        * 🔴 login
        * 🔴 user/profile page
            * 🔴 read
            * 🔴 edit
    * 🔴 module index
    * 🔴 model
        * 🔴 list
        * 🔴 instance
            * 🔴 instance
                * 🔴 create
                * 🔴 read
                * 🔴 update
                * 🔴 delete
    * 🔴 template extraction 
    * 🔴 tests


## c template app
* 🔴 sqlite3 client
    * 🔴 core
        * 🔴 create tables
        * 🔴 user crud ops
        * 🔴 profile crud ops
    * 🔴 model
        * 🔴 list
        * 🔴 instance
            * 🔴 create
            * 🔴 read
            * 🔴 update
            * 🔴 delete
    * 🔴 tests

* 🔴 cli
    * 🔴 core
        * 🔴 setup tables
    * 🔴 model
        * 🔴 db client crud/list ops
        * 🔴 http client crud/list ops
    * 🔴 tests

* 🔴 http client
    * 🔴 core
        * 🔴 auth
        * 🔴 user 
        * 🔴 profile  
    * 🔴 model
        * 🔴 list
        * 🔴 instance
            * 🔴 create
            * 🔴 read
            * 🔴 update
            * 🔴 delete
    * 🔴 tests

* 🔴 gui
    * 🔴 index
        * 🔴 list modules
        * 🔴 create user/profile
        * 🔴 login
        * 🔴 user/profile page
            * 🔴 read
            * 🔴 edit
    * 🔴 module index
    * 🔴 model
        * 🔴 list
        * 🔴 instance
            * 🔴 instance
                * 🔴 create
                * 🔴 read
                * 🔴 update
                * 🔴 delete
    * 🔴 template extraction 
    * 🔴 tests

## haskell template app
* 🔴 sqlite3 client
    * 🔴 core
        * 🔴 create tables
        * 🔴 user crud ops
        * 🔴 profile crud ops
    * 🔴 model
        * 🔴 list
        * 🔴 instance
            * 🔴 create
            * 🔴 read
            * 🔴 update
            * 🔴 delete
    * 🔴 tests

* 🔴 cli
    * 🔴 core
        * 🔴 setup tables
    * 🔴 model
        * 🔴 db client crud/list ops
        * 🔴 http client crud/list ops
    * 🔴 tests

* 🔴 server
    * 🔴 core
        * 🔴 auth
        * 🔴 user 
        * 🔴 profile  
    * 🔴 model
        * 🔴 list
        * 🔴 instance
            * 🔴 create
            * 🔴 read
            * 🔴 update
            * 🔴 delete
    * 🔴 tests

* 🔴 http client
    * 🔴 core
        * 🔴 auth
        * 🔴 user 
        * 🔴 profile  
    * 🔴 model
        * 🔴 list
        * 🔴 instance
            * 🔴 create
            * 🔴 read
            * 🔴 update
            * 🔴 delete
    * 🔴 tests

* 🔴 gui
    * 🔴 index
        * 🔴 list modules
        * 🔴 create user/profile
        * 🔴 login
        * 🔴 user/profile page
            * 🔴 read
            * 🔴 edit
    * 🔴 module index
    * 🔴 model
        * 🔴 list
        * 🔴 instance
            * 🔴 instance
                * 🔴 create
                * 🔴 read
                * 🔴 update
                * 🔴 delete
    * 🔴 template extraction 
    * 🔴 tests

## browser 2.0 clients
* 🟡 python tkinter
    * 🟢 render hello-world-page.json
    * 🟢 render example_spec
    * 🔴 model widgets
        * 🔴 create
        * 🔴 read
        * 🔴 update
        * 🔴 delete
        * 🔴 list
* 🔴 browser 1
    * 🔴 render hello-world-page.json
    * 🔴 render example spec
    * 🔴 model widgets
* 🔴 Go
    * 🔴 render hello-world-page.json
    * 🔴 render example spec
    * 🔴 model widgets
* 🟡 blender extension / app template
    * 🟢 render hello-world-page.json
    * 🟡 render example spec
    * 🔴 model widgets
* 🔴 C
    * 🔴 render hello-world-page.json
    * 🔴 render example spec
    * 🔴 model widgets
* 🔴 haskell
    * 🔴 render hello-world-page.json
    * 🔴 render example spec
    * 🔴 model widgets

## low code node based gui
A node based gui for low code generation of browser2.0 JSONs.

* 🔴 blender extension / app template
    * 🔴 generate hello-world-page.json
    * 🔴 generate example spec
    * 🔴 genereate widgets
