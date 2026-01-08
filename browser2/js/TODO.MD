# TODO JS Lingo Interpreter

* create consistency with the `lingo-app` container element. It needs to be passed into `renderLingoApp` and is also referenced in various places in markup.js as the id `lingo-app` or via closest css `.closest('.lingo-container')`.
* delete `handleSequenceOps` and move logic to custom functions which will be placed in the function lookup