/**
 * JavaScript implementation of the mspec markup language renderer
 * This is equivalent to the Python markup.py module
 */

function enableProtocol() {
    document.cookie = "protocol_mode=true; path=/";
    return 'refresh to enable protocol mode'
}

function disableProtocol() {
    document.cookie = "protocol_mode=false; path=/";
    return 'refresh to disable protocol mode'
}

window.enableProtocol = enableProtocol;
window.disableProtocol = disableProtocol;

// // // // //
//
// helper functions
//
// // // // //

// Date/time formatting
const datetimeFormatStr = '%Y-%m-%dT%H:%M:%S';

function initDateTimeFromInput(value) {
    // 
    // value from date time input will be in format "YYYY-MM-DDTHH:MM" if chosen by a user,
    // but in 2000-01-11T12:34:56 format if set programmatically
    // so we need to handle both cases

    if (value.length === 16) {
        // Add seconds if missing
        return value + ':00';
    }else{
        return value;
    }
}

// Helper function for lingo int conversion
function lingoInt(number = null, string = null, base = 10) {
    if (number !== null && number !== undefined) {
        return Math.floor(Number(number));
    } else if (string !== null && string !== undefined) {
        return parseInt(string, base);
    } else {
        throw new Error('lingo int - must provide either number or string argument');
    }
}

// Helper function for str join
function strJoin(separator, items) {
    return items.map(item => String(item)).join(separator);
}

// Helper function for str concat
function strConcat(items) {
    return items.map(item => String(item)).join('');
}

function getRequestHeaders() {
    // check localStorage for access_token
    const headers = {
        'Content-Type': 'application/json'
    };
    const accessToken = localStorage.getItem('access_token');
    if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
    }
    return headers;
}

async function fileSystemIngestStart(file) {

    let params = {
        name: file.name,
        size: file.size,
        parts: 1,
        finish: true
    };

    console.log('fileSystemIngestFile()', file, params);

    // multipart upload to /api/file-system/ingest-start
    
    const formData = new FormData();
    formData.append('file', file); 
    formData.append('json', JSON.stringify(params));
    let headers = getRequestHeaders();

    // let browser set the correct Content-Type for multipart form data w proper boundary
    delete headers['Content-Type']; 

    try {
        const response = await fetch('/api/file-system/ingest-start', {
            method: 'POST',
            headers: headers,
            body: formData
        });

        if(response.ok) {
            const data = await response.json();
            console.log('File ingested successfully:', data);
            return data;
            // You can handle the response data as needed, e.g., update the UI or store the file ID
        } else {
            const errMsg = `Error ingesting file: ${response.status} - ${response.statusText}`;
            const responseText = await response.text();
            console.error(errMsg, response, responseText);
            return {'error': errMsg};
        }

    } catch (error) {
        console.error('Error uploading file:', error);
        return {'error': error.message};
    }

}

async function mediaCreateImage(file) {

    let params = {
        name: file.name,
        content_type: '' // let backend auto-detect content type
    };

    console.log('mediaCreateImage()', file, params);

    // multipart upload to /api/media/create-image
    
    const formData = new FormData();
    formData.append('file', file); 
    formData.append('json', JSON.stringify(params));
    let headers = getRequestHeaders();

    // let browser set the correct Content-Type for multipart form data w proper boundary
    delete headers['Content-Type'];

    try {
        const response = await fetch('/api/media/create-image', {
            method: 'POST',
            headers: headers,
            body: formData
        });

        if(response.ok) {
            const data = await response.json();
            console.log('Image created successfully:', data);
            return data;
            // You can handle the response data as needed, e.g., update the UI or store the media ID
        } else {
            const errMsg = `Error creating image: ${response.status} - ${response.statusText}`;
            const responseText = await response.text();
            console.error(errMsg, response, responseText);
            return {'error': errMsg};
        }

    } catch (error) {
        console.error('Error uploading image:', error);
        return {'error': error.message};
    }

}

async function mediaIngestMasterImage(file) {

    let params = {
        name: file.name,
        content_type: '' // let backend auto-detect content type
    };

    console.log('mediaIngestMasterImage()', file, params);

    // multipart upload to /api/media/ingest-master-image
    
    const formData = new FormData();
    formData.append('file', file); 
    formData.append('json', JSON.stringify(params));
    let headers = getRequestHeaders();

    // let browser set the correct Content-Type for multipart form data w proper boundary
    delete headers['Content-Type'];

    try {
        const response = await fetch('/api/media/ingest-master-image', {
            method: 'POST',
            headers: headers,
            body: formData
        });

        if(response.ok) {
            const data = await response.json();
            console.log('Master image ingested successfully:', data);
            return data;
            // You can handle the response data as needed, e.g., update the UI or store the media ID
        } else {
            const errMsg = `Error ingesting master image: ${response.status} - ${response.statusText}`;
            const responseText = await response.text();
            console.error(errMsg, response, responseText);
            return {'error': errMsg};
        }

    } catch (error) {
        console.error('Error ingesting master image:', error);
        return {'error': error.message};
    }

}

const placeholderImage = (width, height, text) => {
    // 1. Create a canvas element
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;

    // 2. Get 2D rendering context
    const ctx = canvas.getContext('2d');

    // 3. Fill with a fully transparent color (rgba with alpha = 0)
    //   ctx.fillStyle = 'rgb(168, 168, 168)';
    //   ctx.fillRect(0, 0, width, height);

    // 3. Use a checkerboard pattern
    const color1 = 'rgba(234, 234, 234, 0.96)'; // light gray
    const color2 = 'rgba(209, 207, 207, 0.76)'; // darker gray
    const tileSize = 17; // size of each checkerboard tile
    const numTilesX = width / tileSize;
    const numTilesY = height / tileSize;

    for (let i = 0; i < numTilesX; i++) {
        for (let j = 0; j < numTilesY; j++) {
            // Alternate colors based on row and column indices
            ctx.fillStyle = (i + j) % 2 === 0 ? color1 : color2;
            ctx.fillRect(i * tileSize, j * tileSize, tileSize, tileSize);
        }
    }

    // 4. write text
    ctx.fillStyle = 'rgb(0, 0, 0)';
    ctx.font = '24px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, width / 2, height / 2);

    // 5. Convert to data URL
    // Default format is 'image/png' which supports transparency
    const dataURL = canvas.toDataURL(); 

    // 6. Use the data URL in an Image object
    const img = new Image(width, height);
    img.src = dataURL; 

    return img;
};

// // // // //
//
// argument mappers | mapping JS and lingo function signatures
//
// // // // //

// sequence ops //

function _mapFunctionArgs(app, expression, ctx) {
    const args = expression.args || {};
    const iterable = lingoExecute(app, args.iterable, ctx);
    const iterableValue = (typeof iterable === 'object' && 'value' in iterable) ? iterable.value : iterable;
    const predicate = (item) => {
        const newCtx = ctx ? {...ctx} : {};
        newCtx.self = {item};
        const result = lingoExecute(app, args.function, newCtx);
        if (typeof result === 'object' && result !== null && 'value' in result) {
            return result.value;
        } else if (typeof result === 'object' && result !== null && !Array.isArray(result)) {
            const evaluatedResult = {};
            for (const [key, value] of Object.entries(result)) {
                const evaluated = lingoExecute(app, value, newCtx);
                evaluatedResult[key] = (typeof evaluated === 'object' && evaluated !== null && 'value' in evaluated)
                    ? evaluated.value
                    : evaluated;
            }
            return evaluatedResult;
        }
        return result;
    };
    return [predicate, iterableValue];
}

function _predicateFunctionArgs(app, expression, ctx) {
    const args = expression.args || {};
    const iterable = lingoExecute(app, args.iterable, ctx);
    const iterableValue = (typeof iterable === 'object' && 'value' in iterable) ? iterable.value : iterable;
    const predicate = (item) => {
        const newCtx = ctx ? {...ctx} : {};
        newCtx.self = {item};
        const result = lingoExecute(app, args.function, newCtx);
        return (typeof result === 'object' && 'value' in result) ? result.value : result;
    };
    return [predicate, iterableValue];
}

function _accumulateFunctionArgs(app, expression, ctx) {
    const args = expression.args || {};
    const iterable = lingoExecute(app, args.iterable, ctx);
    const iterableValue = (typeof iterable === 'object' && 'value' in iterable) ? iterable.value : iterable;
    const accumulateFunc = (a, b) => {
        const newCtx = ctx ? {...ctx} : {};
        newCtx.self = {item: a, next_item: b};
        const result = lingoExecute(app, args.function, newCtx);
        return (typeof result === 'object' && 'value' in result) ? result.value : result;
    };
    const initial = args.initial !== undefined ? lingoExecute(app, args.initial, ctx) : null;
    const initialValue = (initial && typeof initial === 'object' && 'value' in initial) ? initial.value : initial;
    return [accumulateFunc, iterableValue, initialValue];
}

function _reduceFunctionArgs(app, expression, ctx) {
    const args = expression.args || {};
    const iterable = lingoExecute(app, args.iterable, ctx);
    const iterableValue = (typeof iterable === 'object' && 'value' in iterable) ? iterable.value : iterable;
    const reduceFunc = (a, b) => {
        const newCtx = ctx ? {...ctx} : {};
        newCtx.self = {item: a, next_item: b};
        const result = lingoExecute(app, args.function, newCtx);
        return (typeof result === 'object' && 'value' in result) ? result.value : result;
    };
    const initial = args.initial !== undefined ? lingoExecute(app, args.initial, ctx) : null;
    const initialValue = (initial && typeof initial === 'object' && 'value' in initial) ? initial.value : null;
    return [reduceFunc, iterableValue, initialValue];
}

// auth //

function _authIsLoggedInArgs(app, expression, ctx) {
    const args = expression.args || {};
    if(args.hasOwnProperty('confirm')) {
        const confirm = unwrapValue(lingoExecute(app, args.confirm, ctx));
        return [confirm];
    }else{
        return [false];
    }
}


// crud //

function _crudCreateArgs(app, expression, ctx) {
    const args = expression.args || {};
    const url = unwrapValue(lingoExecute(app, args.http, ctx));
    const data = lingoExecute(app, args.data, ctx);
    if (expression.args.bind && expression.args.bind.state) {
        const stateKeys = Object.keys(expression.args.bind.state);
        if (stateKeys.length === 1) {
            const stateField = stateKeys[0];
            if (!app.state.hasOwnProperty(stateField)) {
                throw new Error(`crud.create - state field not found: ${stateField}`);
            }
            app.state[stateField].state = 'loading';
        }
    }
    return [url, data];
}

function _crudUpdateArgs(app, expression, ctx) {
    const args = expression.args || {};
    const url = unwrapValue(lingoExecute(app, args.http, ctx));
    const data = lingoExecute(app, args.data, ctx);
    if (expression.args.bind && expression.args.bind.state) {
        const stateKeys = Object.keys(expression.args.bind.state);
        if (stateKeys.length === 1) {
            const stateField = stateKeys[0];
            if (!app.state.hasOwnProperty(stateField)) {
                throw new Error(`crud.update - state field not found: ${stateField}`);
            }
            app.state[stateField].state = 'loading';
        }
    }
    return [url, data];
}

function _crudReadArgs(app, expression, ctx) {
    const args = expression.args || {};
    const url = unwrapValue(lingoExecute(app, args.http, ctx));
    if (expression.args.bind && expression.args.bind.state) {
        const stateKeys = Object.keys(expression.args.bind.state);
        if (stateKeys.length === 1) {
            const stateField = stateKeys[0];
            if (!app.state.hasOwnProperty(stateField)) {
                throw new Error(`crud.read - state field not found: ${stateField}`);
            }
            app.state[stateField].state = 'loading...';
        }
    }
    return [url];
}

function _crudDeleteArgs(app, expression, ctx) {
    const args = expression.args || {};
    const url = unwrapValue(lingoExecute(app, args.http, ctx));
    if (expression.args.bind && expression.args.bind.state) {
        const stateKeys = Object.keys(expression.args.bind.state);
        if (stateKeys.length === 1) {
            const stateField = stateKeys[0];
            if (!app.state.hasOwnProperty(stateField)) {
                throw new Error(`crud.delete - state field not found: ${stateField}`);
            }
            app.state[stateField].state = 'loading';
        }
    }
    return [url];
}

function _crudListArgs(app, expression, ctx) {
    const args = expression.args || {};
    const urlBase = unwrapValue(lingoExecute(app, args.http, ctx));
    const offset = unwrapValue(lingoExecute(app, args.offset, ctx));
    const size = unwrapValue(lingoExecute(app, args.size, ctx));
    const url = `${urlBase}?offset=${offset}&size=${size}`;
    if (expression.args.bind && expression.args.bind.state) {
        const stateKeys = Object.keys(expression.args.bind.state);
        if (stateKeys.length === 1) {
            const stateField = stateKeys[0];
            if (!app.state.hasOwnProperty(stateField)) {
                throw new Error(`crud.list - state field not found: ${stateField}`);
            }
            app.state[stateField].state = 'loading';
        }
    }
    return [url, offset, size];
}

// op //

function _opHttpArgs(app, expression, ctx) {
    const args = expression.args || {};
    const url = unwrapValue(lingoExecute(app, args.url, ctx));
    const params = lingoExecute(app, args.data, ctx);
    if (expression.args.bind && expression.args.bind.state) {
        const stateKeys = Object.keys(expression.args.bind.state);
        if (stateKeys.length === 1) {
            const stateField = stateKeys[0];
            if (!app.state.hasOwnProperty(stateField)) {
                throw new Error(`op.http - state field not found: ${stateField}`);
            }
            app.state[stateField].state = 'loading';
        }
    }
    // console.log('op.http - url:', expression, url, 'params:', params);
    return [url, params];
}

// file system //

function _fileSystemGetFileContentArgs(app, expression, ctx) {
    const args = expression.args || {};
    if (!args.file_id) {
        throw new Error('file_system.get_file_content - missing required arg: file_id');
    }
    const fileId = unwrapValue(lingoExecute(app, args.file_id, ctx));
    const formName = `model-field-get-file-content`;
    app.clientState.forms[formName].state = 'loading';
    const defaultFileName = `file_id_${fileId}`;
    const fileName = (async () => {
        try {
            console.log('file_system.get_file_content - fetching...');
            const response = await fetch('/api/file-system/list-files', {
                method: 'POST',
                headers: getRequestHeaders(),
                body: JSON.stringify({file_id: fileId})
            });
            if (response.ok) {
                const responseData = await response.json();
                try {
                    return responseData.result.items[0].name || defaultFileName;
                } catch (error) {
                    console.error('file_system.get_file_content - error parsing file metadata response:', error);
                    return defaultFileName;
                }
            } else {
                console.error('file_system.get_file_content - HTTP error while fetching file metadata:', response.status, response.statusText);
                return defaultFileName;
            }
        } catch (error) {
            console.error('file_system.get_file_content - network error while fetching file metadata:', error);
            return defaultFileName;
        }
    })();
    return [app, fileId, fileName, formName];
}

// media //

function _mediaGetMediaFileContentArgs(app, expression, ctx) {
    const args = expression.args || {};
    const imageId = unwrapValue(lingoExecute(app, args.image_id, ctx));
    console.log('media.get_media_file_content - imageId:', imageId);
    if (!ctx || !ctx.self || !ctx.self.file_output) {
        throw new Error('media.get_media_file_content - missing self.file_output in context');
    }
    const fileOutput = ctx.self.file_output;
    const defaultFileId = '-1';
    const fileId = (async () => {
        try {
            console.log('media.get_media_file_content - fetching image metadata...');
            const response = await fetch(`/api/media/get-image?image_id=${imageId}`, {
                method: 'GET',
                headers: getRequestHeaders()
            });
            if (response.ok) {
                const responseData = await response.json();
                console.log('media.get_media_file_content - image data:', responseData);
                try {
                    const fileId = responseData.result.file_id;
                    fileOutput.fileId = fileId;
                    return fileId;
                } catch (error) {
                    console.error('media.get_media_file_content - error parsing media metadata response:', error);
                    return defaultFileId;
                }
            } else {
                console.error('media.get_media_file_content - HTTP error while fetching media metadata:', response.status, response.statusText);
                return defaultFileId;
            }
        } catch (error) {
            console.error('media.get_media_file_content - network error while fetching media metadata:', error);
            return defaultFileId;
        }
    })();
    const defaultFileName = `image_id_${imageId}`;
    const fileName = (async () => {
        if (await fileId === '-1') {
            return defaultFileName;
        }
        try {
            console.log('media.get_media_file_content - fetching file metadata...');
            const response = await fetch('/api/file-system/list-files', {
                method: 'POST',
                headers: getRequestHeaders(),
                body: JSON.stringify({file_id: await fileId})
            });
            if (response.ok) {
                const responseData = await response.json();
                try {
                    console.log('media.get_media_file_content - file metadata:', responseData);
                    const fileName = responseData.result.items[0].name;
                    fileOutput.fileName = fileName;
                    return fileName;
                } catch (error) {
                    console.error('media.get_media_file_content - error parsing file metadata response:', error);
                    return defaultFileName;
                }
            } else {
                console.error('media.get_media_file_content - HTTP error while fetching file metadata:', response.status, response.statusText);
                return defaultFileName;
            }
        } catch (error) {
            console.error('media.get_media_file_content - network error while fetching file metadata:', error);
            return defaultFileName;
        }
    })();
    fileOutput.status = 'loading';
    return [app, imageId, fileName, fileOutput];
}


// // // // //
//
// lingo functions
//
// // // // //


const lingoFunctionLookup = {

    // comparison //
    
    'eq': {
        func: (a, b) => a === b,
        args: {'a': {'type': 'any'}, 'b': {'type': 'any'}}
    },
    'ne': {
        func: (a, b) => a !== b,
        args: {'a': {'type': 'any'}, 'b': {'type': 'any'}}
    },
    'lt': {
        func: (a, b) => a < b,
        args: {'a': {'type': 'any'}, 'b': {'type': 'any'}}
    },
    'le': {
        func: (a, b) => a <= b,
        args: {'a': {'type': 'any'}, 'b': {'type': 'any'}}
    },
    'gt': {
        func: (a, b) => a > b,
        args: {'a': {'type': 'any'}, 'b': {'type': 'any'}}
    },
    'ge': {
        func: (a, b) => a >= b,
        args: {'a': {'type': 'any'}, 'b': {'type': 'any'}}
    },
    
    // bool //
    
    'bool': {
        func: (obj) => Boolean(obj),
        args: {'object': {'type': 'any'}}
    },
    'not': {
        func: (obj) => !obj,
        args: {'object': {'type': 'any'}}
    },
    'and': {
        func: (a, b) => a && b,
        args: {'a': {'type': 'any'}, 'b': {'type': 'any'}}
    },
    'or': {
        func: (a, b) => a || b,
        args: {'a': {'type': 'any'}, 'b': {'type': 'any'}}
    },
    
    // int //
    
    'int': {
        func: lingoInt,
        args: {
            'number': {'type': 'any', 'default': null},
            'string': {'type': 'str', 'default': null},
            'base': {'type': 'int', 'default': 10}
        }
    },
    'neg': {
        func: (obj) => -obj,
        args: {'object': {'type': 'any'}}
    },
    
    // float //
    
    'float': {
        func: (number) => Number(number),
        args: {'number': {'type': 'any'}}
    },
    'round': {
        func: (number, ndigits = null) => {
            if (ndigits === null) {
                return Math.round(number);
            }
            const multiplier = Math.pow(10, ndigits);
            return Math.round(number * multiplier) / multiplier;
        },
        args: {
            'number': {'type': 'float'},
            'ndigits': {'type': 'int', 'default': null}
        }
    },
    
    // str //
    
    'str': {
        func: (obj) => String(obj),
        args: {'object': {'type': 'any'}}
    },
    'join': {
        func: strJoin,
        args: {
            'separator': {'type': 'str'},
            'items': {'type': 'list'}
        }
    },
    'concat': {
        func: strConcat,
        args: {
            'items': {'type': 'list'}
        }
    },

    // struct //
    
    'key': {
        func: (object, key) => {
            if (object && typeof object === 'object' && key in object) {
                return object[key];
            } else {
                console.error('lingo function key - key not found in object:', key, 'object:', object);
                throw new Error(`lingo function key - key '${key}' not found in object`);
            }
        },
        args: {
            'object': {'type': 'struct'},
            'key': {'type': 'str'}
        }
    },
    
    // math //
    
    'add': {
        func: (a, b) => a + b,
        args: {'a': {'type': 'number'}, 'b': {'type': 'number'}}
    },
    'sub': {
        func: (a, b) => a - b,
        args: {'a': {'type': 'number'}, 'b': {'type': 'number'}}
    },
    'mul': {
        func: (a, b) => a * b,
        args: {'a': {'type': 'number'}, 'b': {'type': 'number'}}
    },
    'div': {
        func: (a, b) => a / b,
        args: {'a': {'type': 'number'}, 'b': {'type': 'number'}}
    },
    'floordiv': {
        func: (a, b) => Math.floor(a / b),
        args: {'a': {'type': 'number'}, 'b': {'type': 'number'}}
    },
    'mod': {
        func: (a, b) => a % b,
        args: {'a': {'type': 'number'}, 'b': {'type': 'number'}}
    },
    'pow': {
        func: (a, b) => Math.pow(a, b),
        args: {'a': {'type': 'number'}, 'b': {'type': 'number'}}
    },
    'min': {
        func: (a, b) => Math.min(a, b),
        args: {'a': {'type': 'number'}, 'b': {'type': 'number'}}
    },
    'max': {
        func: (a, b) => Math.max(a, b),
        args: {'a': {'type': 'number'}, 'b': {'type': 'number'}}
    },
    'abs': {
        func: (number) => Math.abs(number),
        args: {'number': {'type': 'number'}}
    },
    
    // sequence //
    
    'len': {
        func: (obj) => obj.length,
        args: {'object': {'type': 'any'}}
    },
    'range': {
        func: (start = 0, stop, step = 1) => {
            const result = [];
            for (let i = start; i < stop; i += step) {
                result.push(i);
            }
            return result;
        },
        args: {
            'start': {'type': 'int', 'default': 0},
            'stop': {'type': 'int'},
            'step': {'type': 'int', 'default': 1}
        }
    },
    'slice': {
        func: (iterator, start = null, stop, step = null) => {
            if (step !== null && step !== 1) {
                const result = [];
                const actualStart = start === null ? 0 : start;
                for (let i = actualStart; i < stop; i += step) {
                    if (i < iterator.length) {
                        result.push(iterator[i]);
                    }
                }
                return result;
            }
            const actualStart = start === null ? 0 : start;
            return iterator.slice(actualStart, stop);
        },
        args: {
            'iterator': {'type': 'list'},
            'start': {'type': 'int', 'default': null},
            'stop': {'type': 'int'},
            'step': {'type': 'int', 'default': null}
        }
    },
    'any': {
        func: (iterable) => iterable.some(x => x),
        args: {'iterable': {'type': 'list'}}
    },
    'all': {
        func: (iterable) => iterable.every(x => x),
        args: {'iterable': {'type': 'list'}}
    },
    'sum': {
        func: (iterable, start = 0) => iterable.reduce((acc, val) => acc + val, start),
        args: {
            'iterable': {'type': 'list'},
            'start': {'type': 'number', 'default': 0}
        }
    },
    'sorted': {
        func: (iterable) => [...iterable].sort(),
        args: {'iterable': {'type': 'list'}}
    },
    
    // sequence ops //
    
    'map': {
        func: (predicate, iterable) => ({type: 'list', value: iterable.map(predicate)}),
        createArgs: _mapFunctionArgs
    },
    'filter': {
        func: (predicate, iterable) => ({type: 'list', value: iterable.filter(predicate)}),
        createArgs: _predicateFunctionArgs
    },
    'dropwhile': {
        func: (predicate, iterable) => {
            const result = [];
            let dropping = true;
            for (const item of iterable) {
                if (dropping && !predicate(item)) dropping = false;
                if (!dropping) result.push(item);
            }
            return {type: 'list', value: result};
        },
        createArgs: _predicateFunctionArgs
    },
    'takewhile': {
        func: (predicate, iterable) => {
            const result = [];
            for (const item of iterable) {
                if (predicate(item)) result.push(item);
                else break;
            }
            return {type: 'list', value: result};
        },
        createArgs: _predicateFunctionArgs
    },
    'reversed': {
        func: (sequence) => [...sequence].reverse(),
        args: {'sequence': {'type': 'list'}}
    },
    'accumulate': {
        func: (accumulateFunc, iterable, initialValue) => {
            const result = [];
            let accumulator = initialValue !== null ? initialValue : iterable[0];
            if (initialValue !== null) {
                result.push(accumulator);
                for (const item of iterable) {
                    accumulator = accumulateFunc(accumulator, item);
                    result.push(accumulator);
                }
            } else {
                result.push(accumulator);
                for (let i = 1; i < iterable.length; i++) {
                    accumulator = accumulateFunc(accumulator, iterable[i]);
                    result.push(accumulator);
                }
            }
            return {type: 'list', value: result};
        },
        createArgs: _accumulateFunctionArgs
    },
    'reduce': {
        func: (reduceFunc, iterable, initialValue) => {
            const result = initialValue !== null
                ? iterable.reduce(reduceFunc, initialValue)
                : iterable.reduce(reduceFunc);
            return {type: getTypeName(result), value: result};
        },
        createArgs: _reduceFunctionArgs
    },
    
    // date and time #
    
    'current': {
        'weekday': {
            func: () => {
                // Python weekday: 0=Monday, 6=Sunday
                // JS getDay: 0=Sunday, 6=Saturday
                // Convert JS to Python format
                const day = new Date().getDay();
                return day === 0 ? 6 : day - 1;
            },
            args: {},
            sig: 'kwargs'
        }
    },
    'datetime': {
        'now': {
            func: () => new Date(),
            args: {},
            sig: 'kwargs'
        }
    },
    
    // random //
    
    'random': {
        'randint': {
            func: (a, b) => Math.floor(Math.random() * (b - a + 1)) + a,
            args: {'a': {'type': 'int'}, 'b': {'type': 'int'}}
        }
    },

    // client //

    'client': {
        'reload': {
            func: () => {
                window.location.reload();
                return {acknowledged: true, message: 'reload triggered'};
            },
            args: {},
            sig: 'kwargs'
        }
    },

    // crud //

    'crud': {
        'create': {
            func: async (url, data) => {
                try {
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: getRequestHeaders(),
                        body: JSON.stringify(data)
                    });
                    if (response.ok) {
                        const responseData = await response.json();
                        // console.log('crud.create - responseData:', responseData);
                        return {state: 'success', item_id: responseData.id};
                    } else {
                        const errorData = await response.json();
                        let errorMessage = `${response.status} ${response.statusText}`;
                        if (errorData.hasOwnProperty('error') && errorData.error.hasOwnProperty('message')) {
                            errorMessage = errorData.error.message;
                        }
                        console.error('crud.create - HTTP error:', response.status, response.statusText);
                        return {state: 'error', error: errorMessage};
                    }
                } catch (error) {
                    console.error('crud.create - network error:', error);
                    return {state: 'error', error: `Network error: ${error.message}`};
                }
            },
            createArgs: _crudCreateArgs
        },
        'read': {
            func: async (url) => {
                // console.log('crud.read - url:', url);
                try {
                    const response = await fetch(url, {
                        method: 'GET',
                        headers: getRequestHeaders()
                    });
                    if (response.ok) {
                        const responseData = await response.json();
                        // console.log('crud.read - responseData:', responseData);
                        return {state: 'loaded', data: responseData};
                    } else {
                        const errorData = await response.json();
                        let errorMessage = `${response.status} ${response.statusText}`;
                        if (errorData.hasOwnProperty('error') && errorData.error.hasOwnProperty('message')) {
                            errorMessage = errorData.error.message;
                        }
                        console.error('crud.read - HTTP error:', response.status, response.statusText);
                        return {state: 'error', error: errorMessage};
                    }
                } catch (error) {
                    console.error('crud.read - network error:', error);
                    return {state: 'error', error: `Network error: ${error.message}`};
                }
            },
            createArgs: _crudReadArgs
        },
        'update': {
            func: async (url, data) => {
                try {
                    const response = await fetch(url, {
                        method: 'PUT',
                        headers: getRequestHeaders(),
                        body: JSON.stringify(data)
                    });
                    if (response.ok) {
                        const responseData = await response.json();
                        // console.log('crud.update - responseData:', responseData);
                        return {state: 'edited', data: responseData};
                    } else {
                        const errorData = await response.json();
                        let errorMessage = `${response.status} ${response.statusText}`;
                        if (errorData.hasOwnProperty('error') && errorData.error.hasOwnProperty('message')) {
                            errorMessage = errorData.error.message;
                        }
                        console.error('crud.update - HTTP error:', response.status, response.statusText);
                        return {state: 'error', error: errorMessage};
                    }
                } catch (error) {
                    console.error('crud.update - network error:', error);
                    return {state: 'error', error: `Network error: ${error.message}`};
                }
            },
            createArgs: _crudUpdateArgs
        },
        'delete': {
            func: async (url) => {
                try {
                    const response = await fetch(url, {
                        method: 'DELETE',
                        headers: getRequestHeaders()
                    });
                    if (response.ok) {
                        console.log('crud.delete - item deleted successfully');
                        return {state: 'deleted'};
                    } else {
                        const errorData = await response.json();
                        let errorMessage = `${response.status} ${response.statusText}`;
                        if (errorData.hasOwnProperty('error') && errorData.error.hasOwnProperty('message')) {
                            errorMessage = errorData.error.message;
                        }
                        console.error('crud.delete - HTTP error:', response.status, response.statusText);
                        return {state: 'error', error: errorMessage};
                    }
                } catch (error) {
                    console.error('crud.delete - network error:', error);
                    return {state: 'error', error: `Network error: ${error.message}`};
                }
            },
            createArgs: _crudDeleteArgs
        },
        'list': {
            func: async (url, offset, size) => {
                try {
                    const response = await fetch(url, {
                        method: 'GET',
                        headers: getRequestHeaders()
                    });
                    if (response.ok) {
                        // console.log('crud.list - raw text response:', await response.text());
                        const responseData = await response.json();
                        // console.log('crud.list - responseData:', responseData);
                        return {
                            state: 'loaded',
                            total: responseData.total,
                            items: responseData.items.map(item => ({type: 'struct', value: item})),
                            showing: responseData.items.length,
                            offset: offset,
                            size: size
                        };
                    } else {
                        const errorData = await response.json();
                        let errorMessage = `${response.status} ${response.statusText}`;
                        if (errorData.hasOwnProperty('error') && errorData.error.hasOwnProperty('message')) {
                            errorMessage = errorData.error.message;
                        }
                        console.error('crud.list - HTTP error:', response.status, response.statusText);
                        return {state: 'error', error: errorMessage};
                    }
                } catch (error) {
                    console.error('crud.list - network error:', error);
                    return {state: 'error', error: `Network error: ${error.message}`};
                }
            },
            createArgs: _crudListArgs
        }
    },

    // op //

    'op': {
        'http': {
            func: async (url, params) => {
                try {
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: getRequestHeaders(),
                        body: JSON.stringify(params)
                    });
                    if (response.ok) {
                        const responseData = await response.json();
                        // console.log('op.http - responseData:', responseData);
                        if (responseData.hasOwnProperty('result')) {
                            const wrappedResult = wrapValue(responseData.result);
                            // console.log('op.http - wrappedResult:', wrappedResult);
                            if (url === '/api/auth/login-user') {
                                const accessToken = responseData.result.access_token;
                                if (accessToken) {
                                    localStorage.setItem('access_token', accessToken);
                                    // console.log('op.http - stored access_token in localStorage');
                                }
                            } else if (url === '/api/auth/logout-user' && params.mode !== 'others') {
                                localStorage.removeItem('access_token');
                                // window.location.reload();
                            }
                            return {state: 'result', result: wrappedResult};
                        } else {
                            return {state: 'error', error: 'Response missing result field'};
                        }

                    } else {
                        const errorData = await response.json();
                        let errorMessage = `${response.status} ${response.statusText}`;
                        if (errorData.hasOwnProperty('error') && errorData.error.hasOwnProperty('message')) {
                            errorMessage = errorData.error.message;
                        }
                        console.error('op.http - HTTP error:', response.status, response.statusText);

                        if(url == '/api/auth/logout-user') {
                            localStorage.removeItem('access_token');
                            window.location.reload();
                        }

                        return {state: 'error', error: errorMessage};
                    }
                } catch (error) {
                    console.error('op.http - network error:', error);
                    return {state: 'error', error: `Network error: ${error.message}`};
                }
            },
            createArgs: _opHttpArgs
        }
    },

    // auth //

    'auth': {
        'is_logged_in': {
            func: () => {
                // console.log('auth.is_logged_in - checking login status');
                try {
                    const accessToken = localStorage.getItem('access_token');
                    return {logged_in: !!accessToken, message: 'Logged in, not confirmed with server'};
                } catch (error) {
                    console.error('auth.is_logged_in - error:', error);
                    return {logged_in: false, message: `Error checking login status: ${error.message}`};
                }
            },
            createArgs: _authIsLoggedInArgs
        }
    },

    // file system //

    'file_system': {
        'get_file_content': {
            func: async (app, fileId, fileName, formName) => {
                try {
                    const response = await fetch('/api/file-system/get-file-content', {
                        method: 'POST',
                        headers: getRequestHeaders(),
                        body: JSON.stringify({file_id: fileId})
                    });
                    if (response.ok) {
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = await fileName;
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                        window.URL.revokeObjectURL(url);
                        console.log('file_system.get_file_content - file download completed');
                        app.clientState.forms[formName].state = 'success';
                    } else {
                        const errorData = await response.json();
                        let errorMessage = `${response.status} ${response.statusText}`;
                        if (errorData.hasOwnProperty('error') && errorData.error.hasOwnProperty('message')) {
                            errorMessage = errorData.error.message;
                        }
                        console.error('file_system.get_file_content - HTTP error:', response.status, response.statusText);
                        app.clientState.forms[formName].state = 'error';
                        app.clientState.forms[formName].error = errorMessage;
                        return {state: 'error', error: errorMessage};
                    }
                } catch (error) {
                    console.error('file_system.get_file_content - network error:', error);
                    app.clientState.forms[formName].state = 'error';
                    app.clientState.forms[formName].error = `Network error: ${error.message}`;
                    return {state: 'error', error: `Network error: ${error.message}`};
                } finally {
                    renderLingoApp(app, document.getElementById('lingo-app'), true);
                }
            },
            createArgs: _fileSystemGetFileContentArgs
        }
    },

    // media //

    'media': {
        'get_media_file_content': {
            func: async (app, imageId, fileName, fileOutput) => {
                await fileName;
                try {
                    const response = await fetch('/api/media/get-media-file-content', {
                        method: 'POST',
                        headers: getRequestHeaders(),
                        body: JSON.stringify({image_id: imageId})
                    });
                    if (response.ok) {
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        fileOutput.localUrl = url;
                        fileOutput.status = 'loaded';
                        console.log('media.get_media_file_content - file download completed');
                        return {acknowledged: true, message: 'File download complete'};
                    } else {
                        const errorData = await response.json();
                        let errorMessage = `${response.status} ${response.statusText}`;
                        if (errorData.hasOwnProperty('error') && errorData.error.hasOwnProperty('message')) {
                            errorMessage = errorData.error.message;
                        }
                        console.error('media.get_media_file_content - HTTP error:', response.status, response.statusText);
                        fileOutput.status = 'error';
                        fileOutput.error = errorMessage;
                        return {state: 'error', error: errorMessage};
                    }
                } catch (error) {
                    console.error('media.get_media_file_content - network error:', error);
                    fileOutput.status = 'error';
                    fileOutput.error = `Network error: ${error.message}`;
                    return {state: 'error', error: `Network error: ${error.message}`};
                } finally {
                    renderLingoApp(app, document.getElementById('lingo-app'), true);
                }
            },
            createArgs: _mediaGetMediaFileContentArgs
        }
    }

};

/**
 * LingoApp class - equivalent to Python LingoApp dataclass
 */
class LingoApp {
    constructor(spec, params = {}, state = {}, buffer = [], afterUpdate = null, afterRender = null) {
        this.spec = JSON.parse(JSON.stringify(spec)); // deep copy
        this.params = params;
        this.state = state;
        this.buffer = buffer;
        this.afterUpdate = afterUpdate;
        this.afterRender = afterRender;

        this.parentUrl = this.spec.lingo.parent_url || null;
        this.parentSpec = null;

        console.log('LingoApp()', this.parentUrl)

        //
        // if parent_url is defined, fetch the parent spec
        //

        if(this.parentUrl) {
            const xhr = new XMLHttpRequest();

            try{
                xhr.open('GET', this.parentUrl, false); // false for synchronous request
                xhr.send(null);

            }catch(error){
                console.error('LingoApp() - error during parent spec fetch:', error);
                throw new Error(`Error during parent spec fetch: ${error.message}`);
            }

            if (xhr.status === 200) {
                try {
                    this.parentSpec = JSON.parse(xhr.responseText);
                    console.log('LingoApp() - fetched parent spec:', this.parentSpec);

                } catch (error) {
                    console.error('LingoApp() - error parsing parent spec JSON:', error, xhr.responseText);
                    throw new Error(`Failed to parse parent spec JSON: ${error.message}`);
                }
            } else {
                console.error('LingoApp() - error fetching parent spec:', xhr.status, xhr.statusText);
                throw new Error(`Failed to fetch parent spec: ${xhr.status} - ${xhr.statusText}`);
            }

        }

        this.clientState = {
            forms: {},
            media: {}
        };

        this.timers = {}; // { [timerName]: timeoutId | null }
    }
}

/**
 * Start a timer by name - runs func, then schedules itself based on interval
 */
function startTimer(app, timerName) {
    const timerSpec = app.spec.timers[timerName];
    if (!timerSpec) {
        throw new Error(`timer '${timerName}' not defined in spec`);
    }

    function runTimer() {
        try {
            lingoExecute(app, timerSpec.func);
        } catch (error) {
            console.error(`Timer '${timerName}' func error:`, error);
        }

        const container = document.getElementById('lingo-app');
        if (container) {
            renderLingoApp(app, container);
        }

        let interval;
        if (typeof timerSpec.interval === 'number') {
            interval = timerSpec.interval;
        } else {
            try {
                interval = unwrapValue(lingoExecute(app, timerSpec.interval));
            } catch (error) {
                console.error(`Timer '${timerName}' interval error:`, error);
                interval = -1;
            }
        }

        if (interval >= 0) {
            // interval == 0: re-run on the next event loop tick (setTimeout delay of 0)
            // interval > 0: re-run after interval seconds
            app.timers[timerName] = setTimeout(runTimer, interval * 1000);
        } else {
            // interval < 0: timer self-disabled, will not re-run
            app.timers[timerName] = null;
        }
    }

    runTimer();
}

/**
 * Stop all running timers on an app
 */
function stopAllTimers(app) {
    for (const timerName in app.timers) {
        if (app.timers[timerName] !== null) {
            clearTimeout(app.timers[timerName]);
            app.timers[timerName] = null;
        }
    }
}

/**
 * Create a new LingoApp instance - equivalent to Python lingo_app()
 */
function lingoApp(spec, params = {}, options = {}) {
    const specCopy = JSON.parse(JSON.stringify(spec));
    const instance = new LingoApp(specCopy, params, {}, [], options.afterUpdate, options.afterRender);
    
    // Validate params
    for (const argName in params) {
        if (!(argName in instance.spec.params)) {
            throw new Error(`argument ${argName} not defined in spec`);
        }
    }
    
    lingoUpdateState(instance);

    // Auto-start timers
    if (instance.spec.timers) {
        for (const [timerName, timerSpec] of Object.entries(instance.spec.timers)) {
            if (timerSpec.auto_start) {
                startTimer(instance, timerName);
            }
        }
    }

    return instance;
}

/**
 * Update state values - equivalent to Python lingo_update_state()
 */
function lingoUpdateState(app, ctx = null) {
    for (const [key, value] of Object.entries(app.spec.state)) {
        if ('calc' in value) {
            // This is a calculated value
            const newValue = lingoExecute(app, value.calc, ctx);
            
            // Extract actual value if wrapped
            const actualValue = (typeof newValue === 'object' && newValue !== null && 'value' in newValue)
                ? newValue.value
                : newValue;
            
            const actualType = (typeof newValue === 'object' && newValue !== null && 'type' in newValue)
                ? newValue.type
                : getTypeName(actualValue);
            
            if (!typesMatch(actualType, value.type)) {
                throw new Error(`state.${key} - expression returned type mismatch: ${actualType}, expected: ${value.type}`);
            }
            app.state[key] = actualValue;
        } else {
            // Non-calculated value, set to default if not already set
            if (!(key in app.state)) {
                if (!('default' in value)) {
                    throw new Error(`state.${key} - missing default value`);
                }
                let defaultValue = value.default;
                const typeName = getTypeName(defaultValue);
                
                if (value.type === 'datetime' && typeName === 'str') {
                    console.log(`state.${key} - parsing datetime default value:`, defaultValue);
                    defaultValue = new Date(defaultValue);
                }else if (!typesMatch(typeName, value.type)) {
                    throw new Error(`state.${key} - default value type mismatch : ${typeName} != ${value.type}`);
                }

                app.state[key] = defaultValue;

                console.log(`state.${key} - setting default value:`, defaultValue, 'type:', typeName);
            }
        }
    }

    // Call afterUpdate callback if defined
    if (app.afterUpdate) {
        app.afterUpdate(app);
    }
    
    return app;
}

/**
 * type helpers
 */
function getTypeName(value) {
    // console.log('getTypeName()', typeof value, value);
    if (typeof value === 'string') return 'str';
    if (typeof value === 'number') {
        return Number.isInteger(value) ? 'int' : 'float';
    }
    if (typeof value === 'boolean') return 'bool';
    if (value instanceof Date) return 'datetime';
    if (Array.isArray(value)) return 'list';
    if (typeof value === 'object' && value !== null && 'type' in value && 'value' in value) {
        return value.type;
    }
    if (typeof value === 'object' && 'fields' in value && 'name' in value) {
        return 'model';
    }
    if (typeof value === 'object' && 'params' in value && 'result' in value && 'func' in value) {
        return 'op';
    }
    if (typeof value === 'object') return 'struct';
    return typeof value;
}

function typesMatch(a, b, allowAny = true) {
    /*
    Check if two type names match, with option to allow 'any' type
    */
    if(a === b){
        return true;
    }else if (allowAny && (a === 'any' || b === 'any')) {
        return true;
    }else{
        return false;
    }
}

function unwrapValue(data) {
    if (typeof data === 'object' && data !== null && 'value' in data && 'type' in data) {
        return data.value;
    }else{
        return data;
    }
}

function wrapValue(value) {
    /*
    Wrap a primitive value in a type/value object,
    or return an already wrapped object as is
    */

    if (typeof value === 'object' && value !== null && 'value' in value && 'type' in value) {
        return value;
    }else{
        const typeName = getTypeName(value);
        return {type: typeName, value: value};
    }
}

/**
 * Format date to string - equivalent to Python datetime formatting
 */
function formatDateTime(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
}

/**
 * Main expression executor - equivalent to Python lingo_execute()
 */
function lingoExecute(app, expression, ctx = null) {
    // Calculate expression
    let result;

    // console.log('lingoExecute()', expression, ctx);
    
    if (typeof expression === 'object' && expression !== null && !Array.isArray(expression)) {
        if ('set' in expression) {
            result = renderSet(app, expression, ctx);
        } else if ('state' in expression) {
            result = renderState(app, expression, ctx);
        } else if ('params' in expression) {
            result = renderParams(app, expression, ctx);
        } else if ('op' in expression) {
            result = renderOp(app, expression, ctx);
        } else if ('call' in expression) {
            result = renderCall(app, expression, ctx);
        } else if ('block' in expression) {
            result = renderBlock(app, expression, ctx);
        } else if ('lingo' in expression) {
            result = renderLingo(app, expression, ctx);
        } else if ('branch' in expression) {
            result = renderBranch(app, expression, ctx);
        } else if ('switch' in expression) {
            result = renderSwitch(app, expression, ctx);
        } else if ('heading' in expression) {
            result = renderHeading(app, expression, ctx);
        } else if ('form' in expression) {
            result = renderForm(app, expression, ctx);
        } else if ('args' in expression) {
            result = renderArgs(app, expression, ctx);
        } else if ('self' in expression) {
            return renderSelf(app, expression, ctx);
        } else if ('model' in expression) {
            return renderModel(app, expression, ctx);
        } else if ('breadcrumbs' in expression) {
            return renderBreadcrumbs(app, expression, ctx);
        } else {
            result = expression;
        }
    } else {
        result = expression;
    }
    
    // Format return value - wrap primitives in type/value object
    
    if (typeof result === 'string' || typeof result === 'number' || 
               typeof result === 'boolean' || result instanceof Date) {
        // Primitive types - wrap with type info
        // console.log('lingo - wrapping primitive result', expression, result);
        return {type: getTypeName(result), value: result};
    } else if (Array.isArray(result)) {
        // Array - return as list type
        let returnList;
        
        // if item is object call lingoExecute and append the result, otherwise append the item as is
        if (result.every(item => typeof item === 'object' && item !== null)) {
            returnList = result.map(item => lingoExecute(app, item, ctx));
        } else {
            returnList = result;
        }
        return returnList;

    }else if (typeof result === 'object' && result !== null) {
        // Already an object or array, return as is
        // console.log('lingo - returning object result', expression, result, result instanceof Date);
        return result;
    } else {
        // Unknown type
        console.error('lingo - unsupported return type', expression, typeof result, result);
        throw new Error(`Unsupported return type: ${typeof result}`);
    }
}

/**
 * Render output buffer - equivalent to Python render_output()
 */
function renderOutput(app, ctx = null) {
    app.buffer = [];
    // console.log('renderOutput()', typeof app.spec.output, app.spec.output.length);
    for (let n = 0; n < app.spec.output.length; n++) {
        const element = app.spec.output[n];
        try {
            const rendered = lingoExecute(app, element, ctx);
            // console.log('Rendered output element:', typeof rendered, rendered);
            if (typeof rendered === 'object' && rendered !== null && !Array.isArray(rendered)) {
                app.buffer.push(rendered)
            } else if (Array.isArray(rendered)) {
                for (const item of rendered) {
                    if (typeof item === 'object' && item !== null && !Array.isArray(item)) {
                        app.buffer.push(item);
                    } else {
                        app.buffer.push(...item);
                    }
                }
            } else {
                throw new Error(`Rendered output is not an object or array: ${typeof rendered} - ${n}`);
            }
        } catch (error) {
            console.error(`Error rendering output element ${n}:`, error, element);
            throw new Error(`Render error - output ${n} - ${error.message}`);
        }
    }
    return app.buffer;
}

/**
 * Render block - equivalent to Python render_block()
 */
function renderBlock(app, element, ctx = null) {
    const elements = [];
    // console.log('renderBlock()', element);
    for (let n = 0; n < element.block.length; n++) {
        const childElement = element.block[n];
        try {
            elements.push(lingoExecute(app, childElement, ctx));
        } catch (error) {
            throw new Error(`block error, element ${n}: ${error.message}`);
        }
    }
    return elements;
}

/**
 * Render branch (if/elif/else) - equivalent to Python render_branch()
 */
function renderBranch(app, element, ctx = null) {
    const branches = element.branch;
    const numBranches = branches.length;
    const lastIndex = numBranches - 1;
    
    if (numBranches < 2) {
        throw new Error('branch - must have at least 2 cases');
    }
    
    if (!('else' in branches[lastIndex])) {
        throw new Error('branch - last element must be else case');
    }
    
    for (let n = 0; n < branches.length; n++) {
        const branch = branches[n];
        let expr, then;
        
        // Get expression for branch
        if ('if' in branch) {
            if (n !== 0) {
                throw new Error(`branch ${n} - must be if case`);
            }
            expr = branch.if;
        } else if ('elif' in branch) {
            if (n === 0 || n === lastIndex) {
                throw new Error(`branch ${n} - elif must not be first or last case`);
            }
            expr = branch.elif;
        } else if ('else' in branch) {
            if (n !== lastIndex) {
                throw new Error(`branch ${n} - else case must be last case`);
            }
            expr = true;
        } else {
            throw new Error(`branch ${n} - missing if/elif/else key`);
        }
        
        // Get then expression
        if ('then' in branch) {
            then = branch.then;
        } else if ('else' in branch) {
            then = branch.else;
        } else {
            throw new Error(`branch ${n} - missing then expression`);
        }
        
        // Execute expression
        try {
            const conditionResult = lingoExecute(app, expr, ctx);
            // Extract actual value if wrapped
            const condition = (typeof conditionResult === 'object' && conditionResult !== null && 'value' in conditionResult)
                ? conditionResult.value
                : conditionResult;
            
            if (condition) {
                try {
                    // console.log(`branch then condition matched`, then);
                    const thenResult = lingoExecute(app, then, ctx);
                    // console.log(`branch then result`, thenResult);
                    return thenResult;
                } catch (error) {
                    throw new Error(`branch ${n} - error processing then expression: ${error.message}`);
                }
            }
        } catch (error) {
            throw new Error(`branch ${n} - error processing condition: ${error.message}`);
        }
    }
    
    throw new Error('invalid branch expression');
}

/**
 * Render switch statement - equivalent to Python render_switch()
 */
function renderSwitch(app, expression, ctx = null) {
    try {
        const switchExpr = expression.switch.expression;
        const cases = expression.switch.cases;
        const defaultCase = expression.switch.default;
        
        if (cases.length === 0) {
            throw new Error('switch - must have at least one case');
        }
        
        const valueResult = lingoExecute(app, switchExpr, ctx);
        // Extract actual value if wrapped
        const value = (typeof valueResult === 'object' && valueResult !== null && 'value' in valueResult)
            ? valueResult.value
            : valueResult;
        
        for (const caseItem of cases) {
            // Also evaluate case expression if it's not a literal
            let caseValue = caseItem.case;
            if (typeof caseValue === 'object' && caseValue !== null && !('value' in caseValue)) {
                // It's an expression, evaluate it
                const caseResult = lingoExecute(app, caseValue, ctx);
                caseValue = (typeof caseResult === 'object' && caseResult !== null && 'value' in caseResult)
                    ? caseResult.value
                    : caseResult;
            }
            
            if (value === caseValue) {
                return lingoExecute(app, caseItem.then, ctx);
            }
        }
        
        return lingoExecute(app, defaultCase, ctx);
    } catch (error) {
        throw new Error(`switch - ${error.message}`);
    }
}

/**
 * Render params access - equivalent to Python render_params()
 */
function renderParams(app, expression, ctx = null) {
    const fieldNames = Object.keys(expression.params);
    if (fieldNames.length !== 1) {
        throw new Error('params - must have exactly one param field');
    }
    const fieldName = fieldNames[0];
    
    if (!(fieldName in app.spec.params)) {
        throw new Error(`params - undefined field: ${fieldName}`);
    }
    
    const paramDef = app.spec.params[fieldName];
    let value;
    
    if (fieldName in app.params) {
        value = app.params[fieldName];
    } else if ('default' in paramDef) {
        value = paramDef.default;
    } else {
        throw new Error(`params - missing value for field: ${fieldName}`);
    }
    
    if (getTypeName(value) !== paramDef.type) {
        throw new Error(`params.${fieldName} - value type mismatch: ${paramDef.type} != ${getTypeName(value)}`);
    }
    
    return value;
}

/**
 * Render state setter - equivalent to Python render_set()
 */
function renderSet(app, expression, ctx = null) {
    // console.log('renderSet()', app, expression);
    try {
        
        // init
        let target;             // requested target frome expression
        let stateToSet;         // the object to be updated
        let setStateValue;      // the function to call to update state
        let setStructValue;     // the function to call to update a struct field if applicable
        let fieldType;          // type of value being set
        let fieldName;          // the name of the state field being set
        let fieldDisplayName;   // the name of the field to display in error messages (includes struct field if applicable)

        if('state' in expression.set){

            target = expression.set.state;
            
            // get state field

            const fieldNames = Object.keys(target);
            if (fieldNames.length !== 1) {
                throw new Error('set - must have exactly one state field');
            }
            fieldName = fieldNames[0];

            if(!app.spec.state.hasOwnProperty(fieldName)){
                throw new Error(`set - state field not found: ${fieldName}`);
            }

            stateToSet = app.state[fieldName];
            setStateValue = (newValue) => app.state[fieldName] = newValue;
            setStructValue = (structFieldName, newValue) => app.state[fieldName][structFieldName] = newValue;
            fieldType = app.spec.state[fieldName].type;
            fieldDisplayName = `state.${fieldName}`;

        }else if('clientState' in expression.set){

            if('forms' in expression.set.clientState){
                target = expression.set.clientState.forms;
                const formNames = Object.keys(expression.set.clientState.forms);
                if (formNames.length !== 1) {
                    throw new Error('set - must have exactly one form in clientState');
                }
                fieldName = formNames[0];
                if (!app.clientState.forms.hasOwnProperty(fieldName)) {
                    throw new Error(`set - clientState form not found: ${fieldName}`);
                }

                stateToSet = app.clientState.forms[fieldName];
                setStateValue = (newValue) => app.clientState.forms[fieldName] = newValue;
                setStructValue = (structFieldName, newValue) => app.clientState.forms[fieldName][structFieldName] = newValue;
                fieldType = getTypeName(stateToSet);
                fieldDisplayName = `clientState.forms.${fieldName}`;

            }else{
                throw new Error('set - clientState must have forms field');
            }
        }else{
            throw new Error('set - must have either state or clientState field');
        }

        // if is a struct, get struct field name
        let value = lingoExecute(app, expression.to, ctx);

        const setValue = () => {

            const newType = getTypeName(value);
            const outValue = unwrapValue(value);

            if(fieldType === 'struct'){
                // console.log('set - setting struct fields:', fieldName, outValue);

                /*
                there are 2 ways to set a struct field:
                    1. single values
                        set: {state: {my_struct_variable: {struct_field: {}}}}
                        to: 5

                        in set, you specify the state variable and struct field
                        and in to you provide a primitive value

                    2. multiple fields at once
                        set: {state: {my_struct_variable: {}}}
                        to: {struct_field1: 5, struct_field2: "hello"}

                        in set, you specify only the state variable
                        and in to you provide an object with field names and values,
                        the fields that are provided will be updated and other fields
                        will remain unchanged
                */

                const numStructKeys = Object.keys(target[fieldName]).length;
                let structSetType;
                if (numStructKeys == 0) {
                    structSetType = 'multiple';
                }else if (numStructKeys == 1) {
                    structSetType = 'single';
                }else{
                    throw new Error('set - struct set must have either zero fields to use multi set or one field to use single set');
                }

                if(structSetType === 'single'){
                    // struct field name is the only key in target[fieldName]
                    const structFieldName = Object.keys(target[fieldName])[0];

                    if (!(structFieldName in stateToSet)) {
                        throw new Error(`set - struct field not found: ${fieldName}.${structFieldName}`);
                    }

                    const origStructValue = stateToSet[structFieldName];

                    // verify type of outValue matches type of origStructValue
                    const newStructType = getTypeName(origStructValue);
                    const outValueType = getTypeName(outValue);
                    if (!typesMatch(outValueType, newStructType)) {
                        throw new Error(`set - type mismatch: ${newStructType} != ${outValueType} - ${fieldDisplayName}.${structFieldName}`);
                    }

                    setStructValue(structFieldName, outValue);

                // console.log(`set - setting struct field: ${fieldDisplayName}.${structFieldName} =`, outValue);
                }else{

                    // console.log('set - setting multiple struct fields for', fieldDisplayName, outValue);

                    // for each field in outValue, set the corresponding struct field and ensure type matches

                    for(const [structFieldName, structFieldValue] of Object.entries(outValue)){

                        if (!(structFieldName in stateToSet)) {
                            throw new Error(`set - struct field not found: ${fieldDisplayName}.${structFieldName}`);
                        }

                        const origStructValue = stateToSet[structFieldName];

                        // verify type of `structFieldValue` matches type of `origStructValue`
                        const newStructType = getTypeName(origStructValue);
                        const structFieldValueType = getTypeName(structFieldValue);
                        if (!typesMatch(structFieldValueType, newStructType)) {
                            throw new Error(`set - type mismatch: ${newStructType} != ${structFieldValueType} - ${fieldDisplayName}.${structFieldName}`);
                        }

                        setStructValue(structFieldName, structFieldValue);

                        // console.log(`set - setting struct field: ${fieldDisplayName}.${structFieldName} =`, structFieldValue);
                    }
                }

            }else{
                if (!typesMatch(newType, fieldType)) {
                    throw new Error(`set - type mismatch: ${fieldType} != ${newType} - ${fieldDisplayName}`, outValue);
                }
                setStateValue(outValue);
                // console.log(`set - setting value: ${fieldDisplayName} =`, outValue);
            }
        }

        // if value is a promise, await it
        if (value instanceof Promise) {
            value.then(result => {
                value = result;
                setValue();

                // rerender output after state update
                renderLingoApp(app, document.getElementById('lingo-app'), ctx);
            });
            return value;
        }else{
            setValue();
            return value;
        }

    } catch (error) {
        throw new Error(`set - ${error.message}`);
    }
}

/**
 * Render state access - equivalent to Python render_state()
 */
function renderState(app, expression, ctx = null) {
    const fieldNames = Object.keys(expression.state);
    if (fieldNames.length !== 1) {
        console.error('state - invalid expression, must have exactly one state field', expression);
        throw new Error('state - must have exactly one state field');
    }
    const fieldName = fieldNames[0];
    
    if (!(fieldName in app.state)) {
        throw new Error(`state - field not found: ${fieldName}`);
    }

    // check if expression.state.fieldName is an object with a field
    if (typeof expression.state[fieldName] === 'object' && expression.state[fieldName] !== null) {
        // check for exactly one key
        const keys = Object.keys(expression.state[fieldName]);
        if (keys.length === 1) {
            const structFieldName = keys[0];
            return app.state[fieldName][structFieldName];
        }else if(keys.length > 1){
            throw new Error('state - cannot access struct field, multiple fields found in expression');
        }
    }

    return app.state[fieldName];
    
}

/**
 * Render lingo expression - equivalent to Python render_lingo()
 */
function renderLingo(app, element, ctx = null) {
    const result = lingoExecute(app, element.lingo, ctx);
    
    const convert = (x) => {
        if (x instanceof Date) {
            return formatDateTime(x);
        }
        return String(x);
    };

    console.log('lingo - renderLingo result', element, result);
    
    // Handle wrapped format {type: ..., value: ...}
    if (typeof result === 'object' && result !== null && 'value' in result) {
        if (['str', 'int', 'float', 'bool', 'datetime'].includes(result.type)) {
            return {text: convert(result.value)};
        } else if (result.type === 'list') {
            return {text: result.value.map(item => convert(item)).join(', ')};
        } else {
            throw new Error(`lingo - unexpected result value type: ${result.type}`);
        }
    } else if (typeof result === 'object' && result !== null && 'text' in result) {
        // Already a text element
        return result;
    } else if (Array.isArray(result)) {
        return {text: result.map(item => convert(item)).join(', ')};
    } else {
        console.error('lingo - invalid result type', element, result);
        throw new Error(`lingo - invalid result type: ${typeof result}`, result);
    }
}

/**
 * Render heading - equivalent to Python render_heading()
 */
function renderHeading(app, element, ctx = null) {
    if (!('level' in element)) {
        throw new Error('heading - missing level key');
    }
    
    if (element.level < 1 || element.level > 6) {
        throw new Error('heading - level must be between 1 and 6');
    }
    
    try {
        const heading = lingoExecute(app, element.heading, ctx);
        let headingText;
        
        if ('text' in heading) {
            headingText = heading.text;
        } else if (typeof heading === 'object' && heading !== null && 'value' in heading) {
            // Handle wrapped format {type: ..., value: ...}
            headingText = String(heading.value);
        } else if (typeof heading === 'string') {
            headingText = heading;
        } else if (typeof heading === 'number' || typeof heading === 'boolean') {
            headingText = String(heading);
        } else {
            throw new Error(`heading - invalid heading type: ${typeof heading} - expected string or object with text key`);
        }
        
        return {heading: headingText, level: element.level};
    } catch (error) {
        throw new Error(`heading - error processing heading expression: ${error.message}`);
    }
}

/**
 * Render form - creates a form element with fields
 */
function renderForm(app, element, ctx = null) {
    // console.log('renderForm()', element);
    if (!('fields' in element.form)) {
        throw new Error('form - missing fields key');
    }
    return element;
}

/**
 * Render operation call - equivalent to Python render_op()
 */
function renderOp(app, expression, ctx = null) {

    /*

    There are two ways to use an op, interactively with 
    a form and a call button, or non-interactively and
    return the result directly. The interactive form
    will call the server to handle the op, but the non-interactive form
    will locally execute the op defined in the page spec's op field.

    Interactive op example:

        {"op": {
            "bind": {"state": {"op_view_state": {}}},
            "interactive": true,
            "http": {"state": {"op_api_url": {}}},
            "definition": {"params": {"op_definition": {}}}
        }}

    Non-interactive op example:

        {"op": {"randomize_number": {"max": 100}}}

        NOTE: do not supply interactive=false, to use
        this syntax there must be only one key which is
        the op name which contains the args.

    */

    let isInteractive = false;
    if ('interactive' in expression.op) {
        if(expression.op.interactive !== true){
            throw new Error('op - interactive field must be true if present');
        }
        isInteractive = true;
    }else{
        isInteractive = false;
    }

    if(isInteractive){

        // interactive op //

        const op = expression.op;
        // console.log('renderOp() - interactive op', op);

        if(!op.hasOwnProperty('definition')){
            throw new Error('op - missing definition for interactive op');
        }

        const definitioResult = lingoExecute(app, op.definition, ctx);

        if(typeof definitioResult === 'object' && definitioResult !== null && 'value' in definitioResult){
            if(definitioResult.type === 'str'){
                // split value by dot and confirrm it has 2 parts, module and op name
                const parts = definitioResult.value.split('.');
                if(parts.length !== 2){
                    console.error('op - definition as string reference must be in format "module.op_name"', definitioResult.value);
                    throw new Error('op - definition as string reference must be in format "module.op_name"');
                }
                const [moduleName, opName] = parts;

                // get from app.parentSpec.modules or throw error if not found
                if(!app.parentSpec || !app.parentSpec.modules || !app.parentSpec.modules.hasOwnProperty(moduleName)){
                    console.error('op - definition module not found in parent spec modules', moduleName, app.parentSpec.modules);
                    throw new Error(`op - definition module not found in parent spec modules: ${moduleName}`);
                }
                const module = app.parentSpec.modules[moduleName];
                if(!module.hasOwnProperty('ops') || !module.ops.hasOwnProperty(opName)){
                    console.error('op - definition op not found in parent spec module ops', opName, module.ops);
                    throw new Error(`op - definition op not found in parent spec module ops: ${opName}`);
                }
                definition = module.ops[opName];


            }else if(definitioResult.type === 'op'){
                definition = definitioResult.value;
            }else{
                console.error('op - definition expression must return type op', definitioResult);
                throw new Error('op - definition expression must return type op');
            }
            
        }else{
            definition = definitioResult;
        }

        if(!definition.hasOwnProperty('params')){
            console.error('op - definition missing params field for interactive op', definition);
            throw new Error('op - missing params in definition for interactive op');
        }

        if(!definition.hasOwnProperty('result')){
            throw new Error('op - missing result in definition for interactive op');
        }

        if(!op.hasOwnProperty('bind')){
            throw new Error('op - missing bind for interactive op');
        }

        if(!op.bind.hasOwnProperty('state')){
            throw new Error('op - bind must bind to state for interactive op');
        }

        if(!op.hasOwnProperty('http')){
            throw new Error('op - missing http for interactive op');
        }

        // render op.auto_submit if provided, otherwise default to false
        let autoSubmit;
        if (expression.op.hasOwnProperty('auto_submit')) {
            autoSubmit = unwrapValue(lingoExecute(app, expression.op.auto_submit, ctx));
        }else{
            autoSubmit = false;
        }

        // console.log('renderOp() - autoSubmit:', autoSubmit, expression.op);

        // bind state //

        const stateKeys = Object.keys(op.bind.state);
        if(stateKeys.length !== 1){
            throw new Error('op - bind state must have exactly one field for interactive op');
        }

        const stateField = stateKeys[0];

        if(!app.spec.state.hasOwnProperty(stateField)){
            throw new Error(`op - bind state field not found: ${stateField}`);
        }

        // create form element //

        const url = unwrapValue(lingoExecute(app, op.http, ctx));

        const submitButtonText = expression.op.submit_button_text ? unwrapValue(lingoExecute(app, expression.op.submit_button_text, ctx)) : 'Submit';

        const formElement = {
            form: {
                fields: definition.params,
                bind: op.bind,
                submit_button_text: submitButtonText,
                auto_submit: autoSubmit,
                action: {
                    set: {state: {[stateField]: {}}},
                    to: {
                        call: 'op.http',
                        args: {
                            url: url,
                            data: app.state[stateField].data,
                            bind: op.bind
                        }
                    }
                }
            }
        };

        // initialize showSecureResultFields in bound state //

        if (!app.state[stateField].hasOwnProperty('showSecureResultFields')) {
            app.state[stateField].showSecureResultFields = {};
        }

        // collect secure fields from result definition //

        const secureResultFields = {};
        if (definition.result && definition.result.fields) {
            for (const [fieldKey, fieldSpec] of Object.entries(definition.result.fields)) {
                if (fieldSpec.secure) {
                    secureResultFields[fieldKey] = fieldSpec;
                    if (!(fieldKey in app.state[stateField].showSecureResultFields)) {
                        app.state[stateField].showSecureResultFields[fieldKey] = false;
                    }
                }
            }
        }

        // build result display based on current op state //

        const currentOpState = app.state[stateField];
        let resultDisplayElements;

        if (currentOpState.state === 'result') {
            resultDisplayElements = [{text: 'success ', style: {color: 'green', bold: true}}];
            const unwrapped = unwrapValue(currentOpState.result);

            if (Object.keys(secureResultFields).length > 0 && typeof unwrapped === 'object' && unwrapped !== null) {
                const redactedValue = {};
                for (const [key, value] of Object.entries(unwrapped)) {
                    if (secureResultFields.hasOwnProperty(key) && !currentOpState.showSecureResultFields[key]) {
                        redactedValue[key] = 'REDACTED';
                    } else {
                        redactedValue[key] = value;
                    }
                }
                
                resultDisplayElements.push({type: 'struct', value: redactedValue});

                for (const fieldKey of Object.keys(secureResultFields)) {
                    const showSecureResultFields = currentOpState.showSecureResultFields;
                    resultDisplayElements.push({
                        button: {
                            clientFunction: () => {
                                showSecureResultFields[fieldKey] = !showSecureResultFields[fieldKey];
                                renderLingoApp(app, document.getElementById('lingo-app'), true);
                            }
                        },
                        text: showSecureResultFields[fieldKey] ? `hide ${fieldKey}` : `show ${fieldKey}`
                    });
                }
            } else {
                resultDisplayElements.push(currentOpState.result);
            }
        } else if (currentOpState.state === 'error') {
            resultDisplayElements = [
                {text: 'error: ', style: {color: 'red', bold: true}},
                {text: currentOpState.error}
            ];
        } else if (currentOpState.state === 'loading') {
            resultDisplayElements = [{text: 'Loading...', style: {italic: true}}];
        } else {
            const defaultInstruction = 'Please fill out the form and submit.';
            const instruction = expression.op.hasOwnProperty('instruction') ? unwrapValue(lingoExecute(app, expression.op.instruction, ctx)) : defaultInstruction;
            resultDisplayElements = [{text: instruction, style: {italic: true}}];
        }

        let elements = [];
        elements.push(formElement);
        elements.push(...resultDisplayElements);
        return elements;

    }else{

        // non-interactive op //

        // init

        const keys = Object.keys(expression.op);
        if (keys.length !== 1) {
            throw new Error('op - must have exactly one op field');
        }
        const opName = keys[0];
        const opArgs = expression.op[opName];
        
        if (!(opName in app.spec.ops)) {
            throw new Error(`op - undefined op: ${opName}`);
        }
        
        const opDef = app.spec.ops[opName];
        if (!('func' in opDef)) {
            throw new Error(`op - missing func for op: ${opName}`);
        }

        // run op function
        
        return lingoExecute(app, opDef.func, opArgs);
    }
}

/**
 * Render function call - equivalent to Python render_call()
 */
function renderCall(app, expression, ctx = null) {
    const _args = expression.args || {};
    
    const nameSplit = expression.call.split('.');
    const nameDepth = nameSplit.length;
    
    if (nameDepth < 1 || nameDepth > 2) {
        throw new Error('call - invalid function name');
    }
    
    // Get function definition
    let definition;
    try {
        if (nameDepth === 1) {
            definition = lingoFunctionLookup[nameSplit[0]];
        } else {
            definition = lingoFunctionLookup[nameSplit[0]][nameSplit[1]];
        }
    } catch (error) {
        throw new Error(`call - undefined function: ${expression.call}`);
    }

    if (typeof definition === 'undefined' || definition === null) {
        throw new Error(`call - undefined function: ${expression.call}`);
    }

    // console.log('call - function definition', expression, definition);
    
    const func = definition.func;
    const argsDef = definition.args || {};
    
    // Handle functions with custom arg handling
    if (typeof definition.createArgs === 'function') {
        const args = definition.createArgs(app, expression, ctx);
        return definition.func(...args);
    }
    
    // Validate and render args
    const renderedArgs = {};
    const argTypes = {}; // Track original types for float detection
    for (const [argName, argExpression] of Object.entries(_args)) {
        if (!(argName in argsDef)) {
            throw new Error(`call - unknown arg: ${argName}`);
        }
        
        const value = lingoExecute(app, argExpression, ctx);
        
        // If value is a list, we need to evaluate any dict expressions in it
        if (Array.isArray(value)) {
            const evaluatedList = [];
            for (const item of value) {
                if (typeof item === 'object' && item !== null && !('value' in item && 'type' in item) && !Array.isArray(item)) {
                    // It's an unevaluated expression - evaluate it with the current context
                    const evalItem = lingoExecute(app, item, ctx);
                    if (typeof evalItem === 'object' && evalItem !== null && 'value' in evalItem) {
                        evaluatedList.push(evalItem.value);
                    } else {
                        evaluatedList.push(evalItem);
                    }
                } else {
                    // It's a literal value
                    evaluatedList.push(item);
                }
            }
            renderedArgs[argName] = evaluatedList;
            argTypes[argName] = 'list';
        } else {
            // Extract value if it's wrapped in a result object
            const actualValue = (typeof value === 'object' && value !== null && 'value' in value) 
                ? value.value 
                : value;
            
            // Track type for float detection
            const valueType = (typeof value === 'object' && value !== null && 'type' in value)
                ? value.type
                : getTypeName(actualValue);
            
            renderedArgs[argName] = actualValue;
            argTypes[argName] = valueType;
        }
    }

    // console.log('call - rendered args', expression.call, renderedArgs);
    
    // Call function based on signature
    let returnValue;
    if (definition.sig === 'kwargs') {
        returnValue = func(renderedArgs);
        // console.log('call - kwargs function return value', func, renderedArgs, typeof returnValue, returnValue);
    } else {
        // Positional args - build args list with defaults
        const argsList = [];
        for (const argName of Object.keys(argsDef)) {
            if (argName in renderedArgs) {
                argsList.push(renderedArgs[argName]);
            } else if ('default' in argsDef[argName]) {
                argsList.push(argsDef[argName].default);
            } else {
                throw new Error(`call - missing required arg: ${argName}`);
            }
        }
        returnValue = func(...argsList);
        // console.log('call - positional function return value', func, argsList, typeof returnValue, returnValue);
    }

    // console.log('call - function return value', expression.call, typeof returnValue, returnValue);
    
    // Format return value similar to Python
    if (Array.isArray(returnValue)) {
        // Check if all elements are of the same type
        const elementTypes = new Set();
        const elements = [];
        for (const item of returnValue) {
            const itemType = getTypeName(item);
            elementTypes.add(itemType);
            elements.push(item);
        }
        
        // Return list with type info
        if (elementTypes.size === 1) {
            const elementType = Array.from(elementTypes)[0];
            return {type: 'list', value: elements, element_type: elementType};
        } else {
            return {type: 'list', value: elements, element_type: 'any'};
        }
    } else if (typeof returnValue === 'object' && returnValue !== null && !Array.isArray(returnValue)) {
        // Already formatted or object
        return returnValue;
    } else {
        // Primitive value - wrap with type info
        let resultType = getTypeName(returnValue);
        
        // For arithmetic operations, if any arg was a float, result is float
        // Also, division always returns float
        if (typeof returnValue === 'number' && expression.call) {
            const arithmeticOps = ['add', 'sub', 'mul', 'mod', 'pow'];
            if (expression.call === 'div') {
                resultType = 'float';
            } else if (arithmeticOps.includes(expression.call)) {
                const hasFloatArg = Object.values(argTypes).some(t => t === 'float');
                if (hasFloatArg) {
                    resultType = 'float';
                }
            }
        }
        
        return {type: resultType, value: returnValue};
    }
}


/**
 * Render args access - equivalent to Python render_args()
 */
function renderArgs(app, expression, ctx = null) {
    const argName = expression.args;
    if (!ctx || !(argName in ctx)) {
        throw new Error(`args - undefined arg: ${argName}`);
    }
    return ctx[argName];
}

/**
 * Render self access - equivalent to Python render_self()
 */
function renderSelf(app, expression, ctx = null) {
    try {
        return ctx.self[expression.self];
    } catch (error) {
        throw new Error('self - missing self context');
    }
}

/**
 * Render model widget
 */

function renderModel(app, element, ctx = null) {
    // console.log('renderModel()', element);
    switch (element.model.display) {
        case 'create':
            return _renderModelCreate(app, element, ctx);
        case 'read':
            return _renderModelRead(app, element, ctx);
        case 'delete':
            return _renderModelDelete(app, element, ctx);
        case 'list':
            return _renderModelList(app, element, ctx);
        default:
            throw new Error(`renderModel - unknown display type: ${element.model.display}`);
    }
}

function _renderModelRead(app, element, ctx = null) {

    //
    // init
    //

    if(!element.model.hasOwnProperty('bind')){
        throw new Error('renderModelRead - missing model bind definition');
    }
    if(!element.model.bind.hasOwnProperty('state')){
        throw new Error('renderModelRead - model bind definition must bind to state');
    }

    // get first (and only) field in bind.state
    const stateKeys = Object.keys(element.model.bind.state);
    if( stateKeys.length !== 1 ){
        throw new Error('renderModelRead - model bind.state must have exactly one field');
    }

    if(!element.model.hasOwnProperty('definition')){
        throw new Error('renderModelRead - missing model definition');
    }
    const definition = lingoExecute(app, element.model.definition, ctx);

    const stateField = stateKeys[0];

    let state = app.state[stateField];

    /* assume state is an object and ensure defaults are set */
    if (!state.hasOwnProperty('data')) state.data = null;
    if (!state.hasOwnProperty('state')) state.state = 'pending';
    if (!state.hasOwnProperty('error')) state.error = '';

    //
    // buttons
    //

    let elements = [];

    // load //

    const loadScript = {
        set: {state: {[stateField]: {}}},
        to: {
            call: 'crud.read', 
            args: {
                http: element.model.http,
                model_id: element.model.model_id,
                bind: element.model.bind
            }
        }
    };

    elements.push({
        button: loadScript,
        text: 'load',
        disabled: state.state === 'editing' || state.state === 'loading'
    });

    // edit //

    const editScript = {
        set: {state: {[stateField]: {state: {}}}},
        to: 'editing'
    };

    elements.push({
        button: editScript,
        text: 'edit',
        disabled: state.state !== 'loaded' && state.state !== 'edited'
    });

    // cancel //

    const cancelScript = {
        set: {state: {[stateField]: {state: {}}}},
        to: 'loaded'
    };

    elements.push({
        button: cancelScript,
        text: 'cancel',
        disabled: state.state !== 'editing'
    });

    // status //

    elements.push(...[
        {break: 1},
        {text: 'status: ', style: {bold: true}},
    ]);

    const stateSwitch = {
        switch: {
            expression: { type: 'str', value: state.state },
            cases: [
                {
                    case: 'loaded',
                    then: { 
                        block: [
                            { text: 'loaded', style: {color: 'green', bold: true} },
                        ]
                     }
                },
                {
                    case: 'edited',
                    then: { 
                        block: [
                            { text: 'edited', style: {color: 'green', bold: true} },
                        ]
                     }
                },
                {
                    case: 'error',
                    then: { 
                        block: [
                            { text: 'error: ', style: {color: 'red', bold: true} },
                            { text: state.error, style: {color: 'red'} }
                        ]
                     }
                }
            ],
            default: {
                block: [
                    { text: state.state, style: {italic: true} }
                ]
            }
        }
    };

    elements.push(...renderSwitch(app, stateSwitch, ctx));

    //
    // view item
    //

    if (state.state === 'editing') {
        // view editable form
        elements.push({
            form: {
                fields: definition.fields,
                bind: element.model.bind,
                action: {
                    set: {state: {[stateField]: {}}},
                    to: {
                        call: 'crud.update',
                        args: {
                            http: element.model.http,
                            bind: element.model.bind,
                            data: app.state[stateField].data
                        }
                    }
                }
            }
        });

    }else if(state.state === 'pending'){
        // view loading placeholder
        const placeholder = {};

        for (const field of Object.keys(definition.fields)) {
            placeholder[field] = '...';
        }

        elements.push({
            type: 'struct',
            value: placeholder,
        });
        
    }else{
        // view loaded data as struct key/value table
        // iterate over each key/value in state.data
        // and convert to list of arrays where each array is [key, value]
        let convertedFields = [];
        // console.log('renderModelRead - state.data:', state.data);
        for (const field of Object.keys(state.data)) {

            const fieldDef = definition.fields[field] || {};

            // additional actions for field

            // console.log('renderModelRead - field definition:', fieldDef);
            let additional;
            
            if(fieldDef.type === 'list' && fieldDef.element_type === 'foreign_key'){

                const table = fieldDef.references.table.replaceAll('_', '-');
                const refModule = fieldDef.references.module.replaceAll('_', '-');
                const ids = state.data[field] || [];

                if(table === 'file'){

                    const formName = `model-field-get-file-content`
                    if(!app.clientState.forms.hasOwnProperty(formName)){
                        app.clientState.forms[formName] = {
                            state: 'idle',
                        }
                    }

                    if(app.clientState.forms[formName].state === 'idle'){
                        additional = {
                            block: ids.map(fileId => ({
                                button: {
                                    call: 'file_system.get_file_content',
                                    args: {file_id: fileId}
                                },
                                text: `⬇ ${fileId}`
                            }))
                        };
                    }else{
                        const resetButton = {
                            button: {
                                clientFunction: () => {
                                    app.clientState.forms[formName].state = 'idle';
                                    renderLingoApp(app, document.getElementById('lingo-app'), true)
                                }, 
                                args: {form: formName}
                            },
                            text: 'reset'
                        };
                        let indicator;
                        switch(app.clientState.forms[formName].state){
                            case 'loading':
                                indicator = {text: 'file downloading...', style: {italic: true}};
                                break;
                            case 'success':
                                indicator = {text: 'file downloaded', style: {color: 'green', bold: true}};
                                break;
                            default:
                                const errMsg = app.clientState.forms[formName].error || 'unknown error';
                                indicator = {text: `error downloading file: ${errMsg}`, style: {color: 'red', bold: true}};
                                break;
                        }
                        additional = {
                            block: [resetButton, indicator]
                        };
                    }

                }else if(table === 'image'){
                    additional = {
                        viewer: {image_ids: ids}
                    };
                }else if(table === 'master-image'){
                    additional = {
                        viewer: {master_image_ids: ids}
                    };
                }else{
                    additional = {
                        block: ids.flatMap((id, idx) => {
                            const loc = `${refModule}/${table}/${id}`;
                            const link = {link: `/${loc}`, text: `go to ${id}`};
                            // Add a separator after each link except the last
                            return idx < ids.length - 1 ? [link, {text: ' '}] : [link];
                        })
                    };
                }
            }else if(fieldDef.type === 'foreign_key'){
                const table = fieldDef.references.table.replaceAll('_', '-');
                const refModule = fieldDef.references.module.replaceAll('_', '-');
                const refField = fieldDef.references.field.replaceAll('_', '-');

                if(refField === 'id' && state.data[field] === '-1') {
                    additional = '-1 indicates no id was set'

                } else if (table === 'user' && refField === 'id') {
                    additional = 'the user that created this item';
                }else if(table === 'file' && refField === 'id'){

                    const formName = `model-field-get-file-content`

                    if(!app.clientState.forms.hasOwnProperty(formName)){
                        app.clientState.forms[formName] = {
                            state: 'idle',
                        }
                    }
                    console.log('renderModelRead - file field - formName:', formName);

                    if(app.clientState.forms[formName].state === 'idle'){
                        additional = {
                            button: { 
                                call: 'file_system.get_file_content',
                                args: {
                                    file_id: state.data[field]
                                }
                            },
                            text: 'download file'
                        }
                    }else{
                        // switch against loading, success, and default (for error)

                        switch(app.clientState.forms[formName].state){
                            case 'loading':
                                additional = {text: 'file downloading...', style: {italic: true}};
                                break;
                            case 'success':
                                additional = {text: 'file downloaded', style: {color: 'green', bold: true}};
                                break;
                            default:
                                const errMsg = app.clientState.forms[formName].error || 'unknown error';
                                additional = {text: errMsg, style: {color: 'red', bold: true}};
                                break;
                        }
                    }
                }else if((table === 'image') && refField === 'id'){
                    additional = {
                        viewer: {
                            image_id: state.data[field]
                        },
                    }
                }else if((table === 'master-image') && refField === 'id'){
                    additional = {
                        viewer: {
                            master_image_id: state.data[field]
                        },
                    }
                }else{
                    const loc = `${refModule}/${table}/${state.data[field]}`;
                    additional = {
                        link: `/${loc}`,
                        text: `go to ${loc}`
                    }
                }
            }else if(field === 'id'){
                additional = 'the unique identifier for this item';
            
            }else{
                additional = '';
            }


            convertedFields.push({
                type: 'struct',
                value: {
                    key: field,
                    value: state.data[field],
                    additional: additional
                }
            });
        }

        elements.push({
            type: 'list',
            display: {
                format: 'table',
                headers: [
                    {text: 'Key', field: 'key'},
                    {text: 'Value', field: 'value'},
                    {text: 'Additional', field: 'additional'}
                ]
            },
            value: convertedFields
        });
    }

    // trigger initial load //

    if (state.state === 'pending') {
        lingoExecute(app, loadScript);
    }

    return elements;
}

function _renderModelDelete(app, element, ctx = null) {
    // console.log('renderModelDelete()', app, element, ctx);
    if(!element.model.hasOwnProperty('bind')){
        throw new Error('renderModelDelete - missing model bind definition');
    }
    if(!element.model.bind.hasOwnProperty('state')){
        throw new Error('renderModelDelete - model bind definition must bind to state');
    }

    // get first (and only) field in bind.state
    const stateKeys = Object.keys(element.model.bind.state);
    if( stateKeys.length !== 1 ){
        throw new Error('renderModelDelete - model bind.state must have exactly one field');
    }

    const stateField = stateKeys[0];

    // ensure confirming_delete state exists
    if (!app.state.hasOwnProperty(stateField)) {
        throw new Error(`renderModelDelete - state field not found: ${stateField}`);
    }

    let state = app.state[stateField];

    if (!state.hasOwnProperty('state')) state.state = 'initial';
    if (!state.hasOwnProperty('error')) state.error = '';

    const switchElement = {
        switch: {
            expression: { type: 'str', value: state.state },
            cases: [
                {
                    case: 'confirming',
                    then: {
                        block: [
                            { text: ' Are you sure you want to delete this model instance? This action cannot be undone.' },
                            { break: 1 },
                            {
                                button: {
                                    set: {state: {[stateField]: {}}},
                                    to: {
                                        call: 'crud.delete',
                                        args: {
                                            http: { state: { base_url: {} } },
                                            model_id: { params: { model_id: {} } }
                                        }
                                    }
                                },
                                text: 'confirm delete'
                            },
                            { text: ' ' },
                            {
                                button: {
                                    set: {state: {[stateField]: {state: {}}}},
                                    to: 'initial'
                                },
                                text: 'cancel'
                            }
                        ]
                    }
                },
                {
                    case: 'deleted',
                    then: [
                        {text: 'item deleted successfully.', style: {color: 'green', bold: true}},
                    ]
                },
                {
                    case: 'error',
                    then: [
                        {text: 'error deleting item: ', style: {color: 'red', bold: true}},
                        {text: state.error}
                    ]
                }
            ],
            default: {
                button: {
                    set: { state: { [stateField]: { state: {} } } },
                    to: 'confirming'
                },
                text: 'delete'
            }
        }
    }

    return renderSwitch(app, switchElement, ctx);
}

function _renderModelList(app, element, ctx = null) {

    /*

    bind can be in these forms:
        * bind: { state: { myStateField: { }}}
        * bind: { clientState: { form: { myFormField: { }}}}

    */

    // selecting can be enabled to choose a model from the list,
    //     -1 means it is disabled,
    //      1 means it is enabled and single selection
    //      
    //      other numbers are reserved for future use (e.g. 2 for multi-selection, 0 for unlimited)
    const selecting = element.model.selecting || -1
    const onSelect = element.model.onSelect || null // onSelect is the callback that will be run when an item is selected
                                                    // it will be called with the selected item as the argument

    //
    // bind to state
    //

    if( !element.model.hasOwnProperty('bind')) {
        throw new Error('renderModelList - missing model bind definition');
    }

    let state;
    let setStatement;

    if (element.model.bind.hasOwnProperty('state')) {

         // get first (and only) field in bind.state
        const stateKeys = Object.keys(element.model.bind.state);
        if( stateKeys.length !== 1 ) {
            throw new Error('renderModelList - model bind.state must have exactly one field');
        }

        const stateField = stateKeys[0];

        state = app.state[stateField];

        setStatement = {state: {[stateField]: {}}};
        
    }else if( element.model.bind.hasOwnProperty('clientState')) {

        // if form not found in clientState, throw error
        if (!element.model.bind.clientState.hasOwnProperty('forms')) {
            throw new Error('renderModelList - model bind.clientState must have forms defined in clientState');
        }

        // get form name
        const formKeys = Object.keys(element.model.bind.clientState.forms);
        if (formKeys.length !== 1) {
            throw new Error('renderModelList - model bind.clientState must have exactly one form');
        }
        const formName = formKeys[0];

        const formStructKeys = Object.keys(element.model.bind.clientState.forms[formName]);
        if (formStructKeys.length === 0) {
            state = app.clientState.forms[formName];
            setStatement = {clientState: {forms: {[formName]: {}}}};
        } else if (formStructKeys.length === 1) {
            const formStructKeyName = formStructKeys[0];
            state = app.clientState.forms[formName][formStructKeyName];
            setStatement = {clientState: {forms: {[formName]: {[formStructKeyName]: {}}}}};
        }else{
            throw new Error('renderModelList - model bind.clientState form definition has too many nested levels. Only one level of nesting allowed after form name.');
        }
        
    }else{
        throw new Error('renderModelList - model bind definition must bind to state or clientState');
    }

   
    //
    // default state
    //

    if (!state.hasOwnProperty('items')) state.items = [];
    if (!state.hasOwnProperty('total')) state.total = 0;
    if (!state.hasOwnProperty('offset')) state.offset = 0;
    if (!state.hasOwnProperty('size')) state.size = 5;
    if (!state.hasOwnProperty('state')) state.state = "initial";
    if (!state.hasOwnProperty('error')) state.error = "";
    if (!state.hasOwnProperty('showing')) state.showing = 0;
    if (!state.hasOwnProperty('selected')) state.selected = []; // if we're selecting items, this will be a list of their ids

    const definition = lingoExecute(app, element.model.definition, ctx);

    let elements = [];

    //
    // pagination buttons
    //

    elements.push({
        text: 'prev',
        button: {
            set: setStatement,
            to: {
                call: 'crud.list', 
                args: {
                    http: element.model.http,
                    offset: state.offset - state.size,
                    size: state.size,
                    bind: element.model.bind
                }
            }
        },
        disabled: state.offset === 0
    });

    const loadScript = {
        set: setStatement,
        to: {
            call: 'crud.list', 
            args: {
                http: element.model.http,
                offset: state.offset,
                size: state.size,
                bind: element.model.bind
            }
        }
    };

    elements.push({
        text: 'load',
        button: loadScript
    });

    elements.push({
        text: 'next',
        button: {
            set: setStatement,
            to: {
                call: 'crud.list', 
                args: {
                    http: element.model.http,
                    offset: state.offset + state.size,
                    size: state.size,
                    bind: element.model.bind
                }
            }
        },
        disabled: {
            call: 'ge',
            args: {
                a: state.offset + state.size,
                b: state.total
            }
        }
    });

    // 
    // status display
    //

    elements.push(...[
        {break: 1},
        {text: 'showing: ', style: {bold: true}},
        {text: String(state.showing)},
        {text: ' of: ', style: {bold: true}},
        {text: String(state.total)},
        {text: ' offset: ', style: {bold: true}},
        {text: String(state.offset)},
        {text: ' size: ', style: {bold: true}},
        {text: String(state.size)},
        {text: ' status: ', style: {bold: true}},
    ]);

    const stateSwitch = {
        switch: {
            expression: { type: 'str', value: state.state },
            cases: [
                {
                    case: 'loading',
                    then: [
                        { text: 'Loading...', style: { italic: true } }
                    ]
                },
                {
                    case: 'error',
                    then: {
                        block: [
                            { text: 'Error: ', style: { color: 'red', bold: true } },
                            { text: state.error, style: { color: 'red', bold: false } }
                        ]
                    }
                },
                {
                    case: 'loaded',
                    then: [
                        { text: 'Loaded', style: { color: 'green', bold: true } }
                    ]
                }
            ],
            default: [
                { text: state.state, style: { italic: true } }
            ]
        }
    };

    elements.push(...renderSwitch(app, stateSwitch, ctx));

    //
    // table display
    //

    let headers = [{text: 'id', field: 'id'}];
    for (const [name, field] of Object.entries(definition.fields)) {
        headers.push({text: field.name.lower_case, field: field.name.snake_case});
    }

    // iterate over app.state[stateField].items and convert id to link

    let itemsForTable = [];
    
    if(element.model.hasOwnProperty('instance_url')) {
        const instanceUrl = unwrapValue(lingoExecute(app, element.model.instance_url, ctx));

        for (let item of state.items) {
            // console.log('renderModelList - pre processing:', item);

            let copyOfItem = JSON.parse(JSON.stringify(item));
            copyOfItem.value.id = {
                link: `${instanceUrl}${item.value.id}`,
                text: String(item.value.id)
            };
            itemsForTable.push(copyOfItem);

            // console.log('renderModelList - post processing:', copyOfItem);
        }
    }else{
        itemsForTable = state.items;
    }

    elements.push({
        type: 'list',
        display: {
            format: 'table',
            headers: headers,
            selecting: selecting,
            onSelect: onSelect
        },
        value: itemsForTable
    });

    if (state.state === 'pending') {
        // trigger initial load
        lingoExecute(app, loadScript);
    }

    return elements;
}

function _renderModelCreate(app, element, ctx = null) {
    
    //
    // init
    //

    if (!element.model.hasOwnProperty('definition')) {
        throw new Error('renderModelCreate - missing model definition');
    }

    const definition = lingoExecute(app, element.model.definition, ctx);

    if (!definition.fields || typeof definition.fields !== 'object') {
        throw new Error('renderModelCreate - invalid model definition fields');
    }

    if( !element.model.hasOwnProperty('bind')) {
        throw new Error('renderModelCreate - missing model bind definition');
    }

    if( !element.model.bind.hasOwnProperty('state')) {
        throw new Error('renderModelCreate - model bind definition must bind to state');
    }

    if (!element.model.hasOwnProperty('instance_url')) {
        throw new Error('renderModelCreate - missing instance_url definition');
    }

    const instanceUrl = unwrapValue(lingoExecute(app, element.model.instance_url, ctx));

    const stateKeys = Object.keys(element.model.bind.state);
    if( stateKeys.length !== 1 ) {
        throw new Error('renderModelCreate - model bind.state must have exactly one field');
    }

    const stateField = stateKeys[0];

    if (!app.state.hasOwnProperty(stateField)) {
        throw new Error(`renderModelCreate - state field not found: ${stateField}`);
    }

    const formElement = {
        form: {
            fields: definition.fields,
            bind: element.model.bind,
            action: {
                set: {state: {[stateField]: {}}},
                to: {
                    call: 'crud.create',
                    args: {
                        http: element.model.http,
                        bind: element.model.bind,
                        data: app.state[stateField].data
                    }
                }
            }
        }
    };

    const stateSwitch = {
        switch: {
            expression: { type: 'str', value: app.state[stateField].state },
            cases: [
                {
                    case: 'success',
                    then: {
                        block: [
                            { text: 'Success, ', style: { color: 'green', bold: true } },
                            { link: instanceUrl + app.state[stateField].item_id, text: 'view item' }
                        ]
                    }
                },
                {
                    case: 'error',
                    then: {
                        block: [
                            { text: 'Error: ', style: { color: 'red', bold: true } },
                            { text: app.state[stateField].error, style: { color: 'red', bold: true } }
                        ]
                    }
                },
                {
                    case: 'loading',
                    then: [
                        { text: 'Creating...', style: { italic: true } }
                    ]
                }
            ],
            default: {
                block: [{ text: 'ready', style: { italic: true } }]
            }
        }
    }

    let elements = [];
    elements.push(formElement);
    elements.push(...renderSwitch(app, stateSwitch, ctx));
    return elements;
}

function renderBreadcrumbs(app, element, ctx = null) {

    const crumbs = element.breadcrumbs;
    if (!Array.isArray(crumbs)) {
        throw new Error('breadcrumbs - breadcrumbs must be a list');
    }
    if (crumbs.length === 0 || crumbs.length > 4) {
        throw new Error('breadcrumbs - breadcrumbs list must have 1 to 4 items');
    }

    const elements = [{text: ':: '}];
    let url = '/';
    for (let i = 0; i < crumbs.length; i++) {
        const crumb = unwrapValue(lingoExecute(app, crumbs[i], ctx));
        if (i > 0) url += crumb;
        elements.push({link: url, text: crumb});
        if (i < crumbs.length - 1) {
            elements.push({text: ' :: '});
        }
        if (i > 0) url += '/';
    }

    // console.log('renderBreadcrumbs()', elements);

    return elements;

}

/**
 * DOM Rendering Functions
 */

/**
 * Render the LingoApp to a DOM container
 */
function renderLingoApp(app, container, preserveFocus = false) {
    // console.log('renderLingoApp()', app, container);

    // Store focused element info before re-rendering
    let focusedElement = null;
    let focusedElementState = null;
    
    if (preserveFocus) {
        focusedElement = document.activeElement;
        if (focusedElement && focusedElement.tagName === 'INPUT' && container.contains(focusedElement)) {
            // Store the state field this input is bound to
            const stateFieldName = focusedElement.getAttribute('data-state-field');
            if (stateFieldName) {
                focusedElementState = {
                    fieldName: stateFieldName,
                    selectionStart: focusedElement.selectionStart,
                    selectionEnd: focusedElement.selectionEnd
                };
            }
        }
    }

    // Clear container
    container.innerHTML = '';
    
    // Update state and render output
    if(app.spec.lingo.version == 'page-beta-1') {
        console.log('Rendering page-beta-1 spec');
        lingoUpdateState(app);
        const buffer = renderOutput(app);
        // console.log('Rendered buffer.length:', buffer.length);
        
        // Render each element in the buffer
        for (const element of buffer) {
            const domElement = createDOMElement(app, element);
            if (domElement) {
                container.appendChild(domElement);
            }
        }
    } else if(app.spec.lingo.version == 'script-beta-1') {
        console.log('Rendering script-beta-1 spec', app.spec.output);
        lingoUpdateState(app);
        const result = lingoExecute(app, app.spec.output);
        container.innerHTML = '<pre>' + JSON.stringify(result, null, 4) + '</pre>';

    }else{
        throw new Error(`Unsupported lingo version: ${app.spec.lingo.version}`);
    }
    
    // Restore focus if needed
    if (focusedElementState) {
        const newInputs = container.querySelectorAll(`input[data-state-field="${focusedElementState.fieldName}"]`);
        if (newInputs.length > 0) {
            const newInput = newInputs[0];
            newInput.focus();
            newInput.setSelectionRange(focusedElementState.selectionStart, focusedElementState.selectionEnd);
        }
    }

    // call afterRender callback if defined
    if (app.afterRender) {
        app.afterRender(app);
    }
}

/**
 * Create a DOM element from a buffer element
 */
function createDOMElement(app, element, ctx = null) {
    if ('heading' in element) {
        return createHeadingElement(app, element);
    } else if ('break' in element) {
        return createBreakElement(app, element);
    } else if ('button' in element) {
        return createButtonElement(app, element);
    } else if ('input' in element) {
        return createInputElement(app, element);
    } else if ('link' in element) {
        return createLinkElement(app, element);
    } else if ('text' in element) {
        return createTextElement(app, element);
    } else if ('value' in element) {
        return createValueElement(app, element);
    } else if ('form' in element) {
        return createFormElement(app, element);
    } else if ('viewer' in element) {
        return createViewerElement(app, element);
    } else if (Array.isArray(element)) {
        // If the element is an array, render each item and wrap in a div
        const container = document.createElement('div');
        for (const subElement of element) {
            // call createDomElement recursively for each subElement
            const childDom = createDOMElement(app, subElement, ctx);
            if (childDom) {
                container.appendChild(childDom);
            }
        }
        return container;

    } else {
        throw new Error('createDOMElement - unknown element type: ' + JSON.stringify(element));
    }
}

/**
 * Create heading element
 */
function createHeadingElement(app, element, ctx = null) {
    const level = element.level || 1;
    const heading = document.createElement(`h${level}`);
    heading.textContent = element.heading;
    return heading;
}

/**
 * Create text element
 */
function createTextElement(app, element, ctx = null) {
    // console.debug('createTextElement()', element);

    const span = document.createElement('span');
    span.textContent = element.text;
    
    // Apply styles if present
    if (element.style) {
        if (element.style.bold) {
            span.style.fontWeight = 'bold';
        }
        if (element.style.italic) {
            span.style.fontStyle = 'italic';
        }
        if (element.style.underline) {
            span.style.textDecoration = span.style.textDecoration 
                ? span.style.textDecoration + ' underline' 
                : 'underline';
        }
        if (element.style.strikethrough) {
            span.style.textDecoration = span.style.textDecoration 
                ? span.style.textDecoration + ' line-through' 
                : 'line-through';
        }
        if (element.style.color) {
            // Handle special color names that need conversion
            let color = element.style.color;
            if (color === 'dark_gray') {
                color = 'darkgray';
            } else if (color === 'light_gray') {
                color = 'lightgray';
            }
            span.style.color = color;
        }
    }
    
    return span;
}

/** Create value element
 */
function createValueElement(app, element, ctx = null) {

    // console.log('createValueElement()', element);

    if(element.type == 'struct') {
        // Render individual struct as a table
        const showHeaders = element.display && element.display.headers === false ? false : true;
        
        const table = document.createElement('table');
        
        // Add header row if needed
        if(showHeaders) {
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            
            const keyHeader = document.createElement('th');
            keyHeader.textContent = 'key';
            headerRow.appendChild(keyHeader);
            
            const valueHeader = document.createElement('th');
            valueHeader.textContent = 'value';
            headerRow.appendChild(valueHeader);
            
            thead.appendChild(headerRow);
            table.appendChild(thead);
        }
        
        // Add data rows
        const tbody = document.createElement('tbody');
        for(const [key, value] of Object.entries(element.value)) {
            const row = document.createElement('tr');
            
            const keyCell = document.createElement('td');
            keyCell.textContent = key;
            row.appendChild(keyCell);
            
            const valueCell = document.createElement('td');
            
            // Evaluate the value if it's an expression
            let cellValue = value;
            if(typeof value === 'object' && value !== null) {
                // It's either a typed value like {"type": "str", "value": "green"}
                // or a scripted expression like {"call": "add", "args": {...}}
                if('value' in value && 'type' in value) {
                    // Typed value
                    cellValue = value.value;
                } else if('call' in value || 'lingo' in value) {
                    // Scripted expression - need to evaluate it
                    try {
                        const result = lingoExecute(app, value);
                        if(typeof result === 'object' && result !== null && 'value' in result) {
                            cellValue = result.value;
                        } else {
                            cellValue = result;
                        }
                    } catch(error) {
                        console.error('Error evaluating struct field value:', error);
                        cellValue = '[Error]';
                    }
                }
            }
            
            // Format the cell value for display
            if(Array.isArray(cellValue)) {
                valueCell.innerHTML = cellValue.map(item => {
                        if(typeof item === 'object' && item !== null) {
                            return JSON.stringify(item, null, 4);
                        } else {
                            return String(item);
                        }
                    }).join('<br><br>');
                
            } else {
                valueCell.textContent = String(cellValue);
            }
            row.appendChild(valueCell);
            
            tbody.appendChild(row);
        }
        table.appendChild(tbody);
        
        return table;

    } else if(element.type == 'list') {
        const listFormat = (element.display && element.display.format) ? element.display.format : 'bullets';

        // Check if this is a table format list
        if(listFormat == 'table') {
            // Render list of structs as a table
            if(!element.display.headers && !element.display.columns) {
                throw new Error('createValueElement - table format list requires headers or columns definition');
            }
            if(element.display.hasOwnProperty('headers') && element.display.hasOwnProperty('columns')) {
                throw new Error('createValueElement - table format list cannot have both headers and columns definition');
            }

            /// init table

            const table = document.createElement('table');
            let columnNames = [];

            if(element.display.headers) {
            
                // Add header row
                const thead = document.createElement('thead');
                const headerRow = document.createElement('tr');
                
                for(const headerDef of element.display.headers) {
                    const th = document.createElement('th');
                    th.textContent = headerDef.text;
                    headerRow.appendChild(th);
                    columnNames.push(headerDef.field);
                }
                
                thead.appendChild(headerRow);
                table.appendChild(thead);
            }else{
                columnNames = element.display.columns;
            }
            
            // Add data rows
            const tbody = document.createElement('tbody');
            for(const item of element.value) {
                // Validate that item is a struct
                if(!item || item.type !== 'struct' || !item.value) {
                    throw new Error('createValueElement - table format list items must be structs');
                }
                
                const row = document.createElement('tr');
                if (element.display.selecting === 1) {
                    row.className = 'list-selecting';
                }

                if (element.display.onSelect) {
                    row.onclick = () => element.display.onSelect(item);
                }
                
                for(const columnName of columnNames) {
                    const td = document.createElement('td');
                    
                    const fieldValue = item.value[columnName];

                    // console.log('createValueElement - ', columnName, fieldValue, typeof fieldValue);
                    
                    // Evaluate the value if it's an expression
                    let cellValue = fieldValue;
                    if(typeof fieldValue === 'object' && fieldValue !== null) {
                        if('value' in fieldValue && 'type' in fieldValue) {
                            // Typed value
                            cellValue = fieldValue.value;
                        } else if('call' in fieldValue || 'lingo' in fieldValue || 'branch' in fieldValue) {
                            // Scripted expression - need to evaluate it
                            // console.log('createValueElement - evaluating scripted expression for table cell:', fieldValue);
                            try {
                                const result = lingoExecute(app, fieldValue);
                                // console.log('createValueElement - result of evaluating scripted expression for table cell:', result);
                                if(typeof result === 'object' && result !== null && 'value' in result) {
                                    cellValue = result.value;
                                } else {
                                    cellValue = result;
                                }
                            } catch(error) {
                                console.error('Error evaluating struct field value:', error);
                                cellValue = '[Error]';
                            }
                        }else if('link' in fieldValue){
                            cellValue = createLinkElement(app, fieldValue);
                        }else if('button' in fieldValue){
                            cellValue = createButtonElement(app, fieldValue);
                        }else if('text' in fieldValue){
                            cellValue = createTextElement(app, fieldValue);
                        }else if('block' in fieldValue){
                            let blockContainer = [];
                            for(const blockElement of fieldValue.block) {
                                const domElement = createDOMElement(app, blockElement);
                                if (domElement) {
                                    blockContainer.push(domElement);
                                }
                            }
                            //console.log('createValueElement - rendering block element in table cell:', fieldValue);
                            cellValue = blockContainer;
                        }else if('viewer' in fieldValue){
                            cellValue = createViewerElement(app, fieldValue);
                        }
                    }
                    
                    // Format the cell value for display
                    if(Array.isArray(cellValue)) {
                        // Format arrays as comma-separated values
                        //console.log('createValueElement - cellValue is array:', cellValue);

                        if (cellValue.every(item => item instanceof HTMLElement)) {
                            // td.appendChild for each item
                            cellValue.forEach(item => {
                                td.appendChild(item);
                            });
                        }else if (cellValue.every(item => typeof item === 'object' && item !== null)) {
                            cellValue.forEach(item => {
                                const domElement = createDOMElement(app, item);
                                td.appendChild(domElement);
                            });
                        } else {
                            console.log('createValueElement - cellValue is array but not all items are HTMLElements, converting to string:', cellValue);
                            td.textContent = cellValue.join(', ');
                        }
                    // else if is a Date object
                    } else if(cellValue instanceof Date) {
                        td.textContent = formatDateTime(cellValue);
                    } else if(cellValue instanceof HTMLElement) {
                        td.appendChild(cellValue);

                    // if is scripted expression, execute it
                    } else if(typeof cellValue === 'object' && cellValue !== null) {
                        // console.log('createValueElement - evaluating object value for table cell:', cellValue);
                        try {
                            const result = lingoExecute(app, cellValue);
                            // console.log('createValueElement - result of evaluating object value for table cell:', result);
                            if(typeof result === 'object' && result !== null) {
                                td.appendChild(createDOMElement(app, result));
                            } else {
                                td.textContent = String(result);
                            }
                        } catch(error) {
                            console.error('Error evaluating struct field value:', error);
                            td.textContent = '[Error]';
                        }

                    } else {
                        // console.log('createValueElement - converting cellValue to string:', cellValue);
                        td.textContent = String(cellValue);
                    }
                    row.appendChild(td);
                }
                
                tbody.appendChild(row);
            }
            table.appendChild(tbody);
            
            return table;
        }else if(listFormat == 'bullets' || listFormat == 'numbers') {

            let elementType;
            if(listFormat == 'bullets') {
                elementType = 'ul';
            } else if(listFormat == 'numbers') {
                elementType = 'ol';
            }else{
                throw new Error('createValueElement - unsupported list display format: ' + listFormat);
            }

            const container = document.createElement(elementType);
            for(const item of element.value) {
                const itemElement = createDOMElement({spec: {lingo: {version: 'page-beta-1'}}}, item);
                if(itemElement) {
                    const li = document.createElement('li');
                    li.appendChild(itemElement);
                    container.appendChild(li);
                }else{
                    throw new Error('createValueElement - failed to create DOM element for list item');
                }
            }
            return container;

        }else{
            throw new Error('createValueElement - unsupported list display format: ' + listFormat);
        }

    }else if(element.type == 'str' || element.type == 'int' || element.type == 'float' || element.type == 'bool') {
        const span = document.createElement('span');
        span.textContent = String(element.value);
        return span;
    }else{
        const span = document.createElement('span');
        span.textContent = JSON.stringify(element, null, 4);
        return span;
    }
}

/**
 * Create break element
 */
function createBreakElement(app, element, ctx = null) {
    const container = document.createElement('div');
    for (let i = 0; i < element.break; i++) {
        container.appendChild(document.createElement('br'));
    }
    return container;
}

/**
 * Create button element
 */
function createButtonElement(app, element, ctx) {
    const button = document.createElement('button');
    button.textContent = element.text;

    // console.log('createButtonElement()', typeof element.button, element);


    if (element.hasOwnProperty('disabled')) {
        const disabled = unwrapValue(lingoExecute(app, element.disabled, ctx));
        button.disabled = disabled;
    }

    let onClick;

    if (element.button.hasOwnProperty('clientFunction')) {
        onClick = () => element.button.clientFunction();
    } else if (element.button.hasOwnProperty('timer')) {
        const timerName = element.button.timer;
        onClick = () => {
            try {
                startTimer(app, timerName);
            } catch (error) {
                console.error('Button timer error:', error);
            }
        };
    } else{
        onClick = () => {
            try {
                lingoExecute(app, element.button, ctx);
                renderLingoApp(app, button.closest('.lingo-container'));
            } catch (error) {
                console.error('Button click error:', error);
            }
        };
    }
    
    button.onclick = onClick;
    return button;
}

/**
 * Create input element
 */
function createInputElement(app, element, ctx = null) {
    const input = document.createElement('input');
    input.type = element.input.type || 'text';
    
    // Get state field name
    try {
        const stateFieldName = Object.keys(element.bind.state)[0];
        const fieldType = app.spec.state[stateFieldName].type;
        
        // Store state field name as data attribute for focus restoration
        input.setAttribute('data-state-field', stateFieldName);
        
        // Set initial value
        input.value = app.state[stateFieldName] || '';
        
        // Handle input changes
        input.addEventListener('input', () => {
            try {
                let value = input.value;
                
                // Convert value based on field type
                if (fieldType === 'int') {
                    value = parseInt(value, 10) || 0;
                } else if (fieldType === 'float') {
                    value = parseFloat(value) || 0.0;
                } else if (fieldType === 'bool') {
                    value = Boolean(value);
                }
                
                app.state[stateFieldName] = value;
                renderLingoApp(app, input.closest('.lingo-container'), true);
            } catch (error) {
                console.error('Input change error:', error);
            }
        });
        
        return input;
    } catch (error) {
        console.error('Error creating input element:', error);
        return document.createTextNode('[Input Error]');
    }
}

/**
 * Create link element
 */
function createLinkElement(app, element, ctx = null) {
    const link = document.createElement('a');
    link.href = element.link;
    link.textContent = element.text || element.link;
    return link;
}

/**
 * Create form element with table layout
 */
function createFormElement(app, element, ctx = null) {

    // console.log('createFormElement()', app, element);

    // init //
    const formContainer = document.createElement('div');
    const table = document.createElement('table');
    table.className = 'form-table';

    if (!element.form.hasOwnProperty('fields')) {
        throw new Error('createFormElement - missing form fields definition');
    }
    if (!element.form.hasOwnProperty('bind')) {
        throw new Error('createFormElement - missing form bind definition');
        /* 
        in this future bind will support binding the form data to a state field
        but for now we use it as an id so we can track the form state between renders
        */
    }
    
    const fields = element.form.fields;
    const bind = element.form.bind;

    // form state //

    if (!bind.hasOwnProperty('state')) {
        throw new Error('createFormElement - bind must specify state field');
    }
    const stateKeys = Object.keys(bind.state);
    if (stateKeys.length !== 1) {
        throw new Error('createFormElement - bind.state must have exactly one field');
    }
    const formStateField = stateKeys[0];

    const formId = `form_${formStateField}`;

    if( !app.state.hasOwnProperty(formStateField) ) {
        throw new Error(`createFormElement - state field not found: ${formStateField}`);
    }
    const currentState = app.state[formStateField];
    const formData = currentState.data || {};
    // console.log('createFormElement - formData before:', formData); 
    
    // if element.form.auto_submit provided, execute and unwrap it, else set default false
    let autoSubmit;
    if (element.form.hasOwnProperty('auto_submit')) {
        autoSubmit = unwrapValue(lingoExecute(app, element.form.auto_submit, ctx));
    }else{
        autoSubmit = false;
    }

    // console.log('createFormElement - autoSubmit:', autoSubmit, element.form);
    
    // create a row for each field //

    for (const [fieldKey, fieldSpec] of Object.entries(fields)) {
        const row = document.createElement('tr');

        const formKeyId = `${formId}_${fieldKey}`;

        let ingestState;    // ingest state is for tracking file uploads
                            // or finding items for foreign_key fields
        if (app.clientState.forms.hasOwnProperty(formKeyId)) {
            console.log(`Found existing form state for ${formKeyId}:`, app.clientState.forms[formKeyId]);
            ingestState = app.clientState.forms[formKeyId];
        } else {
            ingestState = {status: 'idle', error: null, popup: null, showSecureFields: {}};
            app.clientState.forms[formKeyId] = ingestState;
        }

        // Column 1: Field name
        const nameCell = document.createElement('td');
        const fieldName = fieldSpec.name.lower_case;
        nameCell.textContent = fieldName + ':';
        row.appendChild(nameCell);

        // Column 2: Input element
        const inputCell = document.createElement('td');
        let inputElement;
        const fieldType = fieldSpec.type;
        const defaultValue = fieldSpec.default;

        // Only initialize from default if not already set
        if (typeof formData[fieldKey] === 'undefined') {
            if (fieldType === 'list') {
                formData[fieldKey] = Array.isArray(defaultValue) ? [...defaultValue] : [];
            } else {
                if (typeof defaultValue === 'undefined') {
                    // switch fieldtype to set sensible defaults
                    switch (fieldType) {
                        case 'bool':
                            formData[fieldKey] = false;
                            break;
                        case 'int':
                            formData[fieldKey] = 0;
                            break;
                        case 'float':
                            formData[fieldKey] = 0.0;
                            break;
                        case 'str':
                            formData[fieldKey] = '';
                            break;
                        case 'datetime':
                            formData[fieldKey] = new Date().toISOString();
                            break;
                        default:
                            formData[fieldKey] = null;
                    }
                }else{
                    formData[fieldKey] = defaultValue;
                }
            }
        }

        if (fieldType === 'list') {

            // List type - create input with add/remove functionality
            const listContainer = document.createElement('div');
            const elementType = fieldSpec.element_type;
            const hasEnum = fieldSpec.enum && Array.isArray(fieldSpec.enum);

            // Create list values display container (defined early so it can be referenced)
            const listValuesContainer = document.createElement('div');
            listValuesContainer.className = 'list-values-container';

            // Define update function first so it can be called from addToList
            const updateListDisplay = () => {
                listValuesContainer.innerHTML = '';

                if (formData[fieldKey].length === 0) {
                    const emptyText = document.createElement('span');
                    emptyText.textContent = '(no items)';
                    emptyText.className = 'list-empty-text';
                    listValuesContainer.appendChild(emptyText);

                } else {
                    const valuesList = document.createElement('div');
                    for (let i = 0; i < formData[fieldKey].length; i++) {
                        const itemContainer = document.createElement('div');
                        itemContainer.className = 'list-item-container';

                        const itemText = document.createElement('span');
                        itemText.textContent = String(formData[fieldKey][i]);
                        itemText.className = 'list-item-text';
                        itemContainer.appendChild(itemText);

                        const removeButton = document.createElement('button');
                        removeButton.textContent = 'X';
                        removeButton.type = 'button';
                        removeButton.className = 'remove-button';
                        removeButton.setAttribute('data-index', i);
                        removeButton.addEventListener('click', () => {
                            const index = parseInt(removeButton.getAttribute('data-index'));
                            formData[fieldKey].splice(index, 1);
                            updateListDisplay();
                        });

                        itemContainer.appendChild(removeButton);
                        valuesList.appendChild(itemContainer);
                    }
                    listValuesContainer.appendChild(valuesList);
                }
            };
            // Create input based on element type
            let listInput;
            const isListFK = (elementType === 'foreign_key');
            if (hasEnum) {
                listInput = document.createElement('select');
                for (const option of fieldSpec.enum) {
                    const opt = document.createElement('option');
                    opt.value = option;
                    opt.textContent = option;
                    listInput.appendChild(opt);
                }
            } else if (elementType === 'bool') {
                listInput = document.createElement('input');
                listInput.type = 'checkbox';
            } else if (elementType === 'int') {
                listInput = document.createElement('input');
                listInput.type = 'number';
                listInput.step = '1';
                listInput.placeholder = 'Enter integer';
            } else if (elementType === 'float') {
                listInput = document.createElement('input');
                listInput.type = 'number';
                listInput.step = 'any';
                listInput.placeholder = 'Enter number';
            } else if (elementType === 'datetime') {
                listInput = document.createElement('input');
                listInput.type = 'datetime-local';
            } else if (elementType === 'foreign_key') {
                const moduleRef = fieldSpec.references.module;
                const tableRef = fieldSpec.references.table;
                if (['file', 'image', 'master_image'].includes(tableRef)) {
                    listInput = document.createElement('input');
                    listInput.type = 'file';
                    const fileIngestStatus = document.createElement('span');
                    listInput.addEventListener('change', async () => {
                        const file = listInput.files[0];
                        if (!file) return;
                        fileIngestStatus.textContent = 'Uploading file...';
                        let ingestFunction;
                        switch (tableRef) {
                            case 'file': ingestFunction = fileSystemIngestStart; break;
                            case 'image': ingestFunction = mediaCreateImage; break;
                            case 'master_image': ingestFunction = mediaIngestMasterImage; break;
                            default: throw new Error(`Unsupported file type for FK list ingest: ${tableRef}`);
                        }
                        const ingestResult = await ingestFunction(file);
                        if (ingestResult.error) {
                            fileIngestStatus.textContent = `Upload failed: ${ingestResult.error}`;
                            console.error('FK list file ingest error:', ingestResult.error);
                        } else {

                            let id;
                            switch (tableRef) {
                                case 'file': id = ingestResult.result.file_id; break;
                                case 'image': id = ingestResult.result.image_id; break;
                                case 'master_image': id = ingestResult.result.master_image_id; break;
                                default: throw new Error(`Unsupported file type for FK list ingest: ${tableRef}`);
                            }
                            formData[fieldKey].push(id);
                            fileIngestStatus.textContent = 'File uploaded successfully!';
                            listInput.value = '';
                        }
                        renderLingoApp(app, document.getElementById('lingo-app'), true);
                    });
                    listContainer.appendChild(listInput);
                    listContainer.appendChild(fileIngestStatus);
                } else {
                    listInput = document.createElement('span');
                    if (app.parentSpec) {
                        const findButton = document.createElement('button');
                        findButton.textContent = `Find ${tableRef}`;
                        findButton.type = 'button';
                        findButton.addEventListener('click', () => {
                            ingestState.status = 'finding';
                            renderLingoApp(app, document.getElementById('lingo-app'), true);
                        });
                        listContainer.appendChild(findButton);
                    } else {
                        listContainer.textContent = `Can't browse for ${tableRef} items w/o model definition`;
                    }
                }
            } else {
                listInput = document.createElement('input');
                listInput.type = 'text';
                listInput.placeholder = 'Enter text';
            }

            if (!isListFK) {
                listInput.className = 'list-input';
                listContainer.appendChild(listInput);

                const addButton = document.createElement('button');
                addButton.textContent = 'Add';
                addButton.type = 'button';
                listContainer.appendChild(addButton);

                const addToList = () => {
                    let value;
                    if (hasEnum) {
                        value = listInput.value;
                    } else if (elementType === 'bool') {
                        value = listInput.checked;
                    } else if (elementType === 'int') {
                        value = parseInt(listInput.value, 10);
                        if (isNaN(value)) return;
                    } else if (elementType === 'float') {
                        value = parseFloat(listInput.value);
                        if (isNaN(value)) return;
                    } else if (elementType === 'datetime') {
                        if (!listInput.value) return;
                        value = listInput.value ? initDateTimeFromInput(listInput.value) : '';
                    } else {
                        value = listInput.value;
                        if (!value) return;
                    }
                    formData[fieldKey].push(value);
                    if (elementType === 'bool') {
                        listInput.checked = false;
                    } else if (!hasEnum) {
                        listInput.value = '';
                    }
                    console.log(`Add to list for field ${fieldKey}`, value, 'Current list:', formData[fieldKey]);
                    updateListDisplay();
                };
                addButton.addEventListener('click', addToList);
                if (listInput.tagName === 'INPUT' && (elementType === 'str' || elementType === 'int' || elementType === 'float')) {
                    listInput.addEventListener('keypress', (e) => {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            addToList();
                        }
                    });
                }
            }
            inputCell.appendChild(listContainer);
            inputElement = listContainer;
            inputElement._listValuesContainer = listValuesContainer;
            inputElement._updateListDisplay = updateListDisplay;

        } else if (fieldType === 'bool') {
            inputElement = document.createElement('input');
            inputElement.type = 'checkbox';
            inputElement.checked = !!formData[fieldKey];
            inputElement.addEventListener('change', () => {
                formData[fieldKey] = inputElement.checked;
            });

        } else if (fieldType === 'int') {
            inputElement = document.createElement('input');
            inputElement.type = 'number';
            inputElement.step = '1';
            inputElement.value = typeof formData[fieldKey] !== 'undefined' ? formData[fieldKey] : '';
            inputElement.addEventListener('input', () => {
                formData[fieldKey] = parseInt(inputElement.value, 10) || 0;
            });

        } else if (fieldType === 'float') {
            inputElement = document.createElement('input');
            inputElement.type = 'number';
            inputElement.step = 'any';
            inputElement.value = typeof formData[fieldKey] !== 'undefined' ? formData[fieldKey] : '';
            inputElement.addEventListener('input', () => {
                formData[fieldKey] = parseFloat(inputElement.value) || 0.0;
            });

        } else if (fieldType === 'datetime') {
            inputElement = document.createElement('input');
            inputElement.type = 'datetime-local';
            const datetimeValue = formData[fieldKey] ? String(formData[fieldKey]).substring(0, 16) : '';
            inputElement.value = datetimeValue;
            inputElement.addEventListener('input', () => {
                formData[fieldKey] = inputElement.value ? initDateTimeFromInput(inputElement.value) : '';
            });

        } else if (fieldType === 'foreign_key') {
            inputElement = document.createElement('input');
            inputElement.type = 'text';

            const module = fieldSpec.references.module;
            const table = fieldSpec.references.table;

            if(table === 'user') {
                inputElement.placeholder = 'Will be set automatically';
                inputElement.disabled = true;
                inputElement.value = '';
            }else {
                inputElement.placeholder = `Enter ${module}.${table} ID`;
                inputElement.value = typeof formData[fieldKey] !== 'undefined' ? formData[fieldKey] : '';
                inputElement.addEventListener('input', () => {
                    formData[fieldKey] = inputElement.value;
                });

                if (ingestState.status !== 'idle') {
                    inputElement.disabled = true;
                }
            }

        } else if (fieldSpec.enum) {
            inputElement = document.createElement('select');
            inputElement.name = fieldKey;
            for (const option of fieldSpec.enum) {
                const opt = document.createElement('option');
                opt.value = option;
                opt.textContent = option;
                opt.selected = option === formData[fieldKey];
                inputElement.appendChild(opt);
            }
            inputElement.addEventListener('change', () => {
                formData[fieldKey] = inputElement.value;
            });

        } else {
            inputElement = document.createElement('input');
            if(fieldSpec.secure || fieldSpec.secure_input) {
                if(ingestState.showSecureFields[fieldKey] === undefined) {
                    ingestState.showSecureFields[fieldKey] = false;
                }
                if(ingestState.showSecureFields[fieldKey] === true) {
                    inputElement.type = 'text';
                } else {
                    inputElement.type = 'password';
                }
            }else{
                inputElement.type = 'text';
            }
            inputElement.value = typeof formData[fieldKey] !== 'undefined' ? formData[fieldKey] : '';
            inputElement.addEventListener('input', () => {
                formData[fieldKey] = inputElement.value;
            });
        }
        inputCell.appendChild(inputElement);
        row.appendChild(inputCell);
        
        // Column 3: List values display (for list types) or Description
        const thirdCell = document.createElement('td');
        
        if (fieldType === 'list') {
            // Use the display container created earlier
            const listValuesContainer = inputElement._listValuesContainer;
            const updateListDisplay = inputElement._updateListDisplay;
            
            // Initialize display
            updateListDisplay();
            
            thirdCell.appendChild(listValuesContainer);

            // Popup for non-file FK list types
            if (fieldSpec.element_type === 'foreign_key' && !['file', 'image', 'master_image'].includes(fieldSpec.references.table)) {
                const moduleRef = fieldSpec.references.module;
                const tableRef = fieldSpec.references.table;
                if (ingestState.status === 'finding' && app.parentSpec) {
                    if (ingestState.popup === null) {
                        ingestState.popup = {
                            items: [],
                            total: 0,
                            offset: 0,
                            size: 10,
                            state: 'pending',
                            errors: ''
                        };
                    }

                    const closePopupFunction = () => {
                        ingestState.status = 'idle';
                        renderLingoApp(app, document.getElementById('lingo-app'), true);
                    };

                    const background = document.createElement('div');
                    background.className = 'popup-background';
                    background.onclick = closePopupFunction;

                    const popUpContentContainer = document.createElement('div');
                    popUpContentContainer.className = 'popup-content';

                    const popupModelSpec = app.parentSpec.modules[moduleRef].models[tableRef];

                    const onPopupSelect = (item) => {
                        console.log('Selected item from popup for FK list:', item);
                        formData[fieldKey].push(item.value.id);
                        ingestState.status = 'idle';
                        renderLingoApp(app, document.getElementById('lingo-app'), true);
                    };

                    const popupModelList = {model: {
                        bind: { clientState: { forms: { [formKeyId]: {popup: {}} } } },
                        display: 'list',
                        http: `/api/${moduleRef}/${tableRef}`.replaceAll('_', '-'),
                        definition: popupModelSpec,
                        selecting: 1,
                        onSelect: onPopupSelect
                    }};

                    const popupModelElements = renderModel(app, popupModelList);

                    popupModelElements.forEach(el => {
                        const domElement = createDOMElement(app, el);
                        domElement.style.zIndex = 101;
                        popUpContentContainer.appendChild(domElement);
                    });
                    thirdCell.appendChild(background);
                    thirdCell.appendChild(popUpContentContainer);
                }
            }
        } else if (fieldType == 'foreign_key') {
            const moduleRef = fieldSpec.references.module;
            const tableRef = fieldSpec.references.table;
            if(tableRef === 'user') {
                thirdCell.textContent = 'Your user id';
            }else if(['file', 'image', 'master_image'].includes(tableRef)) {
                // add file chooser to thirdCell

                let fileIngestStatus = document.createElement('span');
                
                // file input //
                const fileInput = document.createElement('input');
                fileInput.type = 'file';
                fileInput.addEventListener('change', async () => {
                    const file = fileInput.files[0];
                    if (file) {
                        ingestState.status = 'uploading';
                        fileIngestStatus.textContent = 'Uploading file...';
                        
                        let ingestFunction;
                        switch (tableRef) {
                            case 'file':
                                ingestFunction = fileSystemIngestStart;
                                break;
                            case 'image':
                                ingestFunction = mediaCreateImage;
                                break;
                            case 'master_image':
                                ingestFunction = mediaIngestMasterImage;
                                break;
                            default:
                                throw new Error(`Unsupported file type for ingest: ${tableRef}`);
                        }

                        const ingestResult = await ingestFunction(file);
                        if (ingestResult.error) {
                            ingestState.status = 'error';
                            ingestState.error = ingestResult.error;

                            fileIngestStatus.textContent = ingestResult.error;
                            console.error('File ingest error:', ingestResult.error);
                        } else {
                            ingestState.status = 'success';
                            ingestState.error = null;

                            switch(tableRef) {
                                case 'file':
                                    formData[fieldKey] = ingestResult.result.file_id;
                                    break;
                                case 'image':
                                    formData[fieldKey] = ingestResult.result.image_id;
                                    break;
                                case 'master_image':
                                    formData[fieldKey] = ingestResult.result.master_image_id;
                                    break;
                                default:
                                    throw new Error(`Unsupported file type for setting formData: ${tableRef}`);
                            }

                            fileIngestStatus.textContent = 'File uploaded successfully!';
                        }
                        
                        renderLingoApp(app, fileInput.closest('.lingo-container'), true);
                    }
                });

                // status display //
                const resetStateButton = document.createElement('button');
                resetStateButton.textContent = 'Reset';
                resetStateButton.type = 'button';
                resetStateButton.className = 'reset-button';
                resetStateButton.addEventListener('click', () => {
                    console.log('Resetting ingest state for field', fieldKey, ingestState);
                    ingestState.status = 'idle';
                    ingestState.error = null;
                    renderLingoApp(app, document.getElementById('lingo-app'), true);
                });

                if(ingestState.status === 'uploading') {
                    thirdCell.appendChild(resetStateButton);
                    fileIngestStatus.textContent = 'Uploading file...';
                }else if(ingestState.status === 'error') {
                    thirdCell.appendChild(resetStateButton);
                    fileIngestStatus.textContent = ingestState.error;
                }else if(ingestState.status === 'success') {
                    thirdCell.appendChild(resetStateButton);
                    fileIngestStatus.textContent = 'File uploaded successfully!';
                }else{
                    fileIngestStatus.textContent = '';
                    thirdCell.appendChild(fileInput);
                }

                thirdCell.appendChild(fileIngestStatus);

            }else{

                // find item for foreign key reference //

                if(ingestState.status === 'finding') {

                    if (ingestState.popup === null) {
                        ingestState.popup = {
                            items: [],
                            total: 0,
                            offset: 0,
                            size: 10,
                            state: 'pending',
                            errors: ''
                        };
                    }

                    const closePopupFunction = () => {
                        ingestState.status = 'idle';
                        renderLingoApp(app, document.getElementById('lingo-app'), true);
                    }

                    const background = document.createElement('div');
                    background.className = 'popup-background';
                    background.onclick = closePopupFunction;

                    const popUpContentContainer = document.createElement('div');
                    popUpContentContainer.className = 'popup-content';

                    const popupModelSpec = app.parentSpec.modules[moduleRef].models[tableRef]

                    const onPopupSelect = (item) => {
                        console.log('Selected item from popup:', item);
                        formData[fieldKey] = item.value.id;
                        ingestState.status = 'idle';
                        renderLingoApp(app, document.getElementById('lingo-app'), true);
                    }

                    const popupModelList = {model: {
                        bind: { clientState: { forms: { [formKeyId]: {popup: {}} } } },
                        display: 'list',
                        http: `/api/${moduleRef}/${tableRef}`.replaceAll('_', '-'),
                        definition: popupModelSpec,
                        selecting: 1,
                        onSelect: onPopupSelect
                    }};

                    const popupModelElements = renderModel(app, popupModelList)

                    popupModelElements.forEach(el => {
                        const domElement = createDOMElement(app, el);
                        domElement.style.zIndex = 101;
                        popUpContentContainer.appendChild(domElement);
                    });
                    thirdCell.appendChild(background);
                    thirdCell.appendChild(popUpContentContainer);

                }else{
                    if(app.parentSpec) {
                        const findItemButton = createButtonElement(app, {
                            button: {
                                clientFunction: () => {
                                    console.log(`Find item button clicked for ${moduleRef}.${tableRef}`);
                                    ingestState.status = 'finding';
                                    renderLingoApp(app, document.getElementById('lingo-app'), true);
                                }
                            }
                        });
                        findItemButton.textContent = `Find ${tableRef}`;
                        thirdCell.appendChild(findItemButton);
                    }else{
                        // this feature requiers that the page spec define a parent spec
                        // which is used to look of the model definition for the browsing table
                        thirdCell.textContent = `Can't browse for ${tableRef} items w/o model definition`;
                    }
                }
            }
        
        }else if(fieldSpec.secure || fieldSpec.secure_input) {
            const toggleSecureFieldButton = document.createElement('button');
                toggleSecureFieldButton.type = 'button';
                toggleSecureFieldButton.textContent = ingestState.showSecureFields[fieldKey] ? 'hide' : 'show';
                toggleSecureFieldButton.addEventListener('click', () => {
                    ingestState.showSecureFields[fieldKey] = !ingestState.showSecureFields[fieldKey];
                    renderLingoApp(app, document.getElementById('lingo-app'), true);
                });
                thirdCell.appendChild(toggleSecureFieldButton);
        } else {
            // Description for non-list fields
            thirdCell.className = 'form-description';
            thirdCell.textContent = fieldSpec.description || '';
        }
        
        row.appendChild(thirdCell);
        table.appendChild(row);
    }

     // submit action

    const submitAction = () => {
        // console.log('Submitting form with data:', formData);
        const result = lingoExecute(app, element.form.action, {});
        // console.log('Form submission result:', result);
        renderLingoApp(app, document.getElementById('lingo-app'));
    };

    if (autoSubmit === true && currentState.state === 'initial') {
        setTimeout(() => {
            // console.log('Auto-submitting form on initial render');
            currentState.state = 'loading';
            submitAction();
            renderLingoApp(app, document.getElementById('lingo-app'), true);
        }, 0);
    }
    
    // submit button //

    const submitButtonText = element.form.submit_button_text || 'Submit';
    const submitButton = document.createElement('button');
    submitButton.disabled = currentState.state === 'loading';
    submitButton.textContent = submitButtonText;
    submitButton.addEventListener('click', submitAction);

    // status display //
    let stateColor;
    switch(currentState.state) {
        case 'success':
            stateColor = 'green';
            break;
        case 'error':
            stateColor = 'red';
            break;
        default:
            stateColor = 'blue';
    }

    const statusDisplay = {text: currentState.state, style: {bold: true, color: stateColor}};
    const statusElement = createTextElement(app, statusDisplay, ctx);
    
    // additional comment //

    let commentText;
    if (element.hasOwnProperty('comment')) {
        commentText = element.comment;
    } else if (currentState.state === 'error') {
        commentText = {text: currentState.error || 'An error occurred', style: {italic: true, color: 'red'}};
    }else{
        commentText = {text: ''}
    }

    let additionalElement;
    try{
        additionalElement = createTextElement(app, commentText, ctx);
    }catch(error) {
        console.error('Error creating additionalElement for form comment:', error);
        throw `Error creating form comment element must be a text element: ${error}`;
    }

    // final assembly //
    // console.log('createFormElement - adding button', {autoSubmit, currentState: currentState.state});
    const submitRow = document.createElement('tr');
    submitRow.className = 'form-submit-row';
    const buttonCell = document.createElement('td');
    // buttonCell.colSpan = 3;
    // buttonCell.className = 'form-submit-cell';
    buttonCell.appendChild(submitButton);

    const statusCell = document.createElement('td');
    statusCell.appendChild(statusElement);
    
    const additionalCell = document.createElement('td');
    additionalCell.appendChild(additionalElement);

    submitRow.appendChild(buttonCell);
    submitRow.appendChild(statusCell);
    submitRow.appendChild(additionalCell);

    table.appendChild(submitRow);
    formContainer.appendChild(table);

    // console.log('createFormElement - formData after:', formData);
    return formContainer;
}

function createViewerElement(app, element, ctx = null) {

    // console.log('createViewerElement', element);

    // init


    let isGallery;
    let mediaType;
    let galleryIds;
    let mediaId;
    let mediaFileContentReqBody;

    if (element.viewer.hasOwnProperty('image_ids')) {
        // if (element.viewer.image_ids.length === 0) {
        //     throw new Error('createViewerElement - image_ids must not be empty');
        // }
        isGallery = true;
        mediaType = 'image';
        galleryIds = element.viewer.image_ids;
        // mediaId and mediaFileContentReqBody set after galleryState is initialized below
    } else if (element.viewer.hasOwnProperty('image_id')) {
        mediaType = 'image';
        mediaId = element.viewer.image_id;
        mediaFileContentReqBody = {image_id: mediaId};
    } else if (element.viewer.hasOwnProperty('master_image_ids')) {
        // if (element.viewer.master_image_ids.length === 0) {
        //     throw new Error('createViewerElement - master_image_ids must not be empty');
        // }
        isGallery = true;
        mediaType = 'master_image';
        galleryIds = element.viewer.master_image_ids;
        // mediaId and mediaFileContentReqBody set after galleryState is initialized below

    } else if (element.viewer.hasOwnProperty('master_image_id')) {
        mediaType = 'master_image';
        mediaId = element.viewer.master_image_id;
        mediaFileContentReqBody = {master_image_id: mediaId};
    } else {
        throw new Error('createViewerElement - missing viewer image_id, image_ids, or master_image_id');
    }

    const height = element.viewer.height || 100;
    const width = element.viewer.width || 275;

    // init gallery state (gallery mode only)

    let galleryState = null;
    if (isGallery) {
        const galleryKey = `gallery_${galleryIds.join('_')}`;
        if (!app.clientState.media.hasOwnProperty(galleryKey)) {
            app.clientState.media[galleryKey] = {
                galleryIndex: 0,
                insetZoom: 1,
                poppedUp: false,
                displayOriginalSize: false
            };
        }
        galleryState = app.clientState.media[galleryKey];
        mediaId = galleryIds[galleryState.galleryIndex];
        mediaFileContentReqBody = mediaType === 'image' ? {image_id: mediaId} : {master_image_id: mediaId};
    }

    // init per-image client state

    const stateKey = `${mediaType}_${mediaId}`;

    if(!app.clientState.media.hasOwnProperty(stateKey)) {
        app.clientState.media[stateKey] = {
            status: (isGallery && galleryIds.length === 0) ? 'empty-gallery' : 'pending', 
            error: null,
            localUrl: null,
            fileId: null,
            fileName: null,
            insetZoom: 1,
            poppedUp: false,
            displayOriginalSize: false
        };
    }
    const mediaState = app.clientState.media[stateKey];

    // viewer state: gallery mode uses galleryState for zoom/popup/index; single mode uses mediaState
    const viewerState = isGallery ? galleryState : mediaState;

    // function to fetch media

    async function getMediaFileContent() {
        console.log('Fetching media content for media type:', mediaType, 'media ID:', mediaId);
        try {
            const response = await fetch('/api/media/get-media-file-content', {
                method: 'POST',
                headers: getRequestHeaders(),
                body: JSON.stringify(mediaFileContentReqBody)
            });

            if (response.ok) {
                console.log('Media content fetched successfully for media type:', mediaType, 'media ID:', mediaId);
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                mediaState.status = 'loaded';
                mediaState.error = null;
                mediaState.localUrl = url;

            } else {
                const errorData = await response.json();
                mediaState.status = 'error';
                mediaState.error = errorData.error || 'Failed to load image';
                console.error('Error response from get-media-file-content:', errorData);
            }

        } catch (error) {
            mediaState.status = 'error';
            mediaState.error = error.message || 'Failed to load image';
            console.error('Network error while fetching image:', error);
            return null;
        } finally {
            renderLingoApp(app, document.getElementById('lingo-app'), true);
        }
    }

    // 
    // download button
    //

    const localFileName = `${mediaType}_${mediaId}`;
    let downloadButton;
    if(mediaState.status === 'loaded') {
        // source is loaded, this download button will trigger
        // a download using the local source URL without needing to re-fetch from the server
        console.log('media loaded')
        downloadButton = createButtonElement(app, {
            button: {
                clientFunction: () => {
                    // using mediaState.localUrl, download the file
                    const link = document.createElement('a');
                    link.href = mediaState.localUrl;
                    link.download = localFileName;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }
            },
            text: '⬇'
        });

    }else{
        // used to re-trigger download if there is an error,
        // or placeholder button while loading
        downloadButton = createButtonElement(app, {
            button: {
                call: 'media.get_media_file_content',
                args: mediaFileContentReqBody
            },
            disabled: mediaState.status !== 'error',
            text: mediaState.status === 'error' ? '↻' : '⬇'
        }, {self: {file_output: mediaState}});
    }

    const closePopupFunction = () => {
        viewerState.poppedUp = !viewerState.poppedUp;
        viewerState.insetZoom = 1;
        viewerState.displayOriginalSize = false;
        renderLingoApp(app, document.getElementById('lingo-app'), true);
    };

    //
    // pop up
    //

    const background = document.createElement('div');
    background.className = 'popup-background';
    background.onclick = closePopupFunction;

    //
    // view contol buttons
    //

    const zoomIncrement = 0.25;
    const zoomMin = (viewerState.poppedUp) ? 0.05 : 1;
    const zoomMax = (viewerState.poppedUp) ? 5 : 3.5

    const zoomInButton = createButtonElement(app, {
        button: {
            clientFunction: () => {
                viewerState.insetZoom = Math.min(zoomMax, viewerState.insetZoom + zoomIncrement);
                renderLingoApp(app, document.getElementById('lingo-app'), true);
            }
        },
        text: '✚',
        disabled: (mediaState.status !== 'loaded' || viewerState.insetZoom >= zoomMax) || viewerState.displayOriginalSize
    });

    // zoom out 
    const zoomOutButton = createButtonElement(app, {
        button: {
            clientFunction: () => {
                viewerState.insetZoom = Math.max(zoomMin, viewerState.insetZoom - zoomIncrement);
                renderLingoApp(app, document.getElementById('lingo-app'), true);
            }
        },
        text: '—',
        disabled: mediaState.status !== 'loaded' || viewerState.insetZoom <= zoomMin || viewerState.displayOriginalSize
    });

    // pop up buttom
    const popUpButton = createButtonElement(app, {
        button: {
            clientFunction: closePopupFunction
        },
        text: (viewerState.poppedUp) ? '×' : '⌞ ⌝',
        disabled: mediaState.status !== 'loaded'
    });

    // original size buttom
    const originalSizeButton = createButtonElement(app, {
        button: {
            clientFunction: () => {
                viewerState.displayOriginalSize = !viewerState.displayOriginalSize;
                renderLingoApp(app, document.getElementById('lingo-app'), true);
            }
        },
        text: viewerState.displayOriginalSize ? 'scaled' : 'original size',
        disabled: mediaState.status !== 'loaded'
    });

    //
    // gallery navigation buttons (gallery mode only)
    //

    let prevButton = null;
    let nextButton = null;
    let galleryIndicator = null;

    if (isGallery) {
        const imageCount = galleryIds.length;

        prevButton = createButtonElement(app, {
            button: {
                clientFunction: () => {
                    galleryState.galleryIndex = Math.max(0, galleryState.galleryIndex - 1);
                    renderLingoApp(app, document.getElementById('lingo-app'), true);
                }
            },
            text: '◀',
            disabled: galleryState.galleryIndex <= 0
        });

        nextButton = createButtonElement(app, {
            button: {
                clientFunction: () => {
                    galleryState.galleryIndex = Math.min(imageCount - 1, galleryState.galleryIndex + 1);
                    renderLingoApp(app, document.getElementById('lingo-app'), true);
                }
            },
            text: '▶',
            disabled: galleryState.galleryIndex >= imageCount - 1
        });

        galleryIndicator = document.createElement('span');
        const galleryIndexDisplay = (galleryIds.length > 0) ? `${galleryState.galleryIndex + 1}` : '0';
        galleryIndicator.textContent = `${galleryIndexDisplay} / ${imageCount}`;
        galleryIndicator.style.margin = '0 4px';
        galleryIndicator.style.fontWeight = 'bold';
        galleryIndicator.style.padding = '2px 4px';
        galleryIndicator.style.backgroundColor = 'rgba(255, 255, 255, 1.0)';
    }

    //
    // img
    //

    const img = document.createElement('img');
    img.style.zIndex = '100';

    switch (mediaState.status) {

        case 'pending': 
            getMediaFileContent();
             // fall through to loading state
        case 'loading':
            img.src = placeholderImage(width, height, 'Loading...').src;
            break;

        case 'loaded':
            // loading and pending
            img.src = mediaState.localUrl;
            break;

        case 'empty-gallery':
            img.src = placeholderImage(width, height, 'No pics in gallery').src;
            break;

        case 'error':
            img.src = placeholderImage(width, height, 'Error').src;
            break;

        default:
            throw new Error('Invalid media state: ' + mediaState.status);
    }

    img.style.display = 'block';

    if(viewerState.poppedUp) {
        img.style.position = 'fixed';
        img.style.top = '5%';
        if(viewerState.displayOriginalSize) {
            img.style.width = `${img.naturalWidth}px`
            img.style.height = `${img.naturalHeight}px`
    
            // calculate left to center the image
            const windowX = window.innerWidth;
            const left = (windowX - img.naturalWidth) / 2;
            img.style.left = `${left}px`;
            console.log(`Original size - window width: ${windowX}, image width: ${img.naturalWidth}, left: ${left}`);
        }else{
            const windowX = window.innerWidth;
            const baseX = (.75 * windowX);
            const zoomedValue = baseX * viewerState.insetZoom;
            img.style.left = `${(windowX - zoomedValue) / 2}px`;
            img.style.width = `${zoomedValue}px`;
        }
    }else{
        img.style.maxWidth = '100%';
        img.style.height = 'auto';
        img.style.margin = '0 auto';
    }

    //
    // container div
    //

    const zoomedWidth = width * viewerState.insetZoom;

    const div = document.createElement('div');
    div.style.zIndex = '101';
    div.className = 'viewer-container';
    div.style.width = `${zoomedWidth}px`;

    const controlsDiv = document.createElement('div');
    controlsDiv.style.zIndex = '102';
    controlsDiv.className = 'viewer-controls';

    if (isGallery) {
        controlsDiv.appendChild(prevButton);
        controlsDiv.appendChild(galleryIndicator);
        controlsDiv.appendChild(nextButton);
    }

    controlsDiv.appendChild(downloadButton);
    controlsDiv.appendChild(zoomOutButton);
    controlsDiv.appendChild(zoomInButton);
    controlsDiv.appendChild(popUpButton);

    if(viewerState.poppedUp) {
        div.appendChild(background);
        controlsDiv.appendChild(originalSizeButton);
        controlsDiv.style.position = 'fixed';
        controlsDiv.style.top = '10px';
        controlsDiv.style.left = '50%';
        controlsDiv.style.transform = 'translateX(-50%)';

        // img.style.position = 'fixed';
        // img.style.top = '50%';
        // img.style.left = '50%';
        // img.style.transform = 'translate(-50%, -50%)';
        // img.style.zIndex = '100';

    }else if(mediaState.status === 'loaded') {
        img.style.cursor = 'pointer';
        img.onclick = () => {
            viewerState.poppedUp = true;
            renderLingoApp(app, document.getElementById('lingo-app'), true);
        }
    }

    div.appendChild(controlsDiv);
    div.appendChild(img);

    return div;
}