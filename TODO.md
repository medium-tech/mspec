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

## main template prototype
The main prototype are the python + browser 1 browser template apps.

### phase 1
* 🔴 finish legacy browser todo list
* 🟢 rename template apps (to disambiguate from testing libs)
    * 🟢 unittest -> template_app
    * 🟢 test_module -> template_module
    * 🟢 test_model -> single_model
    * 🟢 separate model fields starting with `multi_` to another model in the same module called `template_multi_model`
        *(this will make previewing the gui template apps easier bc there are less fields)*
    * 🟢 `html` (template app) -> `browser1`
* 🔴 refactor python vs. templating logic
* 🔴 add file ingest/upload

### phase 2
* 🔴 go backend
* 🔴 implement cids

### additional features
* 🔴 add foreign key id to test_model
* 🔴 add meta to test_model

### misc
* 🟡 performance testing
* 🔴 clean up whitespace in generated apps

## python template app
* 🟢 sqllite3 client
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
        * 🔴 create user
            * 🔴 login
            * 🔴 reset password
        * 🔴 user page (w logout button)
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
* 🔴 sql/sqllite3 client
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
    * 🔴 make network requests async


## c template app
* 🔴 sql/sqllite3 client
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
    * 🔴 make network requests async

## haskell template app
* 🔴 sql/sqllite3 client
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
    * 🔴 make network requests async


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
