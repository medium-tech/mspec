// vars :: {"sample-module": "module.name.kebab_case"}
// vars :: {"ExampleItem": "model.name.pascal_case", "exampleItem": "model.name.camel_case", "example-item": "model.name.kebab_case"}

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
// data functions
//

function initExampleItem(data) {
    let result = {
        // macro :: html_init_str :: {"description": "field"}
        description: data.description,
        // macro :: html_init_bool :: {"verified": "field"}
        verified: data.verified,
        // macro :: html_init_enum :: {"color": "field"}
        color: data.color,
        // macro :: html_init_int :: {"count": "field"}
        count: data.count,
        // macro :: html_init_float :: {"score": "field"}
        score: data.score,
        // macro :: html_init_list :: {"stuff": "field"}
        stuff: data.stuff,
        // macro :: html_init_datetime :: {"when": "field"}
        when: new Date(data.when),
        // end macro ::
        // insert :: macro.html_init_fields(model.fields)
    }

    if (typeof data.id !== 'undefined') {
        result.id = data.id;
    }
    return result;
}

function exampleExampleItem() {
    const data = {
        description: '',
        verified: false,
        color: 'red',
        count: 42,
        score: 9.9,
        stuff: ['mountain', 'river', 'forest'],
        when: new Date()
    }
    return {...data}
}

function randomExampleItem() {
    return {
        // macro :: html_random_str :: {"description": "field"}
        description: randomStr(),
        // macro :: html_random_bool :: {"verified": "field"}
        verified: randomBool(),
        // macro :: html_random_enum :: {"color": "field", "['red', 'green', 'blue']": "enum_value_list"}
        color: randomStrEnum(['red', 'green', 'blue']),
        // macro :: html_random_int :: {"count": "field"}
        count: randomInt(),
        // macro :: html_random_float :: {"score": "field"}
        score: randomFloat(),
        // macro :: html_random_list :: {"stuff": "field"}
        stuff: randomList(),
        // macro :: html_random_datetime :: {"when": "field"}
        when: randomDatetime()
        // end macro ::
        // insert :: macro.html_random_fields(model.fields)
    }
}

function verifyExampleItem(data) {

    let result = {
        valid: true,
        errors: {}
    }

    // macro :: html_verify_str :: {"description": "field"}
    if (typeof data.description !== 'string') {
        result.error.description = 'description must be a string';
        result.valid = false;
    }

    // macro :: html_verify_bool :: {"verified": "field"}
    if (typeof data.verified !== 'boolean') {
        result.error.verified = 'verified must be a boolean';
        result.valid = false;
    }

    // macro :: html_verify_enum :: {"color": "field", "['red', 'green', 'blue']": "enum_value_list"}
    if (typeof data.color !== 'string') {
        result.error.color = 'color must be a string';
        result.valid = false;
    }else if (!['red', 'green', 'blue'].includes(data.color)) {
        result.error.color = 'invalid color';
        result.valid = false;
    }

    // macro :: html_verify_int :: {"count": "field"}
    if (!Number.isInteger(data.count)) {
        result.error.count = 'count must be an integer';
        result.valid = false;
    }

    // macro :: html_verify_float :: {"score": "field"}
    if (typeof data.score !== 'number') {
        result.error.score = 'score must be a float';
        result.valid = false;
    }

    // macro :: html_verify_list :: {"stuff": "field", "string": "element_type"}
    if (!Array.isArray(data.stuff)) {
        result.error.stuff = 'stuff must be an array';
        result.valid = false;
    }else if (data.stuff.some(tag => typeof tag !== 'string')) {
        result.error.stuff = 'stuff must be an array with element type: string';
        result.valid = false;
    }

    // macro :: html_verify_datetime :: {"when": "field"}
    if (Object.prototype.toString.call(data.when) !== '[object Date]') {
        result.error.when = 'when must be a datetime';
        result.valid = false;
    }
    // end macro ::
    // insert :: macro.html_verify_fields(model.fields)

    return result

}

function exampleItemFromInputTBody(tbody) {   
    const data = {};

    // parse id if exists

    const idInput = tbody.querySelector('input[name="id"]');
    if (idInput) {
        data.id = idInput.value;
    }

    // macro :: html_from_input_tbody_str :: {"description": "field"}
    const descriptionInput = tbody.querySelector('input[name="description"]');
    data.description = descriptionInput.value;

    // macro :: html_from_input_tbody_bool :: {"verified": "field"}
    const verifiedInput = tbody.querySelector('input[name="verified"]');
    data.verified = verifiedInput.checked;

    // macro :: html_from_input_tbody_enum :: {"color": "field"}
    const colorInput = tbody.querySelector('select[name="color"]');
    data.color = colorInput.value;

    // macro :: html_from_input_tbody_int :: {"count": "field"}
    const countInput = tbody.querySelector('input[name="count"]');
    data.count = parseInt(countInput.value);

    // macro :: html_from_input_tbody_float :: {"score": "field"}
    const scoreInput = tbody.querySelector('input[name="score"]');
    data.score = parseFloat(scoreInput.value);

    // macro :: html_from_input_tbody_list :: {"stuff": "field"}
    const stuffInput = tbody.querySelector('input[name="stuff"]');
    data.stuff = JSON.parse(stuffInput.getAttribute('valueAsJSON'));

    // macro :: html_from_input_tbody_datetime :: {"when": "field"}
    const whenInput = tbody.querySelector('input[name="when"]');
    data.when = new Date(whenInput.value);

    // end macro ::
    // insert :: macro.html_from_input_tbody_fields(model.fields)

    return data;
}

function exampleItemToInputTBody(data, tbody) {
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

    // description - str
    const descriptionTdKey = document.createElement('td');
    descriptionTdKey.textContent = 'description';

    const descriptionTdInput = document.createElement('td');
    const descriptionInput = document.createElement('input');
    descriptionInput.name = 'description';
    descriptionInput.value = data.description || '';
    descriptionInput.size = 35;
    descriptionTdInput.appendChild(descriptionInput);

    const descriptionTdOther = document.createElement('td');
    descriptionTdOther.textContent = '-';

    const descriptionTr = document.createElement('tr');
    descriptionTr.appendChild(descriptionTdKey);
    descriptionTr.appendChild(descriptionTdInput);
    descriptionTr.appendChild(descriptionTdOther);

    tbody.appendChild(descriptionTr);

    // macro :: html_to_input_tbody_bool :: {"verified": "field"}

    // verified - bool

    const verifiedTdKey = document.createElement('td');
    verifiedTdKey.textContent = 'verified';

    const verifiedTdInput = document.createElement('td');
    const verifiedInput = document.createElement('input');
    verifiedInput.name = 'verified';
    verifiedInput.type = 'checkbox';
    verifiedInput.checked = data.verified;
    verifiedTdInput.appendChild(verifiedInput);

    const verifiedTdOther = document.createElement('td');
    verifiedTdOther.textContent = '-';

    const verifiedTr = document.createElement('tr');
    verifiedTr.appendChild(verifiedTdKey);
    verifiedTr.appendChild(verifiedTdInput);
    verifiedTr.appendChild(verifiedTdOther);

    tbody.appendChild(verifiedTr);

    // macro :: html_to_input_tbody_enum :: {"color": "field"}

    // color - enum

    const colorTdKey = document.createElement('td');
    colorTdKey.textContent = 'color';

    const colorTdInput = document.createElement('td');
    const colorInput = document.createElement('select');
    colorInput.name = 'color';
    const colorOptions = ['red', 'green', 'blue'];
    for (const option of colorOptions) {
        const colorOption = document.createElement('option');
        colorOption.value = option;
        colorOption.textContent = option;
        if (option === data.color) {
            colorOption.selected = true;
        }
        colorInput.appendChild(colorOption);
    }
    colorTdInput.appendChild(colorInput);

    const colorTdOther = document.createElement('td');
    colorTdOther.textContent = '-';

    const colorTr = document.createElement('tr');
    colorTr.appendChild(colorTdKey);
    colorTr.appendChild(colorTdInput);
    colorTr.appendChild(colorTdOther);

    tbody.appendChild(colorTr);

    // macro :: html_to_input_tbody_int :: {"count": "field"}

    // count - int

    const countTdKey = document.createElement('td');
    countTdKey.textContent = 'count';

    const countTdInput = document.createElement('td');
    const countInput = document.createElement('input');
    countInput.name = 'count';
    countInput.type = 'number';
    countInput.size = 5;
    countInput.value = data.count;
    countTdInput.appendChild(countInput);

    const countTdOther = document.createElement('td');
    countTdOther.textContent = '-';

    const countTr = document.createElement('tr');
    countTr.appendChild(countTdKey);
    countTr.appendChild(countTdInput);
    countTr.appendChild(countTdOther);

    tbody.appendChild(countTr);

    // macro :: html_to_input_tbody_float :: {"score": "field"}

    // score - float

    const scoreTdKey = document.createElement('td');
    scoreTdKey.textContent = 'score';

    const scoreTdInput = document.createElement('td');
    const scoreInput = document.createElement('input');
    scoreInput.name = 'score';
    scoreInput.type = 'number';
    scoreInput.size = 5;
    scoreInput.value = parseFloat(data.score).toFixed(2);
    scoreInput.step = '.01';
    scoreTdInput.appendChild(scoreInput);

    const scoreTdOther = document.createElement('td');
    scoreTdOther.textContent = '-';

    const scoreTr = document.createElement('tr');
    scoreTr.appendChild(scoreTdKey);
    scoreTr.appendChild(scoreTdInput);
    scoreTr.appendChild(scoreTdOther);

    tbody.appendChild(scoreTr);

    // macro :: html_to_input_tbody_list :: {"stuff": "field", "Str": "element_type_capitalized"}

    // stuff - list

    let stuffEntered;

    try {
        stuffEntered = data.stuff.slice()
    }catch {
        stuffEntered = [];
    }

    const stuffTdKey = document.createElement('td');
    stuffTdKey.textContent = 'stuff';

    const stuffTdInput = document.createElement('td');
    
    const stuffInput = document.createElement('input');
    stuffInput.name = 'stuff';
    stuffInput.value = '';
    stuffInput.size = 35;
    // we store the actual data on valueAsJSON because we can't store an array in an input value with escaping 
    // and also so we can reset the input between each tag entered
    stuffInput.setAttribute('valueAsJSON', JSON.stringify(stuffEntered));
    stuffInput.placeholder = 'press enter after each item';

    const stuffTdOther = document.createElement('td');
    const stuffEntriesRender = () => {
        stuffTdOther.innerHTML = '';
        let index = 0;
    
        for (const tag of stuffEntered) {
            const tagLink = document.createElement('a');
            tagLink.innerHTML = tag;
            tagLink.onclick = () => {
                console.log('removing tag', tag);
                stuffEntered = stuffEntered.filter(t => t !== tag);
                stuffInput.setAttribute('valueAsJSON', JSON.stringify(stuffEntered));
                stuffEntriesRender();
            }
            const tagSpacer = document.createElement('span');
            tagSpacer.innerHTML = ', ';

            stuffTdOther.appendChild(tagLink);

            if (index < stuffEntered.length - 1) stuffTdOther.appendChild(tagSpacer);
            index++;
        }
    }

    stuffEntriesRender();

    stuffInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            stuffEntered.push(convertListElementStr(stuffInput.value));
            stuffInput.value = ''
            stuffInput.setAttribute('valueAsJSON', JSON.stringify(stuffEntered));
            stuffEntriesRender();
        }
    });

    stuffTdInput.appendChild(stuffInput);

    const stuffTr = document.createElement('tr');
    stuffTr.appendChild(stuffTdKey);
    stuffTr.appendChild(stuffTdInput);
    stuffTr.appendChild(stuffTdOther);

    tbody.appendChild(stuffTr);

    // macro :: html_to_input_tbody_datetime :: {"when": "field"}

    // when - datetime

    const whenTdKey = document.createElement('td');
    whenTdKey.textContent = 'when';

    const whenTdInput = document.createElement('td');
    const whenInput = document.createElement('input');
    whenInput.name = 'when';
    whenInput.type = 'datetime-local';
    try {
        whenInput.value = data.when.toISOString().split('.')[0].slice(0, 16);
    }catch {
        whenInput.value = '';
    }
    whenTdInput.appendChild(whenInput);

    const whenTdOther = document.createElement('td');
    whenTdOther.textContent = '-';

    const whenTr = document.createElement('tr');
    whenTr.appendChild(whenTdKey);
    whenTr.appendChild(whenTdInput);
    whenTr.appendChild(whenTdOther);

    tbody.appendChild(whenTr);
    // end macro ::
    // insert :: macro.html_to_input_tbody(model.fields)

    return tbody;

}

function exampleItemToDisplayTBody(data, tbody) {
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
    const descriptionTdKey = document.createElement('td');
    descriptionTdKey.textContent = 'description';

    const descriptionTdValue = document.createElement('td');
    descriptionTdValue.textContent = data.description;

    const descriptionTr = document.createElement('tr');
    descriptionTr.appendChild(descriptionTdKey);
    descriptionTr.appendChild(descriptionTdValue);

    tbody.appendChild(descriptionTr);

    // macro :: html_to_display_tbody_bool :: {"verified": "field"}
    const verifiedTdKey = document.createElement('td');
    verifiedTdKey.textContent = 'verified';

    const verifiedTdValue = document.createElement('td');
    verifiedTdValue.textContent = (data.verified) ? 'yes' : 'no';

    const verifiedTr = document.createElement('tr');
    verifiedTr.appendChild(verifiedTdKey);
    verifiedTr.appendChild(verifiedTdValue);

    tbody.appendChild(verifiedTr);

    // macro :: html_to_display_tbody_enum :: {"color": "field"}
    const colorTdKey = document.createElement('td');
    colorTdKey.textContent = 'color';

    const colorTdValue = document.createElement('td');
    colorTdValue.textContent = data.color;

    const colorTr = document.createElement('tr');
    colorTr.appendChild(colorTdKey);
    colorTr.appendChild(colorTdValue);

    tbody.appendChild(colorTr);

    // macro :: html_to_display_tbody_int :: {"count": "field"}
    const countTdKey = document.createElement('td');
    countTdKey.textContent = 'count';

    const countTdValue = document.createElement('td');
    countTdValue.textContent = data.count;

    const countTr = document.createElement('tr');
    countTr.appendChild(countTdKey);
    countTr.appendChild(countTdValue);

    tbody.appendChild(countTr);

    // macro :: html_to_display_tbody_float :: {"score": "field"}
    const scoreTdKey = document.createElement('td');
    scoreTdKey.textContent = 'score';

    const scoreTdValue = document.createElement('td');
    scoreTdValue.textContent = data.score;
    
    const scoreTr = document.createElement('tr');
    scoreTr.appendChild(scoreTdKey);
    scoreTr.appendChild(scoreTdValue);

    tbody.appendChild(scoreTr);

    // macro :: html_to_display_tbody_list :: {"stuff": "field"}
    const stuffTdKey = document.createElement('td');
    stuffTdKey.textContent = 'stuff';

    const stuffTdValue = document.createElement('td');
    stuffTdValue.textContent = data.stuff.join(', ');

    const stuffTr = document.createElement('tr');
    stuffTr.appendChild(stuffTdKey);
    stuffTr.appendChild(stuffTdValue);

    tbody.appendChild(stuffTr);

    // macro :: html_to_display_tbody_datetime :: {"when": "field"}
    const whenTdKey = document.createElement('td');
    whenTdKey.textContent = 'when';

    const whenTdValue = document.createElement('td');
    whenTdValue.textContent = data.when.toISOString().split('.')[0];

    const whenTr = document.createElement('tr');
    whenTr.appendChild(whenTdKey);
    whenTr.appendChild(whenTdValue);

    tbody.appendChild(whenTr);
    // end macro ::
    // insert :: macro.html_to_display_tbody(model.fields)

    return tbody;
}

function exampleItemToTableRow(data) {

    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    tr.onclick = () => window.location.href = `/sample-module/example-item/${data.id}`

    // id - string

    const idTd = document.createElement('td');
    idTd.textContent = data.id;
    tr.appendChild(idTd);

    // macro :: html_to_table_row_str :: {"description": "field"}
    const descriptionTd = document.createElement('td');
    descriptionTd.textContent = data.description;
    tr.appendChild(descriptionTd);

    // macro :: html_to_table_row_bool :: {"verified": "field"}
    const verifiedTd = document.createElement('td');
    verifiedTd.textContent = (data.verified) ? 'yes' : 'no';
    tr.appendChild(verifiedTd);

    // macro :: html_to_table_row_enum :: {"color": "field"}
    const colorTd = document.createElement('td');
    colorTd.textContent = data.color;
    tr.appendChild(colorTd);

    // macro :: html_to_table_row_int :: {"count": "field"}
    const countTd = document.createElement('td');
    countTd.textContent = data.count;
    tr.appendChild(countTd);

    // macro :: html_to_table_row_float :: {"score": "field"}
    const scoreTd = document.createElement('td');
    scoreTd.textContent = data.score;
    tr.appendChild(scoreTd);

    // macro :: html_to_table_row_list :: {"stuff": "field"}
    const stuffTd = document.createElement('td');
    stuffTd.textContent = data.stuff.join(', ');
    tr.appendChild(stuffTd);
    // end macro ::

    // macro :: html_to_table_row_datetime :: {"when": "field"}
    const whenTd = document.createElement('td');
    whenTd.textContent = data.when.toISOString().split('.')[0];
    tr.appendChild(whenTd);
    // end macro ::
    // insert :: macro.html_to_table_row(model.fields)

    return tr;

}

function exampleItemListToDisplayTBody(exampleItemList, tbody) {

    tbody.innerHTML = '';

    for (const exampleItem of exampleItemList) {
        tbody.appendChild(exampleItemToTableRow(exampleItem));
    }

    return tbody;

}

//
// serialize functions
//

function exampleItemForJSON(data) {
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

function clientCreateExampleItem(data) {
    
    return fetch('/api/sample-module/example-item', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
}

function clientReadExampleItem(id) {

    return fetch(`/api/sample-module/example-item/${id}`, {
        method: 'GET',
    })
}

function clientUpdateExampleItem(id, data) {

    return fetch(`/api/sample-module/example-item/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })

}

function clientDeleteExampleItem(id) {

    return fetch(`/api/sample-module/example-item/${id}`, {
        method: 'DELETE',
    })

}

function clientListExampleItems(offset, size) {

    return fetch(`/api/sample-module/example-item?offset=${offset}&size=${size}`, {
        method: 'GET',
    })
}