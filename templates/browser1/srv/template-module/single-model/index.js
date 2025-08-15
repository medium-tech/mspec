// vars :: {"template-module": "module.name.kebab_case"}
// vars :: {"SingleModel": "model.name.pascal_case", "singleModel": "model.name.camel_case", "single-model": "model.name.kebab_case"}

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

function convertListElementDatetime(input) {
    const date = new Date(input);
    if (isNaN(date.getTime())) {
        throw new Error('Invalid datetime');
    }
    return date;
}

//
// defs
//

// insert :: macro.browser1_enum_definitions(model.fields)
// macro :: browser1_enum_definition_begin :: {"single_enum": "field_name"}
const single_enum_options = [
// macro :: browser1_enum_definition_option :: {"red": "option"}
    'red', 
// end macro ::
// ignore ::
    'green', 
    'blue',
// end ignore ::
// macro :: browser1_enum_definition_end :: {}
]
// end macro ::

//
// data functions
//

function initSingleModel(data) {
    let result = {
        // insert :: macro.browser1_init_fields(model.fields)
        // macro :: browser1_init_bool :: {"single_bool": "field"}
        single_bool: data.single_bool,
        // macro :: browser1_init_int :: {"single_int": "field"}
        single_int: data.single_int,
        // macro :: browser1_init_float :: {"single_float": "field"}
        single_float: data.single_float,
        // macro :: browser1_init_str :: {"single_string": "field"}
        single_string: data.single_string,
        // macro :: browser1_init_str_enum :: {"single_enum": "field"}
        single_enum: data.single_enum,
        // macro :: browser1_init_datetime :: {"single_datetime": "field"}
        single_datetime: new Date(data.single_datetime),
        // end macro ::
    }

    if (typeof data.id !== 'undefined') {
        result.id = data.id;
    }
    return result;
}

function exampleSingleModel() {
    const data = {
        // replace :: macro.browser1_example_fields(model.fields)
        single_bool: true,
        single_int: 1,
        single_float: 1.1,
        single_string: 'peaches',
        single_enum: 'red',
        single_datetime: new Date('2023-01-01T00:00:00Z'),
        // end replace ::
    }
    return {...data}
}

function randomSingleModel() {
    return {
        // insert :: macro.browser1_random_fields(model.fields)
        // macro :: browser1_random_bool :: {"single_bool": "field"}
		'single_bool': randomBool(),
        // macro :: browser1_random_int :: {"single_int": "field"}
		'single_int': randomInt(),
        // macro :: browser1_random_float :: {"single_float": "field"}
		'single_float': randomFloat(),
        // macro :: browser1_random_str :: {"single_string": "field"}
		'single_string': randomStr(),
        // macro :: browser1_random_str_enum :: {"single_enum": "field"}
		'single_enum': randomStrEnum(single_enum_options),
        // macro :: browser1_random_datetime :: {"single_datetime": "field"}
		'single_datetime': randomDatetime(),
        // end macro ::
    }
}

function verifySingleModel(data) {

    let result = {
        valid: true,
        errors: {}
    }

    // insert :: macro.browser1_verify_fields(model.fields)
    // macro :: browser1_verify_bool :: {"single_bool": "field"}
    if (typeof data.single_bool !== 'boolean') {
        result.error.single_bool = 'single_bool must be a boolean';
        result.valid = false;
    }

    // macro :: browser1_verify_int :: {"single_int": "field"}
    if (!Number.isInteger(data.single_int)) {
        result.error.single_int = 'single_int must be an integer';
        result.valid = false;
    }

    // macro :: browser1_verify_float :: {"single_float": "field"}
    if (typeof data.single_float !== 'number') {
        result.error.single_float = 'single_float must be a float';
        result.valid = false;
    }

    // macro :: browser1_verify_str :: {"single_string": "field"}
    if (typeof data.single_string !== 'string') {
        result.error.single_string = 'single_string must be a string';
        result.valid = false;
    }

    // macro :: browser1_verify_str_enum :: {"single_enum": "field"}
    if (typeof data.single_enum !== 'string') {
        result.error.single_enum = 'single_enum must be a string';
        result.valid = false;
    }else if (!single_enum_options.includes(data.single_enum)) {
        result.error.single_enum = 'invalid single_enum';
        result.valid = false;
    }

    // macro :: browser1_verify_datetime :: {"single_datetime": "field"}
    if (Object.prototype.toString.call(data.single_datetime) !== '[object Date]') {
        result.error.single_datetime = 'single_datetime must be a datetime';
        result.valid = false;
    }
    // end macro ::

    return result

}

function singleModelFromInputTBody(tbody) {   
    console.log('singleModelFromInputTBody', tbody);
    const data = {};

    // parse id if exists

    const idInput = tbody.querySelector('input[name="id"]');
    if (idInput) {
        data.id = idInput.value;
    }

    // insert :: macro.browser1_from_input_tbody_fields(model.fields)
    // macro :: browser1_from_input_tbody_bool :: {"single_bool": "field"}
    const single_boolInput = tbody.querySelector('input[name="single_bool"]');
    data.single_bool = single_boolInput.checked;

    // macro :: browser1_from_input_tbody_int :: {"single_int": "field"}
    const single_intInput = tbody.querySelector('input[name="single_int"]');
    data.single_int = parseInt(single_intInput.value);

    // macro :: browser1_from_input_tbody_float :: {"single_float": "field"}
    const single_floatInput = tbody.querySelector('input[name="single_float"]');
    data.single_float = parseFloat(single_floatInput.value);

    // macro :: browser1_from_input_tbody_str :: {"single_string": "field"}
    const single_stringInput = tbody.querySelector('input[name="single_string"]');
    data.single_string = single_stringInput.value;

    // macro :: browser1_from_input_tbody_str_enum :: {"single_enum": "field"}
    const single_enumInput = tbody.querySelector('select[name="single_enum"]');
    data.single_enum = single_enumInput.value;

    // macro :: browser1_from_input_tbody_datetime :: {"single_datetime": "field"}
    const single_datetimeInput = tbody.querySelector('input[name="single_datetime"]');
    data.single_datetime = new Date(single_datetimeInput.value);
    // end macro ::

    return data;
}

function singleModelToInputTBody(data, tbody) {
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


    // insert :: macro.browser1_to_input_tbody(model.fields)
    // macro :: browser1_to_input_tbody_bool :: {"single_bool": "field"}
    //
    // single_bool - bool
    //

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

    // macro :: browser1_to_input_tbody_int :: {"single_int": "field"}
    //
    // single_int - int
    //

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

    // macro :: browser1_to_input_tbody_float :: {"single_float": "field"}
    //
    // single_float - float
    //

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

    // macro :: browser1_to_input_tbody_str :: {"single_string": "field"}
    //
    // single_string - str
    //

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

    // macro :: browser1_to_input_tbody_str_enum :: {"single_enum": "field"}
    //
    // single_enum - enum
    //

    const single_enumTdKey = document.createElement('td');
    single_enumTdKey.textContent = 'single_enum';

    const single_enumTdInput = document.createElement('td');
    const single_enumInput = document.createElement('select');
    single_enumInput.name = 'single_enum';
    for (const option of single_enum_options) {
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

    // macro :: browser1_to_input_tbody_datetime :: {"single_datetime": "field"}
    //
    // single_datetime - datetime
    //

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
    // end macro ::

    return tbody;

}

function singleModelToDisplayTBody(data, tbody) {
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

    // insert :: macro.browser1_to_display_tbody(model.fields)
    // macro :: browser1_to_display_tbody_bool :: {"single_bool": "field"}
    //
    // single_bool - bool
    //

    const single_boolTdKey = document.createElement('td');
    single_boolTdKey.textContent = 'single_bool';

    const single_boolTdValue = document.createElement('td');
    single_boolTdValue.textContent = (data.single_bool) ? 'yes' : 'no';

    const single_boolTr = document.createElement('tr');
    single_boolTr.appendChild(single_boolTdKey);
    single_boolTr.appendChild(single_boolTdValue);

    tbody.appendChild(single_boolTr);

    // macro :: browser1_to_display_tbody_int :: {"single_int": "field"}
    //
    // single_int - int
    //

    const single_intTdKey = document.createElement('td');
    single_intTdKey.textContent = 'single_int';

    const single_intTdValue = document.createElement('td');
    single_intTdValue.textContent = data.single_int;

    const single_intTr = document.createElement('tr');
    single_intTr.appendChild(single_intTdKey);
    single_intTr.appendChild(single_intTdValue);

    tbody.appendChild(single_intTr);

    // macro :: browser1_to_display_tbody_float :: {"single_float": "field"}
    //
    // single_float - float
    //

    const single_floatTdKey = document.createElement('td');
    single_floatTdKey.textContent = 'single_float';

    const single_floatTdValue = document.createElement('td');
    single_floatTdValue.textContent = data.single_float;
    
    const single_floatTr = document.createElement('tr');
    single_floatTr.appendChild(single_floatTdKey);
    single_floatTr.appendChild(single_floatTdValue);

    tbody.appendChild(single_floatTr);

    // macro :: browser1_to_display_tbody_str :: {"single_string": "field"}
    //
    // single_string - str
    //

    const single_stringTdKey = document.createElement('td');
    single_stringTdKey.textContent = 'single_string';

    const single_stringTdValue = document.createElement('td');
    single_stringTdValue.textContent = data.single_string;

    const single_stringTr = document.createElement('tr');
    single_stringTr.appendChild(single_stringTdKey);
    single_stringTr.appendChild(single_stringTdValue);

    tbody.appendChild(single_stringTr);

    // macro :: browser1_to_display_tbody_str_enum :: {"single_enum": "field"}
    //
    // single_enum - enum
    //

    const single_enumTdKey = document.createElement('td');
    single_enumTdKey.textContent = 'single_enum';

    const single_enumTdValue = document.createElement('td');
    single_enumTdValue.textContent = data.single_enum;

    const single_enumTr = document.createElement('tr');
    single_enumTr.appendChild(single_enumTdKey);
    single_enumTr.appendChild(single_enumTdValue);

    tbody.appendChild(single_enumTr);

    // macro :: browser1_to_display_tbody_datetime :: {"single_datetime": "field"}
    //
    // single_datetime - datetime
    //

    const single_datetimeTdKey = document.createElement('td');
    single_datetimeTdKey.textContent = 'single_datetime';

    const single_datetimeTdValue = document.createElement('td');
    single_datetimeTdValue.textContent = data.single_datetime.toISOString().split('.')[0];

    const single_datetimeTr = document.createElement('tr');
    single_datetimeTr.appendChild(single_datetimeTdKey);
    single_datetimeTr.appendChild(single_datetimeTdValue);

    tbody.appendChild(single_datetimeTr);
    // end macro ::

    return tbody;
}

function singleModelToTableRow(data) {

    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    tr.onclick = () => window.location.href = `/template-module/single-model/${data.id}`

    // id - string

    const idTd = document.createElement('td');
    idTd.textContent = data.id;
    tr.appendChild(idTd);

    // insert :: macro.browser1_to_table_row(model.fields)
    // macro :: browser1_to_table_row_bool :: {"single_bool": "field"}
    //
    // single_bool - bool
    //

    const single_boolTd = document.createElement('td');
    single_boolTd.textContent = (data.single_bool) ? 'yes' : 'no';
    tr.appendChild(single_boolTd);

    // macro :: browser1_to_table_row_int :: {"single_int": "field"}
    // 
    // single_int - int
    //

    const single_intTd = document.createElement('td');
    single_intTd.textContent = data.single_int;
    tr.appendChild(single_intTd);

    // macro :: browser1_to_table_row_float :: {"single_float": "field"}
    //
    // single_float - float
    //

    const single_floatTd = document.createElement('td');
    single_floatTd.textContent = data.single_float;
    tr.appendChild(single_floatTd);

    // macro :: browser1_to_table_row_str :: {"single_string": "field"}
    //
    // single_string - str
    //

    const single_stringTd = document.createElement('td');
    single_stringTd.textContent = data.single_string;
    tr.appendChild(single_stringTd);

    // macro :: browser1_to_table_row_str_enum :: {"single_enum": "field"}
    //
    // single_enum - enum
    //

    const single_enumTd = document.createElement('td');
    single_enumTd.textContent = data.single_enum;
    tr.appendChild(single_enumTd);

    // macro :: browser1_to_table_row_datetime :: {"single_datetime": "field"}
    //
    // single_datetime - datetime
    //
    
    const single_datetimeTd = document.createElement('td');
    single_datetimeTd.textContent = data.single_datetime.toISOString().split('.')[0];
    tr.appendChild(single_datetimeTd);
    // end macro ::

    return tr;

}

function singleModelListToDisplayTBody(singleModelList, tbody) {

    tbody.innerHTML = '';

    for (const singleModel of singleModelList) {
        tbody.appendChild(singleModelToTableRow(singleModel));
    }

    return tbody;

}

//
// serialize functions
//

function singleModelForJSON(data) {
    // convert an items types to be ready to JSON

    let result = {}
    for (const field in data) {
        if (Object.prototype.toString.call(data[field]) === '[object Date]') {
            result[field] = data[field].toISOString().split('.')[0];
        }else if (Array.isArray(data[field])) {
            result[field] = data[field].map((item) => {
                if (Object.prototype.toString.call(item) === '[object Date]') {
                    return item.toISOString().split('.')[0];
                }else{
                    return item;
                }
            });
        }else{
            result[field] = data[field];
        }
    }
    return result;
}

//
// client functions
//

function clientCreateSingleModel(data) {
    
    return fetch('/api/template-module/single-model', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
}

function clientReadSingleModel(id) {

    return fetch(`/api/template-module/single-model/${id}`, {
        method: 'GET',
    })
}

function clientUpdateSingleModel(id, data) {

    return fetch(`/api/template-module/single-model/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })

}

function clientDeleteSingleModel(id) {

    return fetch(`/api/template-module/single-model/${id}`, {
        method: 'DELETE',
    })

}

function clientListSingleModels(offset, size) {

    return fetch(`/api/template-module/single-model?offset=${offset}&size=${size}`, {
        method: 'GET',
    })
}