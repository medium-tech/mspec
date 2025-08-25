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

function randomStr() {
    const max = randomInt(1, 5)
    const words = []
    for (let i = 0; i < max; i++) {
        words.push(randomStrEnum(randomWords))
    }
    return words.join(' ')
}

function randomStrEnum(options) {
    return options[Math.floor(Math.random() * options.length)]
}

function randomList(randomElementCallback) {
    const max = randomInt(1, 5)
    const items = []
    for (let i = 0; i < max; i++) {
        items.push(randomElementCallback())
    }
    return [...new Set(items)]
}

function randomDatetime() {
    
    return new Date(
        randomInt(1970, 2030),
        randomInt(0, 11),
        randomInt(1, 27),
        randomInt(0, 23),
        randomInt(0, 59),
        randomInt(0, 59)
    )
}

function random_person_name() {
    const first = randomStrEnum(randomFirstNames)
    const middle = randomStrEnum(randomFirstNames)
    const last = randomStrEnum(randomLastNames)

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

function random_user_name() {
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

function random_thing_name() {
    const numAdjectives = randomInt(1, 3)
    const adjectives = []
    for (let i = 0; i < numAdjectives; i++) {
        adjectives.push(randomStrEnum(randomAdjectives))
    }
    const noun = randomStrEnum(randomNouns)
    return adjectives.join(' ') + ' ' + noun
}

function random_email() {
    const userName = random_user_name().replaceAll(' ', '_');
    const domain = randomStrEnum(randomWords);
    const tld = randomStrEnum(['com', 'net', 'org', 'io', 'co', 'info']);
    return `${userName}@${domain}.${tld}`;
}

function random_phone_number() {
    const countryCode = randomInt(1, 99);
    const areaCode = randomInt(100, 999);
    const exchange = randomInt(100, 999);
    const number = randomInt(1000, 9999);
    return `+${countryCode} (${areaCode}) ${exchange}-${number}`;
}

// User session management functions
function getUserSession() {
    const sessionData = localStorage.getItem('userSession');
    return sessionData ? JSON.parse(sessionData) : null;
}

function setUserSession(sessionData) {
    localStorage.setItem('userSession', JSON.stringify(sessionData));
}

function clearUserSession() {
    localStorage.removeItem('userSession');
}

function isUserLoggedIn() {
    const session = getUserSession();
    return session && session.access_token && session.user;
}

// Get API host - in a real app this would be configured
function getApiHost() {
    return window.location.origin; // Assumes API is on same host
}

// Handle create user form submission
function handleCreateUser(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const userData = {
        name: formData.get('name'),
        email: formData.get('email'),
        password1: formData.get('password1'),
        password2: formData.get('password2')
    };
    
    // Basic client-side validation
    if (userData.password1 !== userData.password2) {
        showMessage('Passwords do not match', 'error');
        return false;
    }
    
    createUser(userData);
    return false;
}

// Create user API call
async function createUser(userData) {
    const messageDiv = document.getElementById('message');
    
    try {
        const response = await fetch(`${getApiHost()}/api/core/user`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData)
        });
        
        if (response.ok) {
            const user = await response.json();
            showMessage('User created successfully! You can now login.', 'success');
            // Clear the form
            document.getElementById('createUserForm').reset();
        } else {
            const error = await response.text();
            showMessage(`Error creating user: ${error}`, 'error');
        }
    } catch (error) {
        showMessage(`Network error: ${error.message}`, 'error');
    }
}

// Handle login form submission
function handleLogin(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const loginData = {
        email: formData.get('email'),
        password: formData.get('password')
    };
    
    loginUser(loginData);
    return false;
}

// Login user API call
async function loginUser(loginData) {
    const messageDiv = document.getElementById('message');
    
    try {
        // Create form data for the login endpoint
        const formData = new URLSearchParams();
        formData.append('email', loginData.email);
        formData.append('password', loginData.password);
        
        const response = await fetch(`${getApiHost()}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        });
        
        if (response.ok) {
            const authData = await response.json();
            
            // Store session data
            const sessionData = {
                access_token: authData.access_token,
                user: loginData.email, // Store user email for now
                loginTime: new Date().toISOString()
            };
            setUserSession(sessionData);
            
            showMessage('Login successful! Redirecting...', 'success');
            // Redirect to home page after a short delay
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        } else {
            const error = await response.text();
            showMessage(`Login failed: ${error}`, 'error');
        }
    } catch (error) {
        showMessage(`Network error: ${error.message}`, 'error');
    }
}

// Logout function
function logoutUser() {
    clearUserSession();
    showMessage('You have been logged out.', 'success');
    // Refresh the page to update UI
    setTimeout(() => {
        window.location.reload();
    }, 1000);
}

// Show message function
function showMessage(message, type) {
    const messageDiv = document.getElementById('message');
    if (messageDiv) {
        messageDiv.innerHTML = `<p class="${type}">${message}</p>`;
    }
}

// Update UI based on login status
function updateUIForLoginStatus() {
    const userButtonsDiv = document.getElementById('userButtons');
    if (!userButtonsDiv) return;
    
    if (isUserLoggedIn()) {
        const session = getUserSession();
        userButtonsDiv.innerHTML = `
            <p>Welcome, ${session.user}!</p>
            <button onclick="window.location.href='/user-account.html'" class="navbar-link">User Account</button>
            <button onclick="logoutUser()" class="navbar-link">Logout</button>
        `;
    } else {
        userButtonsDiv.innerHTML = `
            <button onclick="window.location.href='/create-user.html'" class="navbar-link">Create User</button>
            <button onclick="window.location.href='/login.html'" class="navbar-link">Login</button>
        `;
    }
}

// Initialize UI when page loads
document.addEventListener('DOMContentLoaded', function() {
    updateUIForLoginStatus();
});