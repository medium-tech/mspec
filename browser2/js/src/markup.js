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

// Built-in function lookup table
const lingoFunctionLookup = {
    // comparison #
    
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
    
    // bool #
    
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
    
    // int #
    
    'int': {
        func: lingoInt,
        args: {
            'number': {'type': 'any', 'default': null},
            'string': {'type': 'str', 'default': null},
            'base': {'type': 'int', 'default': 10}
        }
    },
    
    // float #
    
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
    
    // str #
    
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
    
    // math #
    
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
    
    // sequence #
    
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
    
    // sequence ops #
    
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
    
    // random #
    
    'random': {
        'randint': {
            func: (a, b) => Math.floor(Math.random() * (b - a + 1)) + a,
            args: {'a': {'type': 'int'}, 'b': {'type': 'int'}}
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
                throw new Error(`state - ${key} - expression returned type: ${actualType}, expected: ${value.type}`);
            }
            app.state[key] = actualValue;
        } else {
            // Non-calculated value, set to default if not already set
            if (!(key in app.state)) {
                if (!('default' in value)) {
                    throw new Error(`state - ${key} - missing default value`);
                }
                if (getTypeName(value.default) !== value.type) {
                    throw new Error(`state - ${key} - default value type mismatch`);
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
    return typeof value;
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
        console.log('lingo - wrapping primitive result', expression, result);
        return {type: getTypeName(result), value: result};
    }else if (typeof result === 'object' && result !== null) {
        // Already an object or array, return as is
        console.log('lingo - returning object result', expression, result, result instanceof Date);
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
    console.log('renderOutput()', typeof app.spec.output, app.spec.output.length);
    for (let n = 0; n < app.spec.output.length; n++) {
        const element = app.spec.output[n];
        try {
            const rendered = lingoExecute(app, element, ctx);
            console.log('Rendered output element:', typeof rendered, rendered);
            if (typeof rendered === 'object' && rendered !== null && !Array.isArray(rendered)) {
                app.buffer.push(rendered);
            } else if (Array.isArray(rendered)) {
                for (const item of rendered) {
                    if (typeof item === 'object' && item !== null && !Array.isArray(item)) {
                        app.buffer.push(item);
                    } else {
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
        throw new Error(`params - value type mismatch: ${paramDef.type} != ${getTypeName(value)}`);
    }
    
    return value;
}

/**
 * Render state setter - equivalent to Python render_set()
 */
function renderSet(app, expression, ctx = null) {
    try {
        const target = expression.set.state;
        const valueExpr = expression.to;
        
        const fieldNames = Object.keys(target);
        if (fieldNames.length !== 1) {
            throw new Error('set - must have exactly one state field');
        }
        const fieldName = fieldNames[0];
        
        if (fieldNames.length === 0) {
            throw new Error('set - missing state field');
        }
        
        const fieldType = app.spec.state[fieldName].type;
        
        const value = lingoExecute(app, valueExpr, ctx);
        
        if (getTypeName(value) !== fieldType) {
            console.error(`set - value type mismatch: ${fieldType} != ${getTypeName(value)} - field: ${fieldName}`, value);
            throw new Error(`set - value type mismatch: ${fieldType} != ${getTypeName(value)} - field: ${fieldName}`, value);
        }
        
        app.state[fieldName] = value;
        
        return app.state[fieldName];

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
    console.log('renderForm()', element);
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
        throw new Error(`call - undefined func: ${expression.call}`);
    }
    
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
        console.log('call - kwargs function return value', func, renderedArgs, typeof returnValue, returnValue);
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
        console.log('call - positional function return value', func, argsList, typeof returnValue, returnValue);
    }

    console.log('call - function return value', expression.call, typeof returnValue, returnValue);
    
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
    }
    
    throw new Error(`handleSequenceOp - unknown function: ${funcName}`);
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
 * DOM Rendering Functions
 */

/**
 * Render the LingoApp to a DOM container
 */
function renderLingoApp(app, container, preserveFocus = false) {
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
        console.log('Rendered buffer.length:', buffer.length);
        
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
        return createFormElement(element);
    } else {
        console.warn('Unknown element type:', element);
        return null;
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
    return span;
}

/** Create value element
 */
function createValueElement(element) {

    if(element.type == 'list') {

        // element.display.format = 'bulleted' | 'numbered' for ul or ol

        const elementType = element.display && element.display.format == 'numbers' ? 'ol' : 'ul';

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
function createFormElement(element) {
    const formContainer = document.createElement('div');
    const table = document.createElement('table');
    table.style.borderCollapse = 'collapse';
    
    const fields = element.form.fields;
    const formData = {};
    
    // Create a row for each field
    for (const [fieldKey, fieldSpec] of Object.entries(fields)) {
        const row = document.createElement('tr');
        
        // Column 1: Field name
        const nameCell = document.createElement('td');
        nameCell.style.padding = '5px 10px';
        nameCell.style.verticalAlign = 'middle';
        const fieldName = fieldSpec.name?.lower_case || fieldKey;
        nameCell.textContent = fieldName.charAt(0).toUpperCase() + fieldName.slice(1) + ':';
        row.appendChild(nameCell);
        
        // Column 2: Input element
        const inputCell = document.createElement('td');
        inputCell.style.padding = '5px 10px';
        
        let inputElement;
        const fieldType = fieldSpec.type;
        const defaultValue = fieldSpec.default;
        
        // Initialize form data with default value
        formData[fieldKey] = defaultValue;
        
        if (fieldType === 'bool') {
            // Checkbox for boolean
            inputElement = document.createElement('input');
            inputElement.type = 'checkbox';
            inputElement.checked = defaultValue;
            inputElement.addEventListener('change', () => {
                formData[fieldKey] = inputElement.checked;
            });
        } else if (fieldType === 'int') {
            // Number input for integers
            inputElement = document.createElement('input');
            inputElement.type = 'number';
            inputElement.step = '1';
            inputElement.value = defaultValue;
            inputElement.addEventListener('input', () => {
                formData[fieldKey] = parseInt(inputElement.value, 10) || 0;
            });
        } else if (fieldType === 'float') {
            // Number input for floats
            inputElement = document.createElement('input');
            inputElement.type = 'number';
            inputElement.step = 'any';
            inputElement.value = defaultValue;
            inputElement.addEventListener('input', () => {
                formData[fieldKey] = parseFloat(inputElement.value) || 0.0;
            });
        } else {
            // Text input for strings and other types
            inputElement = document.createElement('input');
            inputElement.type = 'text';
            inputElement.value = defaultValue;
            inputElement.addEventListener('input', () => {
                formData[fieldKey] = inputElement.value;
            });
        }
        
        inputCell.appendChild(inputElement);
        row.appendChild(inputCell);
        
        // Column 3: Description
        const descCell = document.createElement('td');
        descCell.style.padding = '5px 10px';
        descCell.style.verticalAlign = 'middle';
        descCell.style.fontStyle = 'italic';
        descCell.style.color = '#666';
        descCell.textContent = fieldSpec.description || '';
        row.appendChild(descCell);
        
        table.appendChild(row);
    }
    
    // Add submit button row
    const submitRow = document.createElement('tr');
    const submitCell = document.createElement('td');
    submitCell.colSpan = 3;
    submitCell.style.padding = '10px';
    
    const submitButton = document.createElement('button');
    submitButton.textContent = 'Submit';
    submitButton.addEventListener('click', () => {
        console.log('Form submitted:', formData);
    });
    
    submitCell.appendChild(submitButton);
    submitRow.appendChild(submitCell);
    table.appendChild(submitRow);
    
    formContainer.appendChild(table);
    return formContainer;
}