const randomNouns = ['apple', 'banana', 'horse', 'iguana', 'jellyfish', 'kangaroo', 'lion', 'quail', 'rabbit', 'snake', 'tiger', 'x-ray', 'yak', 'zebra']
const randomAdjectives = ['shiny', 'dull', 'new', 'old', 'big', 'small', 'fast', 'slow', 'hot', 'cold', 'happy', 'sad', 'angry', 'calm', 'loud', 'quiet']
const randomWords = randomNouns.concat(randomAdjectives)

const randomFirstNames = ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Hank', 'Ivy', 'Jack', 'Kathy', 'Larry', 'Molly', 'Nancy', 'Oscar', 'Peggy', 'Quincy', 'Randy', 'Sally', 'Tom', 'Ursula', 'Victor', 'Wendy', 'Xander', 'Yvonne', 'Zack']
const randomLastNames = ['Adams', 'Brown', 'Clark', 'Davis', 'Evans', 'Ford', 'Garcia', 'Hill', 'Irwin', 'Jones', 'King', 'Lee', 'Moore', 'Nolan', 'Owens', 'Perez', 'Quinn', 'Reed', 'Smith', 'Taylor', 'Upton', 'Vance', 'Wong', 'Xu', 'Young', 'Zhang']

function randomBool() {
    return Math.random() < 0.5
}

function randomInt(min, max) {

    if (min === undefined) {
        min = -100
    }
    if (max === undefined) {
        max = 100
    }

    return Math.floor(Math.random() * (max - min + 1)) + min
}

function randomFloat(min, max) {

    if (min === undefined) {
        min = -100
    }
    if (max === undefined) {
        max = 100
    }

    return Math.random() * (max - min) + min
}

function randomString() {
    const max = randomInt(1, 5)
    const words = []
    for (let i = 0; i < max; i++) {
        words.push(randomEnum(randomWords))
    }
    return words.join(' ')
}

function randomEnum(options) {
    return options[Math.floor(Math.random() * options.length)]
}

function randomList() {
    const max = randomInt(1, 5)
    const words = []
    for (let i = 0; i < max; i++) {
        words.push(randomEnum(randomWords))
    }
    return words
}

function randomPersonName() {
    const first = randomEnum(randomFirstNames)
    const middle = randomEnum(randomFirstNames)
    const last = randomEnum(randomLastNames)

    let name = ''

    if (Math.random() < 0.33) {
        name += first
    }else{
        name += first[0]
    }

    const middleSeed = Math.random()
    if (middleSeed < 0.33) {
        name += ' ' + middle
    } else if (middleSeed < 0.66) {
        name += ' ' + middle[0]
    }

    const lastSeed = Math.random()
    if (lastSeed < 0.33) {
        name += ' ' + last
    } else if (lastSeed < 0.66) {
        name += ' ' + last[0]
    }

    return name
}

function randomUserName() {
    const numWordsInName = randomInt(1, 4)
    const nameWords = [];
    if (Math.random() < 0.33) nameWords.push('the');
    for (let i = 0; i < numWordsInName; i++) {
        const nameWord = randomWords[Math.floor(Math.random() * randomWords.length)];
        const nextWord = (Math.random() < 0.3) ? nameWord.toUpperCase() : nameWord;
        nameWords.push(nextWord);
    }
    const nameSep = Math.random() < 0.3 ? '_' : ' ';
    const nameSuffix = Math.random() < 0.3 ? Math.floor(Math.random() * 1000) : '';
    return `${nameWords.join(nameSep)}${nameSuffix}`
}

function randomThingName() {
    const numAdjectives = randomInt(1, 3)
    const adjectives = []
    for (let i = 0; i < numAdjectives; i++) {
        adjectives.push(randomEnum(randomAdjectives))
    }
    const noun = randomEnum(randomNouns)
    return adjectives.join(' ') + ' ' + noun
}