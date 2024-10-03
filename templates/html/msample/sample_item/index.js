//
// data functions
//

function verifySampleItem(data) {
    /*

    return {
        valid: true/false,
        errors: {
            field: 'error message',
            ...
        }
    }

    */

    let result = {
        valid: true,
        errors: {}
    }

    // name - string

    if (typeof data.name !== 'string') {
        result.error.name = 'name must be a string';
        result.valid = false;
    }

    // verified - boolean

    if (typeof data.verified !== 'boolean') {
        result.error.verified = 'verified must be a boolean';
        result.valid = false;
    }

    // color - string enum (red, green, blue)

    if (typeof data.color !== 'string') {
        result.error.color = 'color must be a string';
        result.valid = false;
    }else if (!['red', 'green', 'blue'].includes(data.color)) {
        result.error.color = 'invalid color';
        result.valid = false;
    }

    // age - integer

    if (!Number.isInteger(data.age)) {
        result.error.age = 'age must be an integer';
        result.valid = false;
    }

    // score - float

    if (typeof data.score !== 'number') {
        result.error.score = 'score must be a float';
        result.valid = false;
    }

    // tags - array of strings

    if (!Array.isArray(data.tags)) {
        result.error.tags = 'tags must be an array';
        result.valid = false;
    }else if (data.tags.some(tag => typeof tag !== 'string')) {
        result.error.tags = 'tags must be an array of strings';
        result.valid = false;
    }

    return result

}

function sampleItemFromInputTBody(tbody) {   
    const data = {};

    // name - string

    const nameInput = tbody.querySelector('input[name="name"]');
    data.name = nameInput.value;

    // verified - boolean

    const verifiedInput = tbody.querySelector('input[name="verified"]');
    data.verified = verifiedInput.checked;

    // color - string enum (red, green, blue)

    const colorInput = tbody.querySelector('select[name="color"]');
    data.color = colorInput.value;

    // age - integer

    const ageInput = tbody.querySelector('input[name="age"]');
    data.age = parseInt(ageInput.value);

    // score - float

    const scoreInput = tbody.querySelector('input[name="score"]');
    data.score = parseFloat(scoreInput.value);

    // tags - array of strings

    const tagsInput = tbody.querySelector('input[name="tags"]');
    data.tags = tagsInput.value.split(',').map(tag => tag.trim());

    return data;
}

function sampleItemToInputTBody(data, tbody) {
    tbody.innerHTML = '';

    // name - string

    const nameTdKey = document.createElement('td');
    nameTdKey.textContent = 'name';

    const nameTdInput = document.createElement('td');
    const nameInput = document.createElement('input');
    nameInput.name = 'name';
    nameInput.value = data.name;
    nameTdInput.appendChild(nameInput);

    const nameTr = document.createElement('tr');
    nameTr.appendChild(nameTdKey);
    nameTr.appendChild(nameTdInput);

    tbody.appendChild(nameTr);

    // verified - boolean

    const verifiedTdKey = document.createElement('td');
    verifiedTdKey.textContent = 'verified';

    const verifiedTdInput = document.createElement('td');
    const verifiedInput = document.createElement('input');
    verifiedInput.name = 'verified';
    verifiedInput.type = 'checkbox';
    verifiedInput.checked = data.verified;
    verifiedTdInput.appendChild(verifiedInput);

    const verifiedTr = document.createElement('tr');
    verifiedTr.appendChild(verifiedTdKey);
    verifiedTr.appendChild(verifiedTdInput);

    tbody.appendChild(verifiedTr);

    // color - string enum (red, green, blue)

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

    const colorTr = document.createElement('tr');
    colorTr.appendChild(colorTdKey);
    colorTr.appendChild(colorTdInput);

    tbody.appendChild(colorTr);

    // age - integer

    const ageTdKey = document.createElement('td');
    ageTdKey.textContent = 'age';

    const ageTdInput = document.createElement('td');
    const ageInput = document.createElement('input');
    ageInput.name = 'age';
    ageInput.type = 'number';
    ageInput.value = data.age;
    ageTdInput.appendChild(ageInput);

    const ageTr = document.createElement('tr');
    ageTr.appendChild(ageTdKey);
    ageTr.appendChild(ageTdInput);

    tbody.appendChild(ageTr);

    // score - float

    const scoreTdKey = document.createElement('td');
    scoreTdKey.textContent = 'score';

    const scoreTdInput = document.createElement('td');
    const scoreInput = document.createElement('input');
    scoreInput.name = 'score';
    scoreInput.type = 'number';
    scoreInput.value = data.score;
    scoreInput.step = '.01';
    scoreTdInput.appendChild(scoreInput);

    const scoreTr = document.createElement('tr');
    scoreTr.appendChild(scoreTdKey);
    scoreTr.appendChild(scoreTdInput);

    tbody.appendChild(scoreTr);

    // tags - array of strings

    const tagsTdKey = document.createElement('td');
    tagsTdKey.textContent = 'tags';

    const tagsTdInput = document.createElement('td');
    const tagsInput = document.createElement('input');
    tagsInput.name = 'tags';
    tagsInput.value = data.tags.join(', ');
    tagsTdInput.appendChild(tagsInput);

    const tagsTr = document.createElement('tr');
    tagsTr.appendChild(tagsTdKey);

    tbody.appendChild(tagsTr);

    return tbody;

}

function sampleItemToDisplayTBody(data, tbody) {
    tbody.innerHTML = '';

    // name - string

    const nameTdKey = document.createElement('td');
    nameTdKey.textContent = 'name';

    const nameTdValue = document.createElement('td');
    nameTdValue.textContent = data.name;

    const nameTr = document.createElement('tr');
    nameTr.appendChild(nameTdKey);
    nameTr.appendChild(nameTdValue);

    tbody.appendChild(nameTr);

    // verified - boolean

    const verifiedTdKey = document.createElement('td');
    verifiedTdKey.textContent = 'verified';

    const verifiedTdValue = document.createElement('td');
    verifiedTdValue.textContent = (data.verified) ? 'yes' : 'no';

    const verifiedTr = document.createElement('tr');
    verifiedTr.appendChild(verifiedTdKey);
    verifiedTr.appendChild(verifiedTdValue);

    tbody.appendChild(verifiedTr);

    // color - string enum (red, green, blue)

    const colorTdKey = document.createElement('td');
    colorTdKey.textContent = 'color';

    const colorTdValue = document.createElement('td');
    colorTdValue.textContent = data.color;

    const colorTr = document.createElement('tr');
    colorTr.appendChild(colorTdKey);
    colorTr.appendChild(colorTdValue);

    tbody.appendChild(colorTr);

    // age - integer

    const ageTdKey = document.createElement('td');
    ageTdKey.textContent = 'age';

    const ageTdValue = document.createElement('td');
    ageTdValue.textContent = data.age;

    const ageTr = document.createElement('tr');
    ageTr.appendChild(ageTdKey);
    ageTr.appendChild(ageTdValue);

    tbody.appendChild(ageTr);

    // score - float

    const scoreTdKey = document.createElement('td');
    scoreTdKey.textContent = 'score';

    const scoreTdValue = document.createElement('td');
    scoreTdValue.textContent = data.score;
    
    const scoreTr = document.createElement('tr');
    scoreTr.appendChild(scoreTdKey);
    scoreTr.appendChild(scoreTdValue);

    tbody.appendChild(scoreTr);

    // tags - array of strings

    const tagsTdKey = document.createElement('td');
    tagsTdKey.textContent = 'tags';

    const tagsTdValue = document.createElement('td');
    tagsTdValue.textContent = data.tags.join(', ');

    const tagsTr = document.createElement('tr');
    tagsTr.appendChild(tagsTdKey);
    tagsTr.appendChild(tagsTdValue);

    tbody.appendChild(tagsTr);

    return tbody;
}

function sampleItemToTableRow(data) {

    const tr = document.createElement('tr');

    // id - string

    const idTd = document.createElement('td');
    idTd.textContent = data.id;
    tr.appendChild(idTd);

    // name - string

    const nameTd = document.createElement('td');
    nameTd.textContent = data.name;
    tr.appendChild(nameTd);

    // verified - boolean

    const verifiedTd = document.createElement('td');
    verifiedTd.textContent = (data.verified) ? 'yes' : 'no';
    tr.appendChild(verifiedTd);

    // color - string enum (red, green, blue)

    const colorTd = document.createElement('td');
    colorTd.textContent = data.color;
    tr.appendChild(colorTd);

    // age - integer

    const ageTd = document.createElement('td');
    ageTd.textContent = data.age;
    tr.appendChild(ageTd);

    // score - float

    const scoreTd = document.createElement('td');
    scoreTd.textContent = data.score;
    tr.appendChild(scoreTd);

    // tags - array of strings

    const tagsTd = document.createElement('td');
    tagsTd.textContent = data.tags.join(', ');
    tr.appendChild(tagsTd);

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

function createSampleItem(data) {
    
    return fetch('/api/sample/sample-item', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
}

function readSampleItem(id) {

    return fetch(`/api/sample/sample-item/${id}`, {
        method: 'GET',
    })
    .then(response => response.json())
}

function updateSampleItem(id, data) {

    return fetch(`/api/sample/sample-item/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })

}

function deleteSampleItem(id) {

    return fetch(`/api/sample/sample-item/${id}`, {
        method: 'DELETE',
    })

}

function listSampleItems(offset, size) {

    return fetch(`/api/sample/sample-item?offset=${offset}&size=${size}`, {
        method: 'GET',
    })
    .then(response => response.json())
}