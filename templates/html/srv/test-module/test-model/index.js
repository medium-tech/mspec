// vars :: {"test-module": "module.name.kebab_case"}
// vars :: {"TestModel": "model.name.pascal_case", "testModel": "model.name.camel_case", "test-model": "model.name.kebab_case"}

//
// convert
//

const trueBoolStrings = ['1', 'true', 't', 'yes', 'y', 'on'];

function convertListElementBool(input) {
    return trueBoolStrings.includes(input.toLowerCase());
}

function convertListElementInt(input) {
    return parseInt(input);
}

function convertListElementFloat(input) {
    const split = input.split('.');
    if (split.length > 2) {
        throw new Error('Invalid float');
    }
    let result = parseFloat(input)
    if (parseInt(split[1]) === 0) {
        result += 0.0000001;
    }
    
    return result;
}

function convertListElementEnum(input) {
    return input;
}

function convertListElementStr(str) {
    return str;
}

//
// defs
//

// insert :: macro.html_enum_definitions(model.fields)
// macro :: html_enum_definition_begin :: {"single_enum": "field_name"}
const single_enum_options = [
// macro :: html_enum_definition_option :: {"red": "option"}
    'red', 
// end macro ::
    'green', 
    'blue',
// macro :: html_enum_definition_end :: {}
]
// end macro ::

// ignore ::
const multi_enum_options = [
    'giraffe', 
    'elephant', 
    'zebra'
]
// end ignore ::

//
// data functions
//

function initTestModel(data) {
    let result = {
        // insert :: macro.html_init_fields(model.fields)
        // macro :: html_init_bool :: {"single_bool": "field"}
        single_bool: data.single_bool,
        // macro :: html_init_int :: {"single_int": "field"}
        single_int: data.single_int,
        // macro :: html_init_float :: {"single_float": "field"}
        single_float: data.single_float,
        // macro :: html_init_str :: {"single_string": "field"}
        single_string: data.single_string,
        // macro :: html_init_str_enum :: {"single_enum": "field"}
        single_enum: data.single_enum,
        // macro :: html_init_datetime :: {"single_datetime": "field"}
        single_datetime: new Date(data.single_datetime),
        // macro :: html_init_list_bool :: {"multi_bool": "field"}
        multi_bool: data.multi_bool,
        // macro :: html_init_list_int :: {"multi_int": "field"}
        multi_int: data.multi_int,
        // macro :: html_init_list_float :: {"multi_float": "field"}
        multi_float: data.multi_float,
        // macro :: html_init_list_str :: {"multi_string": "field"}
        multi_string: data.multi_string,
        // macro :: html_init_list_str_enum :: {"multi_enum": "field"}
        mutli_enum: data.multi_enum,
        // macro :: html_init_list_datetime :: {"multi_datetime": "field"}
        multi_datetime: data.multi_datetime.map(d => new Date(d))
        // end macro ::
    }

    if (typeof data.id !== 'undefined') {
        result.id = data.id;
    }
    return result;
}

function exampleTestModel() {
    const data = {
        // replace :: macro.html_example_fields(model.fields)
        single_bool: true,
        single_int: 1,
        single_float: 1.1,
        single_string: 'peaches',
        single_enum: 'red',
        single_datetime: new Date('2023-01-01T00:00:00Z'),
        multi_bool: [true, false],
        multi_int: [1, 2, 3],
        multi_float: [1.1, 2.2, 3.3],
        multi_string: ['sequence', 'of', 'words'],
        multi_enum: ['giraffe', 'elephant', 'zebra'],
        multi_datetime: [new Date('2023-01-01T00:00:00Z'), new Date('2023-01-02T00:00:00Z')],
        // end replace ::
    }
    return {...data}
}

function randomTestModel() {
    return {
        // insert :: macro.html_random_fields(model.fields)
        // macro :: html_random_bool :: {"single_bool": "field"}
		'single_bool': randomBool(),
        // macro :: html_random_int :: {"single_int": "field"}
		'single_int': randomInt(),
        // macro :: html_random_float :: {"single_float": "field"}
		'single_float': randomFloat(),
        // macro :: html_random_str :: {"single_string": "field"}
		'single_string': randomStr(),
        // macro :: html_random_str_enum :: {"single_enum": "field"}
		'single_enum': randomStrEnum(single_enum_options),
        // macro :: html_random_datetime :: {"single_datetime": "field"}
		'single_datetime': randomDatetime(),
        // macro :: html_random_list_bool :: {"multi_bool": "field"}
		'multi_bool': randomList(randomBool),
        // macro :: html_random_list_int :: {"multi_int": "field"}
		'multi_int': randomList(randomInt),
        // macro :: html_random_list_float :: {"multi_float": "field"}
		'multi_float': randomList(randomFloat),
        // macro :: html_random_list_str :: {"multi_string": "field"}
		'multi_string': randomList(randomStr),
        // macro :: html_random_list_str_enum :: {"multi_enum": "field"}
        'multi_enum': randomList(randomStrEnum(multi_enum_options)),
        // macro :: html_random_list_datetime :: {"multi_datetime": "field"}
        'multi_datetime': randomList(randomDatetime),
        // end macro ::
    }
}

function verifyTestModel(data) {

    let result = {
        valid: true,
        errors: {}
    }

    // insert :: macro.html_verify_fields(model.fields)
    // macro :: html_verify_bool :: {"single_bool": "field"}
    if (typeof data.single_bool !== 'boolean') {
        result.error.single_bool = 'single_bool must be a boolean';
        result.valid = false;
    }

    // macro :: html_verify_int :: {"single_int": "field"}
    if (!Number.isInteger(data.single_int)) {
        result.error.single_int = 'single_int must be an integer';
        result.valid = false;
    }

    // macro :: html_verify_float :: {"single_float": "field"}
    if (typeof data.single_float !== 'number') {
        result.error.single_float = 'single_float must be a float';
        result.valid = false;
    }

    // macro :: html_verify_str :: {"single_string": "field"}
    if (typeof data.single_string !== 'string') {
        result.error.single_string = 'single_string must be a string';
        result.valid = false;
    }

    // macro :: html_verify_str_enum :: {"single_enum": "field"}
    if (typeof data.single_enum !== 'string') {
        result.error.single_enum = 'single_enum must be a string';
        result.valid = false;
    }else if (!single_enum_options.includes(data.single_enum)) {
        result.error.single_enum = 'invalid single_enum';
        result.valid = false;
    }

    // macro :: html_verify_datetime :: {"single_datetime": "field"}
    if (Object.prototype.toString.call(data.single_datetime) !== '[object Date]') {
        result.error.single_datetime = 'single_datetime must be a datetime';
        result.valid = false;
    }

    // macro :: html_verify_list_bool :: {"multi_bool": "field"}
    if (!Array.isArray(data.multi_bool)) {
        result.error.multi_bool = 'multi_bool must be an array';
        result.valid = false;
    }else if (data.multi_bool.some(tag => typeof tag !== 'boolean')) {
        result.error.multi_bool = 'multi_bool must be an array with element type: boolean';
        result.valid = false;
    }

    // macro :: html_verify_list_int :: {"multi_int": "field"}
    if (!Array.isArray(data.multi_int)) {
        result.error.multi_int = 'multi_int must be an array';
        result.valid = false;
    }else if (data.multi_int.some(tag => typeof tag !== 'number')) {
        result.error.multi_int = 'multi_int must be an array with element type: number';
        result.valid = false;
    }

    // macro :: html_verify_list_float :: {"multi_float": "field"}
    if (!Array.isArray(data.multi_float)) {
        result.error.multi_float = 'multi_float must be an array';
        result.valid = false;
    }else if (data.multi_float.some(tag => typeof tag !== 'number')) {
        result.error.multi_float = 'multi_float must be an array with element type: number';
        result.valid = false;
    }

    // macro :: html_verify_list_str :: {"multi_string": "field"}
    if (!Array.isArray(data.multi_string)) {
        result.error.multi_string = 'multi_string must be an array';
        result.valid = false;
    }else if (data.multi_string.some(tag => typeof tag !== 'string')) {
        result.error.multi_string = 'multi_string must be an array with element type: string';
        result.valid = false;
    }

    // macro :: html_verify_list_str_enum :: {"multi_enum": "field"}
    if (!Array.isArray(data.multi_enum)) {
        result.error.multi_enum = 'multi_enum must be an array';
        result.valid = false;
    }else if (data.multi_enum.some(tag => typeof tag !== 'string' || !multi_enum_options.includes(tag))) {
        
        result.error.multi_enum = 'multi_enum elements must be strings from the predefined options';
        result.valid = false;
    }

    // macro :: html_verify_list_datetime :: {"multi_datetime": "field"}
    if(!Array.isArray(data.multi_datetime)) {
        result.error.multi_datetime = 'multi_datetime must be an array';
        result.valid = false;
    }else if (data.multi_datetime.some(tag => Object.prototype.toString.call(tag) !== '[object Date]')) {
        result.error.multi_datetime = 'multi_datetime must be an array with element type: datetime';
        result.valid = false;
    }
    // end macro ::

    return result

}

function testModelFromInputTBody(tbody) {   
    const data = {};

    // parse id if exists

    const idInput = tbody.querySelector('input[name="id"]');
    if (idInput) {
        data.id = idInput.value;
    }

    // macro :: html_from_input_tbody_str :: {"description": "field"}
    // macro :: html_from_input_tbody_bool :: {"verified": "field"}
    // macro :: html_from_input_tbody_enum :: {"color": "field"}
    // macro :: html_from_input_tbody_int :: {"count": "field"}
    // macro :: html_from_input_tbody_float :: {"score": "field"}
    // macro :: html_from_input_tbody_list :: {"stuff": "field"}
    // macro :: html_from_input_tbody_datetime :: {"when": "field"}
    // end macro ::
    // insert :: macro.html_from_input_tbody_fields(model.fields)
    const single_boolInput = tbody.querySelector('input[name="single_bool"]');
    data.single_bool = single_boolInput.checked;


    const single_intInput = tbody.querySelector('input[name="single_int"]');
    data.single_int = parseInt(single_intInput.value);


    const single_floatInput = tbody.querySelector('input[name="single_float"]');
    data.single_float = parseFloat(single_floatInput.value);


    const single_stringInput = tbody.querySelector('input[name="single_string"]');
    data.single_string = single_stringInput.value;


    const single_enumInput = tbody.querySelector('select[name="single_enum"]');
    data.single_enum = single_enumInput.value;


    const single_datetimeInput = tbody.querySelector('input[name="single_datetime"]');
    data.single_datetime = new Date(single_datetimeInput.value);


    const multi_boolInput = tbody.querySelector('input[name="multi_bool"]');
    data.multi_bool = JSON.parse(multi_boolInput.getAttribute('valueAsJSON'));


    const multi_intInput = tbody.querySelector('input[name="multi_int"]');
    data.multi_int = JSON.parse(multi_intInput.getAttribute('valueAsJSON'));


    const multi_floatInput = tbody.querySelector('input[name="multi_float"]');
    data.multi_float = JSON.parse(multi_floatInput.getAttribute('valueAsJSON'));


    const multi_stringInput = tbody.querySelector('input[name="multi_string"]');
    data.multi_string = JSON.parse(multi_stringInput.getAttribute('valueAsJSON'));




    return data;
}

function testModelToInputTBody(data, tbody) {
    tbody.innerHTML = '';

    // show id if present

    if (typeof data.id !== 'undefined') {
        const idTdKey = document.createElement('td');
        idTdKey.textContent = 'id';

        const idTdInput = document.createElement('td');
        const idInput = document.createElement('input');
        idInput.name = 'id';
        idInput.value = data.id;
        idInput.size = 35;
        idInput.readOnly = true;
        idTdInput.appendChild(idInput);

        const idTdOther = document.createElement('td');
        idTdOther.textContent = '-';

        const idTr = document.createElement('tr');
        idTr.appendChild(idTdKey);
        idTr.appendChild(idTdInput);
        idTr.appendChild(idTdOther);

        tbody.appendChild(idTr);
    }

    // macro :: html_to_input_tbody_str :: {"description": "field"}
    // macro :: html_to_input_tbody_bool :: {"verified": "field"}
    // macro :: html_to_input_tbody_enum :: {"color": "field"}
    // macro :: html_to_input_tbody_int :: {"count": "field"}
    // macro :: html_to_input_tbody_float :: {"score": "field"}
    // macro :: html_to_input_tbody_list :: {"stuff": "field", "Str": "element_type_capitalized"}
    // macro :: html_to_input_tbody_datetime :: {"when": "field"}
    // end macro ::
    // insert :: macro.html_to_input_tbody(model.fields)

    // single_bool - bool

    const single_boolTdKey = document.createElement('td');
    single_boolTdKey.textContent = 'single_bool';

    const single_boolTdInput = document.createElement('td');
    const single_boolInput = document.createElement('input');
    single_boolInput.name = 'single_bool';
    single_boolInput.type = 'checkbox';
    single_boolInput.checked = data.single_bool;
    single_boolTdInput.appendChild(single_boolInput);

    const single_boolTdOther = document.createElement('td');
    single_boolTdOther.textContent = '-';

    const single_boolTr = document.createElement('tr');
    single_boolTr.appendChild(single_boolTdKey);
    single_boolTr.appendChild(single_boolTdInput);
    single_boolTr.appendChild(single_boolTdOther);

    tbody.appendChild(single_boolTr);



    // single_int - int

    const single_intTdKey = document.createElement('td');
    single_intTdKey.textContent = 'single_int';

    const single_intTdInput = document.createElement('td');
    const single_intInput = document.createElement('input');
    single_intInput.name = 'single_int';
    single_intInput.type = 'number';
    single_intInput.size = 5;
    single_intInput.value = data.single_int;
    single_intTdInput.appendChild(single_intInput);

    const single_intTdOther = document.createElement('td');
    single_intTdOther.textContent = '-';

    const single_intTr = document.createElement('tr');
    single_intTr.appendChild(single_intTdKey);
    single_intTr.appendChild(single_intTdInput);
    single_intTr.appendChild(single_intTdOther);

    tbody.appendChild(single_intTr);



    // single_float - float

    const single_floatTdKey = document.createElement('td');
    single_floatTdKey.textContent = 'single_float';

    const single_floatTdInput = document.createElement('td');
    const single_floatInput = document.createElement('input');
    single_floatInput.name = 'single_float';
    single_floatInput.type = 'number';
    single_floatInput.size = 5;
    single_floatInput.value = parseFloat(data.single_float).toFixed(2);
    single_floatInput.step = '.01';
    single_floatTdInput.appendChild(single_floatInput);

    const single_floatTdOther = document.createElement('td');
    single_floatTdOther.textContent = '-';

    const single_floatTr = document.createElement('tr');
    single_floatTr.appendChild(single_floatTdKey);
    single_floatTr.appendChild(single_floatTdInput);
    single_floatTr.appendChild(single_floatTdOther);

    tbody.appendChild(single_floatTr);



    // single_string - str
    const single_stringTdKey = document.createElement('td');
    single_stringTdKey.textContent = 'single_string';

    const single_stringTdInput = document.createElement('td');
    const single_stringInput = document.createElement('input');
    single_stringInput.name = 'single_string';
    single_stringInput.value = data.single_string || '';
    single_stringInput.size = 35;
    single_stringTdInput.appendChild(single_stringInput);

    const single_stringTdOther = document.createElement('td');
    single_stringTdOther.textContent = '-';

    const single_stringTr = document.createElement('tr');
    single_stringTr.appendChild(single_stringTdKey);
    single_stringTr.appendChild(single_stringTdInput);
    single_stringTr.appendChild(single_stringTdOther);

    tbody.appendChild(single_stringTr);



    // single_enum - enum

    const single_enumTdKey = document.createElement('td');
    single_enumTdKey.textContent = 'single_enum';

    const single_enumTdInput = document.createElement('td');
    const single_enumInput = document.createElement('select');
    single_enumInput.name = 'single_enum';
    const single_enumOptions = ['red', 'green', 'blue'];
    for (const option of single_enumOptions) {
        const single_enumOption = document.createElement('option');
        single_enumOption.value = option;
        single_enumOption.textContent = option;
        if (option === data.single_enum) {
            single_enumOption.selected = true;
        }
        single_enumInput.appendChild(single_enumOption);
    }
    single_enumTdInput.appendChild(single_enumInput);

    const single_enumTdOther = document.createElement('td');
    single_enumTdOther.textContent = '-';

    const single_enumTr = document.createElement('tr');
    single_enumTr.appendChild(single_enumTdKey);
    single_enumTr.appendChild(single_enumTdInput);
    single_enumTr.appendChild(single_enumTdOther);

    tbody.appendChild(single_enumTr);



    // single_datetime - datetime

    const single_datetimeTdKey = document.createElement('td');
    single_datetimeTdKey.textContent = 'single_datetime';

    const single_datetimeTdInput = document.createElement('td');
    const single_datetimeInput = document.createElement('input');
    single_datetimeInput.name = 'single_datetime';
    single_datetimeInput.type = 'datetime-local';
    try {
        single_datetimeInput.value = data.single_datetime.toISOString().split('.')[0].slice(0, 16);
    }catch {
        single_datetimeInput.value = '';
    }
    single_datetimeTdInput.appendChild(single_datetimeInput);

    const single_datetimeTdOther = document.createElement('td');
    single_datetimeTdOther.textContent = '-';

    const single_datetimeTr = document.createElement('tr');
    single_datetimeTr.appendChild(single_datetimeTdKey);
    single_datetimeTr.appendChild(single_datetimeTdInput);
    single_datetimeTr.appendChild(single_datetimeTdOther);

    tbody.appendChild(single_datetimeTr);


    // multi_bool - list

    let multi_boolEntered;

    try {
        multi_boolEntered = data.multi_bool.slice()
    }catch {
        multi_boolEntered = [];
    }

    const multi_boolTdKey = document.createElement('td');
    multi_boolTdKey.textContent = 'multi_bool';

    const multi_boolTdInput = document.createElement('td');
    
    const multi_boolInput = document.createElement('input');
    multi_boolInput.name = 'multi_bool';
    multi_boolInput.value = '';
    multi_boolInput.size = 35;
    // we store the actual data on valueAsJSON because we can't store an array in an input value with escaping 
    // and also so we can reset the input between each tag entered
    multi_boolInput.setAttribute('valueAsJSON', JSON.stringify(multi_boolEntered));
    multi_boolInput.placeholder = 'press enter after each item';

    const multi_boolTdOther = document.createElement('td');
    const multi_boolEntriesRender = () => {
        multi_boolTdOther.innerHTML = '';
        let index = 0;
    
        for (const tag of multi_boolEntered) {
            const tagLink = document.createElement('a');
            tagLink.innerHTML = tag;
            tagLink.onclick = () => {
                console.log('removing tag', tag);
                multi_boolEntered = multi_boolEntered.filter(t => t !== tag);
                multi_boolInput.setAttribute('valueAsJSON', JSON.stringify(multi_boolEntered));
                multi_boolEntriesRender();
            }
            const tagSpacer = document.createElement('span');
            tagSpacer.innerHTML = ', ';

            multi_boolTdOther.appendChild(tagLink);

            if (index < multi_boolEntered.length - 1) multi_boolTdOther.appendChild(tagSpacer);
            index++;
        }
    }

    multi_boolEntriesRender();

    multi_boolInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            multi_boolEntered.push(convertListElementBool(multi_boolInput.value));
            multi_boolInput.value = ''
            multi_boolInput.setAttribute('valueAsJSON', JSON.stringify(multi_boolEntered));
            multi_boolEntriesRender();
        }
    });

    multi_boolTdInput.appendChild(multi_boolInput);

    const multi_boolTr = document.createElement('tr');
    multi_boolTr.appendChild(multi_boolTdKey);
    multi_boolTr.appendChild(multi_boolTdInput);
    multi_boolTr.appendChild(multi_boolTdOther);

    tbody.appendChild(multi_boolTr);



    // multi_int - list

    let multi_intEntered;

    try {
        multi_intEntered = data.multi_int.slice()
    }catch {
        multi_intEntered = [];
    }

    const multi_intTdKey = document.createElement('td');
    multi_intTdKey.textContent = 'multi_int';

    const multi_intTdInput = document.createElement('td');
    
    const multi_intInput = document.createElement('input');
    multi_intInput.name = 'multi_int';
    multi_intInput.value = '';
    multi_intInput.size = 35;
    // we store the actual data on valueAsJSON because we can't store an array in an input value with escaping 
    // and also so we can reset the input between each tag entered
    multi_intInput.setAttribute('valueAsJSON', JSON.stringify(multi_intEntered));
    multi_intInput.placeholder = 'press enter after each item';

    const multi_intTdOther = document.createElement('td');
    const multi_intEntriesRender = () => {
        multi_intTdOther.innerHTML = '';
        let index = 0;
    
        for (const tag of multi_intEntered) {
            const tagLink = document.createElement('a');
            tagLink.innerHTML = tag;
            tagLink.onclick = () => {
                console.log('removing tag', tag);
                multi_intEntered = multi_intEntered.filter(t => t !== tag);
                multi_intInput.setAttribute('valueAsJSON', JSON.stringify(multi_intEntered));
                multi_intEntriesRender();
            }
            const tagSpacer = document.createElement('span');
            tagSpacer.innerHTML = ', ';

            multi_intTdOther.appendChild(tagLink);

            if (index < multi_intEntered.length - 1) multi_intTdOther.appendChild(tagSpacer);
            index++;
        }
    }

    multi_intEntriesRender();

    multi_intInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            multi_intEntered.push(convertListElementInt(multi_intInput.value));
            multi_intInput.value = ''
            multi_intInput.setAttribute('valueAsJSON', JSON.stringify(multi_intEntered));
            multi_intEntriesRender();
        }
    });

    multi_intTdInput.appendChild(multi_intInput);

    const multi_intTr = document.createElement('tr');
    multi_intTr.appendChild(multi_intTdKey);
    multi_intTr.appendChild(multi_intTdInput);
    multi_intTr.appendChild(multi_intTdOther);

    tbody.appendChild(multi_intTr);



    // multi_float - list

    let multi_floatEntered;

    try {
        multi_floatEntered = data.multi_float.slice()
    }catch {
        multi_floatEntered = [];
    }

    const multi_floatTdKey = document.createElement('td');
    multi_floatTdKey.textContent = 'multi_float';

    const multi_floatTdInput = document.createElement('td');
    
    const multi_floatInput = document.createElement('input');
    multi_floatInput.name = 'multi_float';
    multi_floatInput.value = '';
    multi_floatInput.size = 35;
    // we store the actual data on valueAsJSON because we can't store an array in an input value with escaping 
    // and also so we can reset the input between each tag entered
    multi_floatInput.setAttribute('valueAsJSON', JSON.stringify(multi_floatEntered));
    multi_floatInput.placeholder = 'press enter after each item';

    const multi_floatTdOther = document.createElement('td');
    const multi_floatEntriesRender = () => {
        multi_floatTdOther.innerHTML = '';
        let index = 0;
    
        for (const tag of multi_floatEntered) {
            const tagLink = document.createElement('a');
            tagLink.innerHTML = tag;
            tagLink.onclick = () => {
                console.log('removing tag', tag);
                multi_floatEntered = multi_floatEntered.filter(t => t !== tag);
                multi_floatInput.setAttribute('valueAsJSON', JSON.stringify(multi_floatEntered));
                multi_floatEntriesRender();
            }
            const tagSpacer = document.createElement('span');
            tagSpacer.innerHTML = ', ';

            multi_floatTdOther.appendChild(tagLink);

            if (index < multi_floatEntered.length - 1) multi_floatTdOther.appendChild(tagSpacer);
            index++;
        }
    }

    multi_floatEntriesRender();

    multi_floatInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            multi_floatEntered.push(convertListElementFloat(multi_floatInput.value));
            multi_floatInput.value = ''
            multi_floatInput.setAttribute('valueAsJSON', JSON.stringify(multi_floatEntered));
            multi_floatEntriesRender();
        }
    });

    multi_floatTdInput.appendChild(multi_floatInput);

    const multi_floatTr = document.createElement('tr');
    multi_floatTr.appendChild(multi_floatTdKey);
    multi_floatTr.appendChild(multi_floatTdInput);
    multi_floatTr.appendChild(multi_floatTdOther);

    tbody.appendChild(multi_floatTr);



    // multi_string - list

    let multi_stringEntered;

    try {
        multi_stringEntered = data.multi_string.slice()
    }catch {
        multi_stringEntered = [];
    }

    const multi_stringTdKey = document.createElement('td');
    multi_stringTdKey.textContent = 'multi_string';

    const multi_stringTdInput = document.createElement('td');
    
    const multi_stringInput = document.createElement('input');
    multi_stringInput.name = 'multi_string';
    multi_stringInput.value = '';
    multi_stringInput.size = 35;
    // we store the actual data on valueAsJSON because we can't store an array in an input value with escaping 
    // and also so we can reset the input between each tag entered
    multi_stringInput.setAttribute('valueAsJSON', JSON.stringify(multi_stringEntered));
    multi_stringInput.placeholder = 'press enter after each item';

    const multi_stringTdOther = document.createElement('td');
    const multi_stringEntriesRender = () => {
        multi_stringTdOther.innerHTML = '';
        let index = 0;
    
        for (const tag of multi_stringEntered) {
            const tagLink = document.createElement('a');
            tagLink.innerHTML = tag;
            tagLink.onclick = () => {
                console.log('removing tag', tag);
                multi_stringEntered = multi_stringEntered.filter(t => t !== tag);
                multi_stringInput.setAttribute('valueAsJSON', JSON.stringify(multi_stringEntered));
                multi_stringEntriesRender();
            }
            const tagSpacer = document.createElement('span');
            tagSpacer.innerHTML = ', ';

            multi_stringTdOther.appendChild(tagLink);

            if (index < multi_stringEntered.length - 1) multi_stringTdOther.appendChild(tagSpacer);
            index++;
        }
    }

    multi_stringEntriesRender();

    multi_stringInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            multi_stringEntered.push(convertListElementStr(multi_stringInput.value));
            multi_stringInput.value = ''
            multi_stringInput.setAttribute('valueAsJSON', JSON.stringify(multi_stringEntered));
            multi_stringEntriesRender();
        }
    });

    multi_stringTdInput.appendChild(multi_stringInput);

    const multi_stringTr = document.createElement('tr');
    multi_stringTr.appendChild(multi_stringTdKey);
    multi_stringTr.appendChild(multi_stringTdInput);
    multi_stringTr.appendChild(multi_stringTdOther);

    tbody.appendChild(multi_stringTr);




    return tbody;

}

function testModelToDisplayTBody(data, tbody) {
    tbody.innerHTML = '';

    // id - string

    const idTdKey = document.createElement('td');
    idTdKey.textContent = 'id';

    const idTdValue = document.createElement('td');
    idTdValue.textContent = data.id;

    const idTr = document.createElement('tr');
    idTr.appendChild(idTdKey);
    idTr.appendChild(idTdValue);

    tbody.appendChild(idTr);

    // macro :: html_to_display_tbody_str :: {"description": "field"}
    // macro :: html_to_display_tbody_bool :: {"verified": "field"}
    // macro :: html_to_display_tbody_enum :: {"color": "field"}
    // macro :: html_to_display_tbody_int :: {"count": "field"}
    // macro :: html_to_display_tbody_float :: {"score": "field"}
    // macro :: html_to_display_tbody_list :: {"stuff": "field"}
    // macro :: html_to_display_tbody_datetime :: {"when": "field"}
    // end macro ::
    // insert :: macro.html_to_display_tbody(model.fields)
    const single_boolTdKey = document.createElement('td');
    single_boolTdKey.textContent = 'single_bool';

    const single_boolTdValue = document.createElement('td');
    single_boolTdValue.textContent = (data.single_bool) ? 'yes' : 'no';

    const single_boolTr = document.createElement('tr');
    single_boolTr.appendChild(single_boolTdKey);
    single_boolTr.appendChild(single_boolTdValue);

    tbody.appendChild(single_boolTr);


    const single_intTdKey = document.createElement('td');
    single_intTdKey.textContent = 'single_int';

    const single_intTdValue = document.createElement('td');
    single_intTdValue.textContent = data.single_int;

    const single_intTr = document.createElement('tr');
    single_intTr.appendChild(single_intTdKey);
    single_intTr.appendChild(single_intTdValue);

    tbody.appendChild(single_intTr);


    const single_floatTdKey = document.createElement('td');
    single_floatTdKey.textContent = 'single_float';

    const single_floatTdValue = document.createElement('td');
    single_floatTdValue.textContent = data.single_float;
    
    const single_floatTr = document.createElement('tr');
    single_floatTr.appendChild(single_floatTdKey);
    single_floatTr.appendChild(single_floatTdValue);

    tbody.appendChild(single_floatTr);


    const single_stringTdKey = document.createElement('td');
    single_stringTdKey.textContent = 'single_string';

    const single_stringTdValue = document.createElement('td');
    single_stringTdValue.textContent = data.single_string;

    const single_stringTr = document.createElement('tr');
    single_stringTr.appendChild(single_stringTdKey);
    single_stringTr.appendChild(single_stringTdValue);

    tbody.appendChild(single_stringTr);


    const single_enumTdKey = document.createElement('td');
    single_enumTdKey.textContent = 'single_enum';

    const single_enumTdValue = document.createElement('td');
    single_enumTdValue.textContent = data.single_enum;

    const single_enumTr = document.createElement('tr');
    single_enumTr.appendChild(single_enumTdKey);
    single_enumTr.appendChild(single_enumTdValue);

    tbody.appendChild(single_enumTr);


    const single_datetimeTdKey = document.createElement('td');
    single_datetimeTdKey.textContent = 'single_datetime';

    const single_datetimeTdValue = document.createElement('td');
    single_datetimeTdValue.textContent = data.single_datetime.toISOString().split('.')[0];

    const single_datetimeTr = document.createElement('tr');
    single_datetimeTr.appendChild(single_datetimeTdKey);
    single_datetimeTr.appendChild(single_datetimeTdValue);

    tbody.appendChild(single_datetimeTr);

    const multi_boolTdKey = document.createElement('td');
    multi_boolTdKey.textContent = 'multi_bool';

    const multi_boolTdValue = document.createElement('td');
    multi_boolTdValue.textContent = data.multi_bool.join(', ');

    const multi_boolTr = document.createElement('tr');
    multi_boolTr.appendChild(multi_boolTdKey);
    multi_boolTr.appendChild(multi_boolTdValue);

    tbody.appendChild(multi_boolTr);


    const multi_intTdKey = document.createElement('td');
    multi_intTdKey.textContent = 'multi_int';

    const multi_intTdValue = document.createElement('td');
    multi_intTdValue.textContent = data.multi_int.join(', ');

    const multi_intTr = document.createElement('tr');
    multi_intTr.appendChild(multi_intTdKey);
    multi_intTr.appendChild(multi_intTdValue);

    tbody.appendChild(multi_intTr);


    const multi_floatTdKey = document.createElement('td');
    multi_floatTdKey.textContent = 'multi_float';

    const multi_floatTdValue = document.createElement('td');
    multi_floatTdValue.textContent = data.multi_float.join(', ');

    const multi_floatTr = document.createElement('tr');
    multi_floatTr.appendChild(multi_floatTdKey);
    multi_floatTr.appendChild(multi_floatTdValue);

    tbody.appendChild(multi_floatTr);


    const multi_stringTdKey = document.createElement('td');
    multi_stringTdKey.textContent = 'multi_string';

    const multi_stringTdValue = document.createElement('td');
    multi_stringTdValue.textContent = data.multi_string.join(', ');

    const multi_stringTr = document.createElement('tr');
    multi_stringTr.appendChild(multi_stringTdKey);
    multi_stringTr.appendChild(multi_stringTdValue);

    tbody.appendChild(multi_stringTr);




    return tbody;
}

function testModelToTableRow(data) {

    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    tr.onclick = () => window.location.href = `/test-module/test-model/${data.id}`

    // id - string

    const idTd = document.createElement('td');
    idTd.textContent = data.id;
    tr.appendChild(idTd);

    // macro :: html_to_table_row_str :: {"description": "field"}
    // macro :: html_to_table_row_bool :: {"verified": "field"}
    // macro :: html_to_table_row_enum :: {"color": "field"}
    // macro :: html_to_table_row_int :: {"count": "field"}
    // macro :: html_to_table_row_float :: {"score": "field"}
    // macro :: html_to_table_row_list :: {"stuff": "field"}
    // end macro ::

    // macro :: html_to_table_row_datetime :: {"when": "field"}
    // end macro ::
    // insert :: macro.html_to_table_row(model.fields)
    const single_boolTd = document.createElement('td');
    single_boolTd.textContent = (data.single_bool) ? 'yes' : 'no';
    tr.appendChild(single_boolTd);


    const single_intTd = document.createElement('td');
    single_intTd.textContent = data.single_int;
    tr.appendChild(single_intTd);


    const single_floatTd = document.createElement('td');
    single_floatTd.textContent = data.single_float;
    tr.appendChild(single_floatTd);


    const single_stringTd = document.createElement('td');
    single_stringTd.textContent = data.single_string;
    tr.appendChild(single_stringTd);


    const single_enumTd = document.createElement('td');
    single_enumTd.textContent = data.single_enum;
    tr.appendChild(single_enumTd);


    const single_datetimeTd = document.createElement('td');
    single_datetimeTd.textContent = data.single_datetime.toISOString().split('.')[0];
    tr.appendChild(single_datetimeTd);

    const multi_boolTd = document.createElement('td');
    multi_boolTd.textContent = data.multi_bool.join(', ');
    tr.appendChild(multi_boolTd);

    const multi_intTd = document.createElement('td');
    multi_intTd.textContent = data.multi_int.join(', ');
    tr.appendChild(multi_intTd);

    const multi_floatTd = document.createElement('td');
    multi_floatTd.textContent = data.multi_float.join(', ');
    tr.appendChild(multi_floatTd);

    const multi_stringTd = document.createElement('td');
    multi_stringTd.textContent = data.multi_string.join(', ');
    tr.appendChild(multi_stringTd);



    return tr;

}

function testModelListToDisplayTBody(testModelList, tbody) {

    tbody.innerHTML = '';

    for (const testModel of testModelList) {
        tbody.appendChild(testModelToTableRow(testModel));
    }

    return tbody;

}

//
// serialize functions
//

function testModelForJSON(data) {
    // convert an items types to be ready to JSON

    let result = {}
    for (const field in data) {
        if (Object.prototype.toString.call(data[field]) === '[object Date]') {
            result[field] = data[field].toISOString().split('.')[0];
        }else{
            result[field] = data[field];
        }
    }
    return result;
}

//
// client functions
//

function clientCreateTestModel(data) {
    
    return fetch('/api/test-module/test-model', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
}

function clientReadTestModel(id) {

    return fetch(`/api/test-module/test-model/${id}`, {
        method: 'GET',
    })
}

function clientUpdateTestModel(id, data) {

    return fetch(`/api/test-module/test-model/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })

}

function clientDeleteTestModel(id) {

    return fetch(`/api/test-module/test-model/${id}`, {
        method: 'DELETE',
    })

}

function clientListTestModels(offset, size) {

    return fetch(`/api/test-module/test-model?offset=${offset}&size=${size}`, {
        method: 'GET',
    })
}