/**
 * JavaScript implementation of the mspec markup language renderer
 * This is equivalent to the Python markup.py module
 */

// Date/time formatting
const datetimeFormatStr = '%Y-%m-%dT%H:%M:%S';

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

//
// lingo functions
//


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
    'neg': {
        func: (obj) => -obj,
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
        func: (iterable) => [...iterable].sort((a, b) => a - b),
        args: {'iterable': {'type': 'list'}}
    },
    
    // sequence ops //
    
    'map': {
        func: null, // handled specially in renderCall
        createArgs: true
    },
    'filter': {
        func: null, // handled specially in renderCall
        createArgs: true
    },
    'dropwhile': {
        func: null, // handled specially in renderCall
        createArgs: true
    },
    'takewhile': {
        func: null, // handled specially in renderCall
        createArgs: true
    },
    'reversed': {
        func: (sequence) => [...sequence].reverse(),
        args: {'sequence': {'type': 'list'}}
    },
    'accumulate': {
        func: null, // handled specially in renderCall
        createArgs: true
    },
    'reduce': {
        func: null, // handled specially in renderCall
        createArgs: true
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

    // crud //

    'crud': {
        'create': {
            func: null, // handled specially in renderCall
            createArgs: true
        },
        'read': {
            func: null, // handled specially in renderCall
            createArgs: true
        },
        'update': {
            func: null, // handled specially in renderCall
            createArgs: true
        },
        'delete': {
            func: null, // handled specially in renderCall
            createArgs: true
        },
        'list': {
            func: null, // handled specially in renderCall
            createArgs: true
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
    
    return lingoUpdateState(instance);
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
            
            if (actualType !== value.type) {
                throw new Error(`state.${key} - expression returned type: ${actualType}, expected: ${value.type}`);
            }
            app.state[key] = actualValue;
        } else {
            // Non-calculated value, set to default if not already set
            if (!(key in app.state)) {
                if (!('default' in value)) {
                    throw new Error(`state.${key} - missing default value`);
                }
                const typeName = getTypeName(value.default);
                if (typeName !== value.type) {
                    throw new Error(`state.${key} - default value type mismatch : ${typeName} != ${value.type}`);
                }
                app.state[key] = value.default;
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
 * Get JavaScript type name in Python-compatible format
 */
function getTypeName(value) {
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
    if (typeof value === 'object') return 'struct';
    return typeof value;
}

function unwrapValue(data) {
    if (typeof data === 'object' && data !== null && 'value' in data && 'type' in data) {
        return data.value;
    }else{
        return data;
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
    // console.log('* * * renderOutput()', typeof app.spec.output, app.spec.output.length);
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
                        console.error('Rendered output item is not an object:', typeof item, element, rendered, item);
                        throw new Error(`Rendered output item is not an object: ${typeof item} - output ${n}`);
                    }
                }
            } else {
                throw new Error(`Rendered output is not an object or array: ${typeof rendered} - output ${n}`);
            }
        } catch (error) {
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
    console.log('renderBlock()', element);
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
                    return lingoExecute(app, then, ctx);
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
    console.log('renderSet()', app, expression);
    try {

        // init

        const target = expression.set.state;
        const valueExpr = expression.to;
        
        // get state field

        const fieldNames = Object.keys(target);
        if (fieldNames.length !== 1) {
            throw new Error('set - must have exactly one state field');
        }
        const fieldName = fieldNames[0];

        if(!app.spec.state.hasOwnProperty(fieldName)){
            throw new Error(`set - state field not found: ${fieldName}`);
        }

        // if is a struct, get struct field name
        
        const fieldType = app.spec.state[fieldName].type;

        let value = lingoExecute(app, valueExpr, ctx);

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

                    if (!(structFieldName in app.state[fieldName])) {
                        throw new Error(`set - struct field not found: ${fieldName}.${structFieldName}`);
                    }

                    const origStructValue = app.state[fieldName][structFieldName];

                    // verify type of outValue matches type of origStructValue
                    const newStructType = getTypeName(origStructValue);
                    const outValueType = getTypeName(outValue);
                    if (outValueType !== newStructType) {
                        throw new Error(`set - type mismatch: ${newStructType} != ${outValueType} - field: ${fieldName}.${structFieldName}`);
                    }

                    app.state[fieldName][structFieldName] = outValue;

                    // console.log(`set - setting struct field: ${fieldName}.${structFieldName} =`, outValue);
                }else{

                    // for each field in outValue, set the corresponding struct field and ensure type matches

                    for(const [structFieldName, structFieldValue] of Object.entries(outValue)){

                        if (!(structFieldName in app.state[fieldName])) {
                            throw new Error(`set - struct field not found: ${fieldName}.${structFieldName}`);
                        }

                        const origStructValue = app.state[fieldName][structFieldName];

                        // verify type of `structFieldValue` matches type of `origStructValue`
                        const newStructType = getTypeName(origStructValue);
                        const structFieldValueType = getTypeName(structFieldValue);
                        if (structFieldValueType !== newStructType) {
                            throw new Error(`set - type mismatch: ${newStructType} != ${structFieldValueType} - field: ${fieldName}.${structFieldName}`);
                        }

                        app.state[fieldName][structFieldName] = structFieldValue;

                        // console.log(`set - setting struct field: ${fieldName}.${structFieldName} =`, structFieldValue);
                    }
                }

            }else{
                if (newType !== fieldType) {
                    console.error(`set - type mismatch: ${fieldType} != ${newType} - field: ${fieldName}`, outValue);
                    throw new Error(`set - type mismatch: ${fieldType} != ${newType} - field: ${fieldName}`, outValue);
                }
                app.state[fieldName] = outValue;
                // console.log(`set - setting state field: ${fieldName} =`, outValue);
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
        throw new Error('state - must have exactly one state field');
    }
    const fieldName = fieldNames[0];
    
    if (!(fieldName in app.state)) {
        throw new Error(`state - field not found: ${fieldName}`);
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
    
    return lingoExecute(app, opDef.func, opArgs);
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
    
    // Handle special sequence ops functions with custom arg handling
    if (definition.createArgs) {
        return handleSequenceOp(app, expression, ctx);
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
 * Handle special sequence operations (map, filter, etc.)
 */
function handleSequenceOp(app, expression, ctx = null) {
    const funcName = expression.call;
    const args = expression.args || {};
    
    if (funcName === 'map') {
        const iterable = lingoExecute(app, args.iterable, ctx);
        const iterableValue = (typeof iterable === 'object' && 'value' in iterable) 
            ? iterable.value 
            : iterable;
        
        const mapFunc = (item) => {
            const newCtx = ctx ? {...ctx} : {};
            newCtx.self = {item: item};
            const result = lingoExecute(app, args.function, newCtx);
            // If result has a 'value' key, extract it
            if (typeof result === 'object' && result !== null && 'value' in result) {
                return result.value;
            } else if (typeof result === 'object' && result !== null && !Array.isArray(result)) {
                // It's a dict without 'value' - need to recursively evaluate expressions
                const evaluatedResult = {};
                for (const [key, value] of Object.entries(result)) {
                    const evaluated = lingoExecute(app, value, newCtx);
                    // Extract value if wrapped
                    evaluatedResult[key] = (typeof evaluated === 'object' && evaluated !== null && 'value' in evaluated) 
                        ? evaluated.value 
                        : evaluated;
                }
                return evaluatedResult;
            }
            return result;
        };
        
        const resultArray = iterableValue.map(mapFunc);
        return {type: 'list', value: resultArray};
        
    } else if (funcName === 'filter') {
        const iterable = lingoExecute(app, args.iterable, ctx);
        const iterableValue = (typeof iterable === 'object' && 'value' in iterable) 
            ? iterable.value 
            : iterable;
        
        const filterFunc = (item) => {
            const newCtx = ctx ? {...ctx} : {};
            newCtx.self = {item: item};
            const result = lingoExecute(app, args.function, newCtx);
            return (typeof result === 'object' && 'value' in result) ? result.value : result;
        };
        
        const resultArray = iterableValue.filter(filterFunc);
        return {type: 'list', value: resultArray};
        
    } else if (funcName === 'dropwhile') {
        const iterable = lingoExecute(app, args.iterable, ctx);
        const iterableValue = (typeof iterable === 'object' && 'value' in iterable) 
            ? iterable.value 
            : iterable;
        
        const dropwhileFunc = (item) => {
            const newCtx = ctx ? {...ctx} : {};
            newCtx.self = {item: item};
            const result = lingoExecute(app, args.function, newCtx);
            return (typeof result === 'object' && 'value' in result) ? result.value : result;
        };
        
        const resultArray = [];
        let dropping = true;
        for (const item of iterableValue) {
            if (dropping && !dropwhileFunc(item)) {
                dropping = false;
            }
            if (!dropping) {
                resultArray.push(item);
            }
        }
        return {type: 'list', value: resultArray};
        
    } else if (funcName === 'takewhile') {
        const iterable = lingoExecute(app, args.iterable, ctx);
        const iterableValue = (typeof iterable === 'object' && 'value' in iterable) 
            ? iterable.value 
            : iterable;
        
        const takewhileFunc = (item) => {
            const newCtx = ctx ? {...ctx} : {};
            newCtx.self = {item: item};
            const result = lingoExecute(app, args.function, newCtx);
            return (typeof result === 'object' && 'value' in result) ? result.value : result;
        };
        
        const resultArray = [];
        for (const item of iterableValue) {
            if (takewhileFunc(item)) {
                resultArray.push(item);
            } else {
                break;
            }
        }
        return {type: 'list', value: resultArray};
        
    } else if (funcName === 'accumulate') {
        const iterable = lingoExecute(app, args.iterable, ctx);
        const iterableValue = (typeof iterable === 'object' && 'value' in iterable) 
            ? iterable.value 
            : iterable;
        
        const accumulateFunc = (a, b) => {
            const newCtx = ctx ? {...ctx} : {};
            newCtx.self = {item: a, next_item: b};
            const result = lingoExecute(app, args.function, newCtx);
            return (typeof result === 'object' && 'value' in result) ? result.value : result;
        };
        
        const initial = args.initial !== undefined ? lingoExecute(app, args.initial, ctx) : null;
        const initialValue = (initial && typeof initial === 'object' && 'value' in initial) 
            ? initial.value 
            : initial;
        
        const resultArray = [];
        let accumulator = initialValue !== null ? initialValue : iterableValue[0];
        
        if (initialValue !== null) {
            resultArray.push(accumulator);
            for (const item of iterableValue) {
                accumulator = accumulateFunc(accumulator, item);
                resultArray.push(accumulator);
            }
        } else {
            resultArray.push(accumulator);
            for (let i = 1; i < iterableValue.length; i++) {
                accumulator = accumulateFunc(accumulator, iterableValue[i]);
                resultArray.push(accumulator);
            }
        }
        
        return {type: 'list', value: resultArray};
        
    } else if (funcName === 'reduce') {
        const iterable = lingoExecute(app, args.iterable, ctx);
        const iterableValue = (typeof iterable === 'object' && 'value' in iterable) 
            ? iterable.value 
            : iterable;
        
        const reduceFunc = (a, b) => {
            const newCtx = ctx ? {...ctx} : {};
            newCtx.self = {item: a, next_item: b};
            const result = lingoExecute(app, args.function, newCtx);
            return (typeof result === 'object' && 'value' in result) ? result.value : result;
        };
        
        const initial = args.initial !== undefined ? lingoExecute(app, args.initial, ctx) : null;
        const initialValue = (initial && typeof initial === 'object' && 'value' in initial) 
            ? initial.value 
            : null;
        
        let result;
        if (initialValue !== null) {
            result = iterableValue.reduce(reduceFunc, initialValue);
        } else {
            result = iterableValue.reduce(reduceFunc);
        }
        
        return {type: getTypeName(result), value: result};
    } else if (funcName === 'crud.create') {

        //
        // init params
        //

        const url = unwrapValue(lingoExecute(app, args.http, ctx));
        const data = lingoExecute(app, args.data, ctx);

        // update state to loading if bind is provided
        let stateField = null;
        if (expression.args.bind && expression.args.bind.state) {
            const stateKeys = Object.keys(expression.args.bind.state);
            if (stateKeys.length === 1) {
                stateField = stateKeys[0];
                if(!(app.state.hasOwnProperty(stateField))){
                    throw new Error(`handleSequenceOp - crud.create - state field not found: ${stateField}`);
                }
                app.state[stateField].state = 'loading';
            }
        }

        //
        // send request
        //

        async function sendCreateRequest(url, data) {
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                if (response.ok) {

                    const responseData = await response.json();
                    // console.log('handleSequenceOp - crud.create - responseData:', responseData);
                    return {state: 'success', item_id: responseData.id};
                    
                }else{
                    console.error('handleSequenceOp - crud.create - HTTP error:', response.status, response.statusText); 
                    return {state: 'error', error: `Response error: ${response.status} ${response.statusText}`};
                }

            } catch (error) {
                console.error('handleSequenceOp - crud.create - network error:', error);
                return {state: 'error', error: `Network error: ${error.message}`};
            }
        }
        
        return sendCreateRequest(url, data)
    
    }else if(funcName === 'crud.read'){

        //
        // init params
        //

        const url = unwrapValue(lingoExecute(app, args.http, ctx));
        
        // update state to loading if bind is provided
        let stateField = null;
        if (expression.args.bind && expression.args.bind.state) {
            const stateKeys = Object.keys(expression.args.bind.state);
            if (stateKeys.length === 1) {
                stateField = stateKeys[0];
                if(!(app.state.hasOwnProperty(stateField))){
                    throw new Error(`handleSequenceOp - crud.read - state field not found: ${stateField}`);
                }
                app.state[stateField].state = 'loading...';
            }
        }
        
        //
        // send request
        //
        
        async function sendReadRequest(url) {

            // console.log('handleSequenceOp - crud.read - url:', url);

            try {
                const response = await fetch(url, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {
                    const responseData = await response.json();
                    // console.log('handleSequenceOp - crud.read - responseData:', responseData);

                    return {
                        state: 'loaded',
                        item: responseData
                    };
                    
                }else{
                    console.error('handleSequenceOp - crud.read - HTTP error:', response.status, response.statusText); 
                    return {
                        state: 'error',
                        error: `Response error: ${response.status} ${response.statusText}`
                    };
                }

            } catch (error) {
                console.error('handleSequenceOp - crud.read - network error:', error);
                return {
                    state: 'error',
                    error: `Network error: ${error.message}`
                };
            }
        }

        return sendReadRequest(url);
    
    }else if(funcName === 'crud.delete'){
        
        //
        // init params
        //

        const url = unwrapValue(lingoExecute(app, args.http, ctx));

        // update state to loading if bind is provided
        let stateField = null;
        if (expression.args.bind && expression.args.bind.state) {
            const stateKeys = Object.keys(expression.args.bind.state);
            if (stateKeys.length === 1) {
                stateField = stateKeys[0];
                if(!(app.state.hasOwnProperty(stateField))){
                    throw new Error(`handleSequenceOp - crud.delete - state field not found: ${stateField}`);
                }
                app.state[stateField].state = 'loading';
            }
        }

        //
        // send request
        //

        async function sendDeleteRequest(url) {
            try {
                const response = await fetch(url, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {
                    console.log('handleSequenceOp - crud.delete - item deleted successfully');
                    return {state: 'deleted'};
                    
                }else{
                    console.error('handleSequenceOp - crud.delete - HTTP error:', response.status, response.statusText); 
                    return {
                        state: 'error', 
                        error: `Response error: ${response.status} ${response.statusText}`
                    };
                }

            } catch (error) {
                console.error('handleSequenceOp - crud.delete - network error:', error);
                return {
                    state: 'error',
                    error: `Network error: ${error.message}`
                }
            }
        }

        return sendDeleteRequest(url);

    }else if(funcName === 'crud.list'){

        //
        // init params
        //

        const urlBase = unwrapValue(lingoExecute(app, args.http, ctx));
        const offset = unwrapValue(lingoExecute(app, args.offset, ctx));
        const size = unwrapValue(lingoExecute(app, args.size, ctx));
        const url = `${urlBase}?offset=${offset}&size=${size}`;

        // update state to loading if bind is provided
        let stateField = null;
        if (expression.args.bind && expression.args.bind.state) {
            const stateKeys = Object.keys(expression.args.bind.state);
            if (stateKeys.length === 1) {
                stateField = stateKeys[0];
                if(!(app.state.hasOwnProperty(stateField))){
                    throw new Error(`handleSequenceOp - crud.list - state field not found: ${stateField}`);
                }
                app.state[stateField].state = 'loading';
            }
        }

        async function sendListRequest(url) {
            try {
                const response = await fetch(url, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {

                    const responseData = await response.json();
                    // console.log('handleSequenceOp - crud.list - responseData:', responseData);

                    return {
                        state: 'loaded',
                        total: responseData.total,
                        items: responseData.items.map(item => ({type: 'struct', value: item})),
                        showing: responseData.items.length,
                        offset: offset,
                        size: size
                    };
                    
                }else{
                    console.error('handleSequenceOp - crud.list - HTTP error:', response.status, response.statusText); 
                    return {
                        state: 'error',
                        error: `Response error: ${response.status} ${response.statusText}`
                    };
                }

            } catch (error) {
                console.error('handleSequenceOp - crud.list - network error:', error);
                return {
                    state: 'error',
                    error: `Network error: ${error.message}`
                };
            }
        }

        return sendListRequest(url);

    }else{
        throw new Error(`handleSequenceOp - unknown function: ${funcName}`);
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
    if (!state.hasOwnProperty('item')) state.item = null;
    if (!state.hasOwnProperty('state')) state.state = 'pending';
    if (!state.hasOwnProperty('error')) state.error = '';

    //
    // display
    //

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

    let elements = [];

    elements.push({
        text: 'load',
        button: loadScript
    });

    elements.push(...[
        {break: 1},
        {text: 'status: ', style: {bold: true}},
        {text: state.state},
    ]);

    if (state.state == 'pending') {
        // create placeholder data while loading
        const placeholder = {};

        // iterate over model definition fields to create placeholders
        for (const field of Object.keys(definition.fields)) {
            placeholder[field] = '...';
        }

        elements.push({
            type: 'struct',
            value: placeholder,
        });
    }else{
        elements.push({
            type: 'struct',
            value: state.item,
        });
    }

    if (state.state === 'pending') {
        // trigger initial load
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

    console.log('renderModelDelete - state:', state);

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

    if( !element.model.hasOwnProperty('bind')) {
        throw new Error('renderModelList - missing model bind definition');
    }

    if( !element.model.bind.hasOwnProperty('state')) {
        throw new Error('renderModelList - model bind definition must bind to state');
    }

    // get first (and only) field in bind.state
    const stateKeys = Object.keys(element.model.bind.state);
    if( stateKeys.length !== 1 ) {
        throw new Error('renderModelList - model bind.state must have exactly one field');
    }

    const stateField = stateKeys[0];

    let state = app.state[stateField];

    /* assume state is an object and ensure defaults are set */
    if (!state.hasOwnProperty('items')) state.items = [];
    if (!state.hasOwnProperty('total')) state.total = 0;
    if (!state.hasOwnProperty('offset')) state.offset = 0;
    if (!state.hasOwnProperty('size')) state.size = 5;
    if (!state.hasOwnProperty('state')) state.state = "initial";
    if (!state.hasOwnProperty('error')) state.error = "";

    const definition = lingoExecute(app, element.model.definition, ctx);

    let elements = [];

    //
    // pagination buttons
    //

    elements.push({
        text: 'prev',
        button: {
            set: {state: {[stateField]: {}}},
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
        set: {state: {[stateField]: {}}},
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
            set: {state: {[stateField]: {}}},
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
        {text: state.state},
    ]);

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
        console.log('* rendering item WITH instance_url links');
        const instanceUrl = unwrapValue(lingoExecute(app, element.model.instance_url, ctx));
        console.log('instanceUrl:', element.model.instance_url, instanceUrl);
        console.log('app.state[stateField].items:', app.state[stateField].items);
        for (let item of app.state[stateField].items) {

            let copyOfItem = JSON.parse(JSON.stringify(item));
            copyOfItem.value.id = {
                link: `${instanceUrl}${item.value.id}`,
                text: String(item.value.id)
            };
            itemsForTable.push(copyOfItem);
        }
    }else{
        console.log('* rendering item WITHOUT instance_url links');
        itemsForTable = app.state[stateField].items;
    }

    elements.push({
        type: 'list',
        display: {
            format: 'table',
            headers: headers
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
                            { text: app.state[stateField].error }
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
function createDOMElement(app, element) {
    if ('heading' in element) {
        return createHeadingElement(element);
    } else if ('break' in element) {
        return createBreakElement(element);
    } else if ('button' in element) {
        return createButtonElement(app, element);
    } else if ('input' in element) {
        return createInputElement(app, element);
    } else if ('link' in element) {
        return createLinkElement(element);
    } else if ('text' in element) {
        return createTextElement(element);
    } else if ('value' in element) {
        return createValueElement(element);
    } else if ('form' in element) {
        return createFormElement(app, element);
    } else {
        throw new Error('createDOMElement - unknown element type: ' + JSON.stringify(element));
    }
}

/**
 * Create heading element
 */
function createHeadingElement(element) {
    const level = element.level || 1;
    const heading = document.createElement(`h${level}`);
    heading.textContent = element.heading;
    return heading;
}

/**
 * Create text element
 */
function createTextElement(element) {
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
function createValueElement(element) {

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
                        const dummyApp = {spec: {lingo: {version: 'page-beta-1'}}, state: {}, params: {}};
                        const result = lingoExecute(dummyApp, value);
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
                // Format arrays as comma-separated values
                valueCell.textContent = cellValue.join(', ');
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
            if(!element.display.headers) {
                throw new Error('createValueElement - table format list requires headers definition');
            }
            
            const table = document.createElement('table');
            
            // Add header row
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            
            for(const headerDef of element.display.headers) {
                const th = document.createElement('th');
                th.textContent = headerDef.text;
                headerRow.appendChild(th);
            }
            
            thead.appendChild(headerRow);
            table.appendChild(thead);
            
            // Add data rows
            const tbody = document.createElement('tbody');
            for(const item of element.value) {
                // Validate that item is a struct
                if(!item || item.type !== 'struct' || !item.value) {
                    throw new Error('createValueElement - table format list items must be structs');
                }
                
                const row = document.createElement('tr');
                
                for(const headerDef of element.display.headers) {
                    const td = document.createElement('td');
                    
                    const fieldName = headerDef.field;
                    const fieldValue = item.value[fieldName];

                    // console.log('createValueElement - ', fieldName, fieldValue, typeof fieldValue);
                    
                    // Evaluate the value if it's an expression
                    let cellValue = fieldValue;
                    if(typeof fieldValue === 'object' && fieldValue !== null) {
                        if('value' in fieldValue && 'type' in fieldValue) {
                            // Typed value
                            cellValue = fieldValue.value;
                        } else if('call' in fieldValue || 'lingo' in fieldValue) {
                            // Scripted expression - need to evaluate it
                            try {
                                const dummyApp = {spec: {lingo: {version: 'page-beta-1'}}, state: {}, params: {}};
                                const result = lingoExecute(dummyApp, fieldValue);
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
                            cellValue = createLinkElement(fieldValue);
                        }
                    }
                    
                    // Format the cell value for display
                    if(Array.isArray(cellValue)) {
                        // Format arrays as comma-separated values
                        td.textContent = cellValue.join(', ');
                    } else if(cellValue instanceof HTMLElement) {
                        td.appendChild(cellValue);
                    } else {
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

    }else{
        const span = document.createElement('span');
        span.textContent = JSON.stringify(element, null, 4);
        return span;
    }
}

/**
 * Create break element
 */
function createBreakElement(element) {
    const container = document.createElement('div');
    for (let i = 0; i < element.break; i++) {
        container.appendChild(document.createElement('br'));
    }
    return container;
}

/**
 * Create button element
 */
function createButtonElement(app, element) {
    const button = document.createElement('button');
    button.textContent = element.text;


    if (element.hasOwnProperty('disabled')) {
        const disabled = unwrapValue(lingoExecute(app, element.disabled));
        button.disabled = disabled;
    }
    
    button.onclick = () => {
        try {
            lingoExecute(app, element.button);
            renderLingoApp(app, button.closest('.lingo-container'));
        } catch (error) {
            console.error('Button click error:', error);
        }
    };
    return button;
}

/**
 * Create input element
 */
function createInputElement(app, element) {
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
function createLinkElement(element) {
    const link = document.createElement('a');
    link.href = element.link;
    link.textContent = element.text || element.link;
    return link;
}

/**
 * Create form element with table layout
 */
function createFormElement(app, element) {

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

    if( !app.state.hasOwnProperty(formStateField) ) {
        throw new Error(`createFormElement - state field not found: ${formStateField}`);
    }
    const currentState = app.state[formStateField];
    const formData = currentState.data || {};
    // console.log('createFormElement - formState:', formState);
    
    // create a row for each field //

    for (const [fieldKey, fieldSpec] of Object.entries(fields)) {
        const row = document.createElement('tr');

        // Column 1: Field name
        const nameCell = document.createElement('td');
        const fieldName = fieldSpec.name?.lower_case || fieldKey;
        nameCell.textContent = fieldName.charAt(0).toUpperCase() + fieldName.slice(1) + ':';
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
                formData[fieldKey] = defaultValue;
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
                        removeButton.textContent = '×';
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
            } else {
                listInput = document.createElement('input');
                listInput.type = 'text';
                listInput.placeholder = 'Enter text';
            }
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
                    value = listInput.value + ':00';
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
                formData[fieldKey] = inputElement.value ? inputElement.value + ':00' : '';
            });

        } else if (fieldType === 'foreign_key') {
            inputElement = document.createElement('input');
            inputElement.type = 'text';
            inputElement.value = typeof formData[fieldKey] !== 'undefined' ? formData[fieldKey] : '';
            inputElement.placeholder = 'Enter ID';
            inputElement.addEventListener('input', () => {
                formData[fieldKey] = inputElement.value;
            });

        } else if (fieldSpec.enum) {
            inputElement = document.createElement('select');
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
            inputElement.type = 'text';
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
        } else {
            // Description for non-list fields
            thirdCell.className = 'form-description';
            thirdCell.textContent = fieldSpec.description || '';
        }
        
        row.appendChild(thirdCell);
        table.appendChild(row);
    }
    
    // add submit button //

    const submitRow = document.createElement('tr');
    const submitCell = document.createElement('td');
    submitCell.colSpan = 3;
    submitCell.className = 'form-submit-cell';
    
    const submitButton = document.createElement('button');
    submitButton.disabled = currentState.state === 'submitting';
    submitButton.textContent = 'Submit';
    submitButton.addEventListener('click', () => {
        const result = lingoExecute(app, element.form.action, {});
        console.log('Form submission result:', result);
        renderLingoApp(app, document.getElementById('lingo-app'));
    });

    // final assembly //
    
    submitCell.appendChild(submitButton);
    submitRow.appendChild(submitCell);
    table.appendChild(submitRow);
    
    formContainer.appendChild(table);
    return formContainer;
}