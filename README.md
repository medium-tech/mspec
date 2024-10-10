# mspec

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

* 🟡 templating
    * 🟡 refactor src/sample/__init__.py -> src/sample/sample_item/__init__.py
    * 🟡 extract templates
        * 🟡 add macro syntax
        * 🟡 add insert syntax
    * 🟡 generate py
    * 🟡 generate html
    * 🔴 generated app should have 2 modules and 3 total models, but not sample.sample_item
    * 🔴 template app and generated apps unittests are passing

### guis
* 🔴 python tkinter (and/or gtk)
    * 🔴 index
    * 🔴 sample index
    * 🔴 sample item
        * 🔴 list
        * 🔴 instance
            * 🔴 create
            * 🔴 read
            * 🔴 update
            * 🔴 delete

* 🔴 c (gtk)
    * 🔴 index
    * 🔴 sample index
    * 🔴 sample item
        * 🔴 list
        * 🔴 instance
            * 🔴 create
            * 🔴 read
            * 🔴 update
            * 🔴 delete

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

## additional features
* 🔴 markup
    * 🔴 ui
    * 🔴 scripting
* 🔴 content ids
* 🔴 users
* 🔴 profiles
* 🔴 files
