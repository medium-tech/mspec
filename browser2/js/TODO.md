* add ability to load arbitray pages
* update to support changes in values
    * primitive types like int, bool are now wrapped in a dictionary in the python code but JS hasn't been updated to support this. See commit: b8d419a9dfea3ee5cbe09f00e9a889fb4d9e5e2b
    * JS needs to be able to render return-types.json