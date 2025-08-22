/**
 * JavaScript implementation of the mspec markup language renderer
 * This is equivalent to the Python markup.py module
 */

// Date/time formatting
const datetimeFormatStr = '%Y-%m-%dT%H:%M:%S';

// Built-in function lookup table
const lingoFunctionLookup = {
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
    'pow': {
        func: (a, b) => Math.pow(a, b),
        args: {'a': {'type': 'number'}, 'b': {'type': 'number'}}
    },
    
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
    
    'current': {
        'weekday': {
            func: () => new Date().getDay(), // 0=Sunday, 1=Monday, etc.
            args: {}
        }
    },
    'datetime': {
        'now': {
            func: () => new Date(),
            args: {}
        }
    },
    'random': {
        'randint': {
            func: (a, b) => Math.floor(Math.random() * (b - a + 1)) + a,
            args: {'a': {'type': 'number'}, 'b': {'type': 'number'}}
        }
    }
};

/**
 * LingoApp class - equivalent to Python LingoApp dataclass
 */
class LingoApp {
    constructor(spec, params = {}, state = {}, buffer = []) {
        this.spec = JSON.parse(JSON.stringify(spec)); // deep copy
        this.params = params;
        this.state = state;
        this.buffer = buffer;
    }
}

/**
 * Create a new LingoApp instance - equivalent to Python lingo_app()
 */
function lingoApp(spec, params = {}) {
    const instance = new LingoApp(JSON.parse(JSON.stringify(spec)), params, {}, []);
    
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
            if (getTypeName(newValue) !== value.type) {
                throw new Error(`state - ${key} - expression returned type: ${getTypeName(newValue)}`);
            }
            app.state[key] = newValue;
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
    if (typeof expression === 'object' && expression !== null && !Array.isArray(expression)) {
        if ('set' in expression) {
            return renderSet(app, expression, ctx);
        } else if ('state' in expression) {
            return renderState(app, expression, ctx);
        } else if ('params' in expression) {
            return renderParams(app, expression, ctx);
        } else if ('op' in expression) {
            return renderOp(app, expression, ctx);
        } else if ('call' in expression) {
            return renderCall(app, expression, ctx);
        } else if ('block' in expression) {
            return renderBlock(app, expression, ctx);
        } else if ('lingo' in expression) {
            return renderLingo(app, expression, ctx);
        } else if ('branch' in expression) {
            return renderBranch(app, expression, ctx);
        } else if ('switch' in expression) {
            return renderSwitch(app, expression, ctx);
        } else if ('heading' in expression) {
            return renderHeading(app, expression, ctx);
        } else if ('args' in expression) {
            return renderArgs(app, expression, ctx);
        } else {
            return expression;
        }
    } else {
        return expression;
    }
}

/**
 * Render output buffer - equivalent to Python render_output()
 */
function renderOutput(app, ctx = null) {
    app.buffer = [];
    for (let n = 0; n < app.spec.output.length; n++) {
        const element = app.spec.output[n];
        try {
            const rendered = lingoExecute(app, element, ctx);
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
            const condition = lingoExecute(app, expr, ctx);
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
        
        const value = lingoExecute(app, switchExpr, ctx);
        
        for (const caseItem of cases) {
            if (value === caseItem.case) {
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
            throw new Error(`set - value type mismatch: ${fieldType} != ${getTypeName(value)}`);
        }
        
        app.state[fieldName] = value;
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
    const resultType = typeof result;
    
    if (resultType === 'string') {
        return {text: result};
    } else if (resultType === 'number' || resultType === 'boolean') {
        return {text: String(result)};
    } else if (result instanceof Date) {
        return {text: formatDateTime(result)};
    } else if (typeof result === 'object' && result !== null) {
        return result;
    } else {
        throw new Error(`lingo - invalid result type: ${resultType}`);
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
    const args = expression.args || {};
    
    const nameSplit = expression.call.split('.');
    const nameDepth = nameSplit.length;
    
    if (nameDepth < 1 || nameDepth > 2) {
        throw new Error('call - invalid function name');
    }
    
    // Get function and args definition
    let func, argsDef;
    try {
        if (nameDepth === 1) {
            func = lingoFunctionLookup[nameSplit[0]].func;
            argsDef = lingoFunctionLookup[nameSplit[0]].args || {};
        } else {
            func = lingoFunctionLookup[nameSplit[0]][nameSplit[1]].func;
            argsDef = lingoFunctionLookup[nameSplit[0]][nameSplit[1]].args || {};
        }
    } catch (error) {
        throw new Error(`call - undefined func: ${expression.call}`);
    }
    
    // Validate and render args
    const renderedArgs = {};
    for (const [argName, argExpression] of Object.entries(args)) {
        if (!(argName in argsDef)) {
            throw new Error(`call - unknown arg: ${argName}`);
        }
        
        const value = lingoExecute(app, argExpression, ctx);
        const argType = argsDef[argName].type;
        
        if (argType !== 'any') {
            if (argType === 'number' && typeof value !== 'number') {
                throw new Error(`call - arg ${argName} - expected type number, got ${typeof value}`);
            } else if (argType !== 'number' && argType !== 'any' && typeof value !== argType) {
                throw new Error(`call - arg ${argName} - expected type ${argType}, got ${typeof value}`);
            }
        }
        
        renderedArgs[argName] = value;
    }
    
    // Call function with args in the correct order
    const funcArgs = Object.keys(argsDef).map(argName => renderedArgs[argName]);
    return func(...funcArgs);
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
 * DOM Rendering Functions
 */

/**
 * Render the LingoApp to a DOM container
 */
function renderLingoApp(app, container) {
    // Update state and render output
    lingoUpdateState(app);
    const buffer = renderOutput(app);
    
    // Clear container
    container.innerHTML = '';
    
    // Render each element in the buffer
    for (const element of buffer) {
        const domElement = createDOMElement(app, element);
        if (domElement) {
            container.appendChild(domElement);
        }
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
                renderLingoApp(app, input.closest('.lingo-container'));
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
    link.target = '_blank';
    return link;
}