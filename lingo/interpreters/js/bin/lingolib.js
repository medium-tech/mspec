#!/usr/bin/env node
'use strict';

const { executeFile } = require('../src/lingolib/index.js');


const HELP = [
    'usage: lingolib [--help] <command> [args]',
    '',
    'commands:',
    '  exe <path>    load, parse, execute an exe spec and print result',
    '',
    'supported specs: exe',
    '',
].join('\n');

const args = process.argv.slice(2);

if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
    process.stdout.write(HELP);
    process.exit(0);
}

const command = args[0];

if (command === 'exe') {
    if (args.length < 2) {
        process.stderr.write('error: exe requires a path argument\n');
        process.exit(1);
    }
    try {
        const result = executeFile(args[1]);
        console.log(result);
    } catch (e) {
        process.stderr.write('error: ' + e.message + '\n');
        process.exit(1);
    }
} else {
    process.stderr.write('error: unknown command: ' + JSON.stringify(command) + '\n');
    process.exit(1);
}