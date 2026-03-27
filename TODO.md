# Roadmap
## projects

* [mapp framework](#mapp-framework)
* [lingo](#lingo)

### status colors
|not started|in progress|finished|
|--|--|--|
|🔴|🟡|🟢|

## priorities
* 🟢 file upload
    * 🟢 backend
        * 🟢 cli
        * 🟢 server
        * 🟢 tests
    * 🟢 browser1
        * 🟢 model create
        * 🟢 model download
        * 🟢 tests
* 🟢 media
    * 🟢 backend
        * 🟢 cli
        * 🟢 server
        * 🟢 tests
    * 🟢 browser1
        * 🟢 create image
        * 🟢 download image
        * 🟢 view image
        * 🟢 tests
* 🟢 browser - foreign key
    * 🟢 link to item from model view
    * 🟢 search for item from form
    * 🟢 tests
* 🟡 mega app for testing (merge modules from multiple files)
* 🔴 merge js dev lingo server into mapp template
* 🟡 update testing
    * 🟢 split functions.json apart
        * 🟡 create matching specs for script spec
    * 🔴 implement testing data for page spec
* 🔴 define custom pages
    * 🔴 project index page
    * 🔴 module index page
    * 🔴 model index page
    * 🔴 model instance page
    * 🔴 op page
* 🔴 implement max_models_by_field - ie. limit 1 reaction per post_id
* 🔴 add unique constraint to str fields - ie. only 1 profile with a specific username can exist
* 🔴 create features table for different clients
* 🔴 mspec dev blender extension
    * 🔴 update nodes for new functions
    * 🔴 spec creators
    * 🔴 cms extension
        * 🔴 file backup
        * 🔴 metadata logging
* 🔴 refactor
    * 🔴 js parity to py for lingo function arg mapping
    * 🔴 internal naming conventions
        * 🔴 py - in lingo.py; rename `render_*` functions --> `execute_<name>`
        * 🔴 js - same as above for python
    * 🔴 remove plain objects (parity w/ future go implementation)
        * 🔴 create context types (remove plain objects)
            * 🔴 py
            * 🔴 js
        * 🔴 create value type, no passing around primitives
            * 🔴 py
            * 🔴 js

## mapp framework
* 🟢 create tests for auth via cli
* 🟢 all unittests passing
* 🟢 auth - finish integration + tests
    * 🟢 server auth
    * 🟢 cli db auth
    * 🟢 cli http auth
    * 🟢 create 2 users for crud ctx during setup
        * 🟢 ensure user a cannot delete/update items from user b
    * 🟢 max models tests
        * 🟢 add test case of max of 0 models
* 🟡 lingo integration to mapp
    * 🟢 add tests for js browser2
    * 🟢 add new functions to javascript lingo interpreter
    * 🟡 built in lingo ui (lingo pages served in mapp by generating html templates with lingo pages)
        * 🟢 lingo index page
            * 🟢 lingo module page
                * 🟢 lingo model page (create lingo widgets/functions for each of the below)
                    * 🟢 create
                    * 🟢 read
                    * 🟢 update
                    * 🟢 delete
                    * 🟢 list
                    * 🟢 tests
                * 🟢 lingo op page (this will run the op on the backend server and return the result)
                    * 🟢 http
                    * 🟢 tests
            * 🟢 auth
                * 🟢 login
                * 🟢 logout
                * 🟢 user view
                * 🟢 attach session to all op/model calls
                * 🟢 tests
        * 🔴 serve additional lingo pages
            * 🔴 update mspec to support defining other pages and their lingo (for apps running in users local browser)
* 🔴 file upload
    * 🔴 backend
        * 🔴 upload
        * 🔴 download
    * 🔴 lingo / ui
        * 🔴 upload
        * 🔴 download
    * 🔴 add support for multipart upload/download
* 🔴 media files
    * 🔴 media data models  - w/ mediainfo + id of file + master file + alternate versions (ids to other audio/imgs/etc)
        * 🔴 audio
        * 🔴 image
        * 🔴 video
        * 🔴 text (plain or lingo)
    * 🔴 lingo ui
        * 🔴 image viewer
        * 🔴 player
            * 🔴 audio
            * 🔴 video
        * 🔴 text
            * 🔴 display as plain txt
            * 🔴 tail (for following logs)
            * 🔴 render as lingo

* 🟡 refactor internal py api

    * 🔴 parity with JS API

    * 🟢 rename mspec/markup.py to lingo.py
    * 🔴 rename `render_output` to `lingo_render`
    * 🔴 rename remaining `render_*` functions to `execute_*`
    * 🔴 migrate `mtemplate/__init__.py` logic to `mtemplate/core.py`
    * 🟢 migrate builtin auth ops
        * 🟢 migrate `builtin.yaml` ops to `func` style logic

## lingo
* 🔴 add background tasks 
    * 🔴 timers similar to blender's app timers
    * 🔴 scheduled (cron style)
* 🔴 add hook functions
    * 🔴 startup
    * 🔴 shutdown
* 🔴 add meta to models
    * 🔴 users can add key/value "tags" to models
        * 🔴 namespace allows different tagging domains ie. public/admin/user
* 🔴 static site
    * 🔴 generate module/model index and pages
    * 🔴 server redraw process
        * 🔴 manual
        * 🔴 daemon
            * 🔴 interval of N seconds
            * 🔴 allow crud/file ops to tag site for redraw
* 🔴 device
    * 🔴 gps location
        * 🔴 read location; store on model and display to user
        * 🔴 visualize w OSM
    * 🔴 camera
        * 🔴 display camera in real time (ie. mirror)
        * 🔴 take photo & create file+image models
        * 🔴 take audio & create file+audio models
        * 🔴 take video & create file+video models
* 🔴 storage - local vs. remote
    * 🔴 crud lingo method - in page app be able to specify local or remote db
    * 🔴 file lingo method - in page app be able to specify local or remote access
* 🔴 language changes
    * in page lingo specs, rename `ops` to `funcs` to disambiguate calling an op from displaying an op's ui
        to call a page's func you would do `{call: 'funcs.my_func', args: {...}`, and then `{op: 'func.my_func', ...}` would create
        a ui widget to call the function and display the response, `{op: 'my_module.my_backend_op', http: '...'}` to call a backend op via ui
        or `{call: 'my_module.my_backend_op', http: '...', args: ...}` to call it programmatically
    * 🔴 remove `call` function
    * 🔴 remove `lingo` function
    * 🔴 add `error` as function/widget/value/type?
    * 🔴 update `model` functions
        * 🔴 merge model.display `delete` mode into `read` mode, rename `read` to `item`
            * 🔴 add options to init model in delete/read/edit mode
            * 🔴 add options to limit model to only view delete/read and/or edit modes
        * 🔴 remove urls from args, instead supply `module_name` and `model_name`, then infer urls from that
        * 🔴 remove definition from args? lingo app would need access to backend spec then get def from module/model name
* 🔴 implement cids - a separate cid table stores the cid for models or files
* 🔴 implement versioning - of cids and models
* 🔴 purchasing
    * 🔴 subscription
    * 🔴 single transaction
* 🔴 more types
    * 🔴 if default, it is NOT required
    * 🔴 validate fields w/ lingo script inline in the generator script
    * 🔴 multi-dimensional arrays
    * 🔴 date and time
        * 🔴 date
        * 🔴 time
        * 🔴 any of datetime, date or time

## prepare to scale codebase
* 🔴 testing
    * 🔴 add test_data to pages to verify rendered buffer
    * 🔴 refactor tests into individual files for each function group (comparison, bool, str, sequence, etc)
        * 🔴 pages
        * 🔴 scripts
    * 🔴 create a hello world test that only uses functions from the str function group
        * 🔴 page
        * 🔴 script
* 🔴 mspec documentation (this is the ToC for the README.md)
    * 🔴 lingo language
        * 🔴 core language - what is shared between all script types
        * 🔴 script types (page, script, generator)
            * description of what is does
            * features available on in this language
            * python examples for rendering/running scripts
            * test data
    * 🔴 python implementation
        * 🔴 mapp
            * 🔴 code
            * 🔴 running
            * 🔴 testing
        * 🔴 lingo execute
        * 🔴 rendering page
        * 🔴 testing
    * 🔴 legacy browser implementation
        * 🔴 lingo execute
        * 🔴 rendering page
        * 🔴 testing
    * 🔴 templating (document as mostly deprecated)
    * 🔴 app io
        * server
            - static ui files
            - http request/response/error codes
        * cli commands/args/stdout/stderr
        * sqlite commands
* 🔴 project mgmt - create tracking for
    * 🔴 clients
        * 🔴 lingo - tracking for each function group, green when implemented and tested
    * 🔴 for products below create tracking for
        * hello world
        * features

# Alpha 1

## products

### open source code
* 🔴 lingo_exe
    * 🔴 python
    * 🔴 legacy_browser

* 🔴 lingo_gui
    * requires: lingo_exe.*
    * render a page script
    * allows creating an app with a lingo script
        * a browser2 app is a light wrapper around this with other browser related features
    * 🔴 legacy_browser
    * 🔴 python_tk
    * 🔴 blender_app
        * 🔴 extension
            * 🔴 panel
            * 🔴 menu
        * 🔴 app_template

### browser2
    * 🔴 legacy_browser
    * 🔴 python_tk

### blender_app
* 🔴 cms
    * 🔴 backup and sync
    * 🔴 files w/ cid
        * 🔴 backup policy
    * 🔴 forms for taking metadata (ie. audio/image/video)
    * 🔴 integrate with
        * 🔴 video timeline
        * 🔴 image editor
        * 🔴 3d viewspace
* 🔴 mspec dev app
    * 🔴 lingo nodes
    * 🔴 spreadsheet 
    * 🔴 create + render lingo page
    * 🔴 sever mgnt
* 🔴 image editing
    * 🔴 selections
    * 🔴 filters
    * 🔴 layers
* 🔴 midi
    * 🔴 create
    * 🔴 render
* 🔴 daw
    * 🔴 record
    * 🔴 mix
    * 🔴 filter
* 🔴 browser2
    * framework: lingo_gui.blender_app.app_template
    * 🔴 merge in music player
    * 🔴 add streaming
    * 🔴 add video support
    * 🔴 add image gallery
    * 🔴 kiosk mode

### other apps

* 🔴 chat
    * 🔴 text
    * 🔴 a/v
        * 🔴 call
        * 🔴 messages

* 🔴 media_platform
    * 🔴 music
    * 🔴 still artwork
    * 🔴 audio (non-musical ie. spoken word/speech/podcast)
    * 🔴 video - 

* 🔴 classifieds

* 🔴 maps
    * 🔴 search for locations
    * 🔴 directions

* 🔴 gig
    * 🔴 storage/warehousing
    * 🔴 delivery
    * 🔴 taxi


## IT Docs
* 🔴 hardware
    * 🔴 purchasing
    * 🔴 building machine
    * 🔴 troubleshooting
    * 🔴 maintenance
* 🔴 softare
    * 🔴 installation
    * 🔴 troubleshooting
    * 🔴 maintenance
* 🔴 cloud
    * 🔴 setting up server
* 🔴 user guide
    * 🔴 personal computer
        * 🔴 purchasing
            * 🔴 ready to go
            * 🔴 build your own
        * 🔴 backup
            * 🔴 locally (ie. ext. harddrive)
            * 🔴 personal server
            * 🔴 find backup service
    * 🔴 server
        * 🔴 ...
    * 🔴 studio
        * 🔴 ...
    * 🔴 media server
        * 🔴 ...

## Studio Integration
* 🔴 ...

## Cloud Hosting
* 🔴 backup
* 🔴 scale

## content
* 🔴 ...

## Network
* 🔴 ...

# Future Plans
## Alpha V2
* support for go
* support for c
* blender custom build
    * primitives
        * camera/mic/midi recording
        * player w sync from audio file or stream (ie. mic)
        * mixer / streaming
            * mix audio/video signals
            * compositor nodes for controlling output
            * script / show flow control

## Beta
* support for haskell