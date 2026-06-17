#!/usr/bin/env node

function helloWorld() {
  return 'hello.world';
}

if (require.main === module) {
  console.log(helloWorld());
}

module.exports = {
  helloWorld,
};
