# Roadmap

## projects

* [main prototype](#main-template-prototype)
* [python template app](#python-template-app)
* [legacy browser template app](#legacy-browser-template-app-html)
* [go template app](#go-template-app)
* [c template app](#c-template-app)
* [haskell template app](#haskell-template-app)
* [browser 2.0 clients](#browser-20-clients)

### status colors
|not started|in progress|finished|
|--|--|--|
|🔴|🟡|🟢|

## main template prototype
The main prototype are the python + html browser template apps.

* 🟡 add auth/users/profile support
    * 🟡 python backend
        * 🟢 client/server unittests for profile/user
        * 🟢 onboarding working, new user/profile/password
        * 🟢 login workflow
        * 🔴 add salt to pw
        * 🔴 reset password by email code
        * 🔴 add login sessions/logout
        * 🔴 add acls to endpoints/models
    * 🔴 html ui user / profiles
* 🔴 add foreign key id to test_model
* 🔴 add cid to test_model
* 🔴 add meta to test_model
* 🔴 add fille ingest/upload
* 🔴 rename template apps
    * 🔴 unittest -> template_app
    * 🔴 test_module -> template_module
    * 🔴 test_model -> template_model
* 🟡 performance testing
* 🔴 refactor python vs. templating logic
* 🔴 get rid of `__post_init__` and use type conversion explicitly where needed
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
            * 🟡 instance
                * 🟡 create
                * 🟡 read
                * 🟡 update
                * 🟡 delete
    * 🔴 template extraction 
    * 🔴 tests
    * 🔴 make network requests async

## legacy browser template app (html)
* 🟢 html/js
    * 🟢 index (`templates/html/srv/index.html`)
        * 🟢 list modules
        * 🔴 create user/profile
        * 🔴 login
        * 🔴 user/profile page
            * 🔴 read
            * 🔴 edit
    * 🟢 module index (`templates/html/srv/test-module/index.html`)
    * 🟢 model
        * 🟢 list (`templates/html/srv/test-module/test-model/index.html`)
        * 🟢 create (`templates/html/srv/test-module/test-model/index.html`)
        * 🟢 instance
            * 🟢 instance (`templates/html/srv/test-module/test-model/instance.html`)
                * 🟢 read
                * 🟢 update
                * 🟢 delete
    * 🟢 template extraction 
    * 🟢 unittests (`templates/html/tests/test-module/testModel.spec.js`)

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
* 🔴 html
    * 🔴 render hello-world-page.json
    * 🔴 render example spec
    * 🔴 model widgets
* 🔴 Go
    * 🔴 render hello-world-page.json
    * 🔴 render example spec
    * 🔴 model widgets
* 🔴 blender app template
    * 🔴 render hello-world-page.json
    * 🔴 render example spec
    * 🔴 model widgets
* 🔴 C
    * 🔴 render hello-world-page.json
    * 🔴 render example spec
    * 🔴 model widgets
* 🔴 haskell
    * 🔴 render hello-world-page.json
    * 🔴 render example spec
    * 🔴 model widgets