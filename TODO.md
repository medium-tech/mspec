# Roadmap

🔴 = not started

🟡 = started

🟢 = finished

### template prototype (python backend + html browser gui)
* 🟡 add auth/users/profile support
    * 🟡 python backend
        * 🟢 client/server unittests for profile/user
        * 🟢 onboarding working, new user/profile/password
        * 🟢 login workflow
        * 🔴 add salt to pw
        * 🔴 reset password by email code
        * 🔴 add login sessions/logout
        * 🔴 add acls to endpoints/models
    * 🔴 html ui
        * 🔴 create user
        * 🔴 view user
        * 🔴 login
        * 🔴 create profile
        * 🔴 view profile
* 🟢 refactor sample_module to match core module
    * 🟢 refactor code
    * 🟢 refactor templating
    * 🟢 tests passing
        * 🟢 sample app
            * 🟢 client/server
            * 🟢 browser gui
        * 🟢 generated app
            * 🟢 client/server
            * 🟢 browser gui
* 🟢 replace mongo with sqlite
    * 🟢 template tests passing
    * 🟢 generated app tests passing
* 🟢 fix ui handling of dates
* 🔴 refactor python vs. templating logic
* 🔴 add foreign key id to test_model
* 🔴 add cid to test_model
* 🔴 add meta to test_model
* 🟡 performance testing
* 🔴 get rid of `__post_init__` and use type conversion explicitly where needed
* 🔴 rename template apps
    * 🔴 unittest -> template_app
    * 🔴 test_module -> template_module
    * 🔴 test_model -> template_model
* 🔴 clean up whitespace in generated apps
* 🔴 git rid of jinja dependency (do this after creating apps in several languages to determine full scope needed from templating)
    
### template guis

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

* 🔴 haskell
    * 🔴 index
    * 🔴 sample index
    * 🔴 sample item
        * 🔴 list
        * 🔴 instance
            * 🔴 create
            * 🔴 read
            * 🔴 update
            * 🔴 delete

### template servers
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

* 🔴 haskell
    * 🔴 index
    * 🔴 sample index
    * 🔴 sample item
        * 🔴 list
        * 🔴 instance
            * 🔴 create
            * 🔴 read
            * 🔴 update
            * 🔴 delete

### template clients
* 🔴 go
    * 🔴 user login
    * 🔴 model
        * 🔴 list
        * 🔴 instance
            * 🔴 create
            * 🔴 read
            * 🔴 update
            * 🔴 delete

# browser 2.0 GUIs
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