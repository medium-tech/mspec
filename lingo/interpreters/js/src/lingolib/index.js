'use strict';

const fs = require('fs');
const YAML = require('yaml');


function parseFile(path) {
  const text = fs.readFileSync(path, 'utf8');
  const doc = YAML.parse(text);
  const spec = doc && doc.lingo && doc.lingo.spec;
  if (!spec) {
    throw new Error('missing lingo.spec in ' + path);
  }
  return doc;
}

function evalExpr(expr) {
  if (expr !== null && typeof expr === 'object' && 'str' in expr) {
    return String(expr.str);
  }
  throw new Error('unsupported expression: ' + JSON.stringify(expr));
}

function executeExe(doc) {
  if (doc.main === undefined) {
    throw new Error('exe spec missing main');
  }
  return evalExpr(doc.main);
}

function executeFile(path) {
  const doc = parseFile(path);
  const spec = doc.lingo.spec;
  if (spec === 'exe') {
    return executeExe(doc);
  }
  throw new Error('unsupported spec: ' + spec);
}

module.exports = { parseFile, executeExe, executeFile };
