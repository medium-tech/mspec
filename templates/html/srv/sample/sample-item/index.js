// vars :: {"SampleItem": "model.PascalCase", "sampleItem": "model.camelCase", "sample-item": "model.kebab_case"}

//
// data functions
//

const defaultSampleItem = {
    name: '',
    verified: false,
    color: 'red',
    age: 42,
    score: 9.9,
    tags: []
}

function randomSampleItem() {
    return {
        // macro :: html_random_string :: {"name": "field"}
        name: randomString(),
        // macro :: html_random_boolean :: {"verified": "field"}
        verified: randomBool(),
        // macro :: html_random_enum :: {"color": "field", "['red', 'green', 'blue']": "enum_value_list"}
        color: randomEnum(['red', 'green', 'blue']),
        // macro :: html_random_integer :: {"age": "field"}
        age: randomInt(),
        // macro :: html_random_float :: {"score": "field"}
        score: randomFloat(),
        // macro :: html_random_list :: {"tags": "field"}
        tags: randomList()
        // end macro ::
        // insert :: model.html_random_fields
    }
}

function verifySampleItem(data) {

    let result = {
        valid: true,
        errors: {}
    }

    // macro :: html_verify_string :: {"name": "field"}
    if (typeof data.name !== 'string') {
        result.error.name = 'name must be a string';
        result.valid = false;
    }

    // macro :: html_verify_boolean :: {"verified": "field"}
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

    // macro :: html_verify_integer :: {"age": "field"}
    if (!Number.isInteger(data.age)) {
        result.error.age = 'age must be an integer';
        result.valid = false;
    }

    // macro :: html_verify_float :: {"score": "field"}
    if (typeof data.score !== 'number') {
        result.error.score = 'score must be a float';
        result.valid = false;
    }

    // macro :: html_verify_list :: {"tags": "field"}
    if (!Array.isArray(data.tags)) {
        result.error.tags = 'tags must be an array';
        result.valid = false;
    }else if (data.tags.some(tag => typeof tag !== 'string')) {
        result.error.tags = 'tags must be an array of strings';
        result.valid = false;
    }
    // end macro ::
    // insert :: model.html_verify_fields

    return result

}

function sampleItemFromInputTBody(tbody) {   
    const data = {};

    // macro :: html_from_input_tbody_string :: {"name": "field"}
    const nameInput = tbody.querySelector('input[name="name"]');
    data.name = nameInput.value;

    // macro :: html_from_input_tbody_boolean :: {"verified": "field"}
    const verifiedInput = tbody.querySelector('input[name="verified"]');
    data.verified = verifiedInput.checked;

    // macro :: html_from_input_tbody_enum :: {"color": "field"}
    const colorInput = tbody.querySelector('select[name="color"]');
    data.color = colorInput.value;

    // macro :: html_from_input_tbody_integer :: {"age": "field"}
    const ageInput = tbody.querySelector('input[name="age"]');
    data.age = parseInt(ageInput.value);

    // macro :: html_from_input_tbody_float :: {"score": "field"}
    const scoreInput = tbody.querySelector('input[name="score"]');
    data.score = parseFloat(scoreInput.value);

    // macro :: html_from_input_tbody_list :: {"tags": "field"}
    const tagsInput = tbody.querySelector('input[name="tags"]');
    data.tags = JSON.parse(tagsInput.getAttribute('valueAsJSON'));
    // end macro ::
    // insert :: model.html_from_input_tbody_fields

    return data;
}

function sampleItemToInputTBody(data, tbody) {
    tbody.innerHTML = '';

    // macro :: html_to_input_tbody_string :: {"name": "field"}
    const nameTdKey = document.createElement('td');
    nameTdKey.textContent = 'name';

    const nameTdInput = document.createElement('td');
    const nameInput = document.createElement('input');
    nameInput.name = 'name';
    nameInput.value = data.name;
    nameInput.size = 35;
    nameTdInput.appendChild(nameInput);

    const nameTdOther = document.createElement('td');
    nameTdOther.textContent = '-';

    const nameTr = document.createElement('tr');
    nameTr.appendChild(nameTdKey);
    nameTr.appendChild(nameTdInput);
    nameTr.appendChild(nameTdOther);

    tbody.appendChild(nameTr);

    // macro :: html_to_input_tbody_boolean :: {"verified": "field"}
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

    // macro :: html_to_input_tbody_integer :: {"age": "field"}
    const ageTdKey = document.createElement('td');
    ageTdKey.textContent = 'age';

    const ageTdInput = document.createElement('td');
    const ageInput = document.createElement('input');
    ageInput.name = 'age';
    ageInput.type = 'number';
    ageInput.size = 5;
    ageInput.value = data.age;
    ageTdInput.appendChild(ageInput);

    const ageTdOther = document.createElement('td');
    ageTdOther.textContent = '-';

    const ageTr = document.createElement('tr');
    ageTr.appendChild(ageTdKey);
    ageTr.appendChild(ageTdInput);
    ageTr.appendChild(ageTdOther);

    tbody.appendChild(ageTr);

    // macro :: html_to_input_tbody_float :: {"score": "field"}
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

    // macro :: html_to_input_tbody_list :: {"tags": "field"}
    let tagsEntered = data.tags.slice();

    const tagsTdKey = document.createElement('td');
    tagsTdKey.textContent = 'tags';

    const tagsTdInput = document.createElement('td');
    
    const tagsInput = document.createElement('input');
    tagsInput.name = 'tags';
    tagsInput.value = '';
    tagsInput.size = 35;
    // we store the actual data on valueAsJSON because we can't store an array in an input value with escaping 
    // and also so we can reset the input between each tag entered
    tagsInput.setAttribute('valueAsJSON', JSON.stringify(tagsEntered));
    tagsInput.placeholder = 'press enter after each tag';

    const tagsTdOther = document.createElement('td');
    const renderTags = () => {
        tagsTdOther.innerHTML = '';
        let index = 0;
    
        for (const tag of tagsEntered) {
            const tagLink = document.createElement('a');
            tagLink.innerHTML = tag;
            tagLink.onclick = () => {
                console.log('removing tag', tag);
                tagsEntered = tagsEntered.filter(t => t !== tag);
                tagsInput.setAttribute('valueAsJSON', JSON.stringify(tagsEntered));
                renderTags();
            }
            const tagSpacer = document.createElement('span');
            tagSpacer.innerHTML = ', ';

            tagsTdOther.appendChild(tagLink);

            if (index < tagsEntered.length - 1) tagsTdOther.appendChild(tagSpacer);
            index++;
        }
    }

    renderTags();

    tagsInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            tagsEntered.push(tagsInput.value);
            tagsInput.value = ''
            tagsInput.setAttribute('valueAsJSON', JSON.stringify(tagsEntered));
            renderTags();
        }
    });

    tagsTdInput.appendChild(tagsInput);

    const tagsTr = document.createElement('tr');
    tagsTr.appendChild(tagsTdKey);
    tagsTr.appendChild(tagsTdInput);
    tagsTr.appendChild(tagsTdOther);

    tbody.appendChild(tagsTr);
    // end macro ::
    // insert :: model.html_to_input_tbody_fields

    return tbody;

}

function sampleItemToDisplayTBody(data, tbody) {
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

    // macro :: html_to_display_tbody_string :: {"name": "field"}
    const nameTdKey = document.createElement('td');
    nameTdKey.textContent = 'name';

    const nameTdValue = document.createElement('td');
    nameTdValue.textContent = data.name;

    const nameTr = document.createElement('tr');
    nameTr.appendChild(nameTdKey);
    nameTr.appendChild(nameTdValue);

    tbody.appendChild(nameTr);

    // macro :: html_to_display_tbody_boolean :: {"verified": "field"}
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

    // macro :: html_to_display_tbody_integer :: {"age": "field"}
    const ageTdKey = document.createElement('td');
    ageTdKey.textContent = 'age';

    const ageTdValue = document.createElement('td');
    ageTdValue.textContent = data.age;

    const ageTr = document.createElement('tr');
    ageTr.appendChild(ageTdKey);
    ageTr.appendChild(ageTdValue);

    tbody.appendChild(ageTr);

    // macro :: html_to_display_tbody_float :: {"score": "field"}
    const scoreTdKey = document.createElement('td');
    scoreTdKey.textContent = 'score';

    const scoreTdValue = document.createElement('td');
    scoreTdValue.textContent = data.score;
    
    const scoreTr = document.createElement('tr');
    scoreTr.appendChild(scoreTdKey);
    scoreTr.appendChild(scoreTdValue);

    tbody.appendChild(scoreTr);

    // macro :: html_to_display_tbody_list :: {"tags": "field"}
    const tagsTdKey = document.createElement('td');
    tagsTdKey.textContent = 'tags';

    const tagsTdValue = document.createElement('td');
    tagsTdValue.textContent = data.tags.join(', ');

    const tagsTr = document.createElement('tr');
    tagsTr.appendChild(tagsTdKey);
    tagsTr.appendChild(tagsTdValue);

    tbody.appendChild(tagsTr);
    // end macro ::
    // insert :: model.html_to_display_tbody_fields

    return tbody;
}

function sampleItemToTableRow(data) {

    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    tr.onclick = () => window.location.href = `/sample/sample-item/${data.id}`

    // id - string

    const idTd = document.createElement('td');
    idTd.textContent = data.id;
    tr.appendChild(idTd);

    // macro :: html_to_table_row_string :: {"name": "field"}
    const nameTd = document.createElement('td');
    nameTd.textContent = data.name;
    tr.appendChild(nameTd);

    // macro :: html_to_table_row_boolean :: {"verified": "field"}
    const verifiedTd = document.createElement('td');
    verifiedTd.textContent = (data.verified) ? 'yes' : 'no';
    tr.appendChild(verifiedTd);

    // macro :: html_to_table_row_enum :: {"color": "field"}
    const colorTd = document.createElement('td');
    colorTd.textContent = data.color;
    tr.appendChild(colorTd);

    // macro :: html_to_table_row_integer :: {"age": "field"}
    const ageTd = document.createElement('td');
    ageTd.textContent = data.age;
    tr.appendChild(ageTd);

    // macro :: html_to_table_row_float :: {"score": "field"}
    const scoreTd = document.createElement('td');
    scoreTd.textContent = data.score;
    tr.appendChild(scoreTd);

    // macro :: html_to_table_row_list :: {"tags": "field"}
    const tagsTd = document.createElement('td');
    tagsTd.textContent = data.tags.join(', ');
    tr.appendChild(tagsTd);
    // end macro ::
    // insert :: model.html_to_table_row_fields

    return tr;

}

function sampleItemListToDisplayTBody(sampleItemList, tbody) {

    tbody.innerHTML = '';

    for (const sampleItem of sampleItemList) {
        tbody.appendChild(sampleItemToTableRow(sampleItem));
    }

    return tbody;

}

//
// client functions
//

function clientCreateSampleItem(data) {
    
    return fetch('/api/sample/sample-item', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
}

function clientReadSampleItem(id) {

    return fetch(`/api/sample/sample-item/${id}`, {
        method: 'GET',
    })
}

function clientUpdateSampleItem(id, data) {

    return fetch(`/api/sample/sample-item/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })

}

function clientDeleteSampleItem(id) {

    return fetch(`/api/sample/sample-item/${id}`, {
        method: 'DELETE',
    })

}

function clientListSampleItems(offset, size) {

    return fetch(`/api/sample/sample-item?offset=${offset}&size=${size}`, {
        method: 'GET',
    })
    .then(response => response.json())
}