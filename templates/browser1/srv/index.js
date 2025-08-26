//
// user session management
//

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

//
// create user
//

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

async function createUser(userData) {
    
    try {
        const response = await fetch(`/api/core/user`, {
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

//
// login/logout
//

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

async function loginUser(loginData) {
    
    try {
        // Create form data for the login endpoint
        const formData = new URLSearchParams();
        formData.append('email', loginData.email);
        formData.append('password', loginData.password);
        
        const response = await fetch(`/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        });
        
        if (response.ok) {
            const authData = await response.json();
            
            // Get current user information to store user_id
            const userResponse = await fetch('/api/auth/me', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${authData.access_token}`
                }
            });
            
            let userId = null;
            if (userResponse.ok) {
                const userData = await userResponse.json();
                userId = userData.id;
            }
            
            // Store session data
            const sessionData = {
                access_token: authData.access_token,
                user: loginData.email,
                user_id: userId,
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

function logoutUser() {
    clearUserSession();
    updateUIForLoginStatus();
    showMessage('You have been logged out. Redirecting to home page...', 'success');
    setTimeout(() => {
        window.location.href = '/';
    }, 1500);
}

// 
// ui
//

function showMessage(message, type) {
    const messageDiv = document.getElementById('message');
    if (messageDiv) {
        messageDiv.innerHTML = `<p class="${type}">${message}</p>`;
    }
}

// enable/disable UI elements based on login status
function updateUIForLoginStatus() {
    const loggedOutButtons = document.getElementById('loggedOutButtons');
    const loggedInButtons = document.getElementById('loggedInButtons');
    const userName = document.getElementById('userName');
    
    if (!loggedOutButtons || !loggedInButtons) return;
    
    if (isUserLoggedIn()) {
        const session = getUserSession();
        loggedOutButtons.hidden = true;
        loggedInButtons.hidden = false;
        if (userName) {
            userName.textContent = session.user;
        }
    } else {
        loggedOutButtons.hidden = false;
        loggedInButtons.hidden = true;
    }
}

// initialize UI when page loads
document.addEventListener('DOMContentLoaded', function() {
    updateUIForLoginStatus();
});

//
// profile management
//

function handleCreateProfile(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    
    // Parse tags and hierarchies from comma-separated strings
    const tagsStr = formData.get('tags') || '';
    const tags = tagsStr ? tagsStr.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
    
    const hierarchiesStr = formData.get('hierarchies') || '';
    const hierarchies = hierarchiesStr ? hierarchiesStr.split(',').map(h => h.trim()).filter(h => h) : [];
    
    // Parse meta data JSON
    let metaData = {};
    const metaDataStr = formData.get('metaData');
    if (metaDataStr && metaDataStr.trim()) {
        try {
            metaData = JSON.parse(metaDataStr);
        } catch (e) {
            showMessage('Invalid JSON format in Additional Data field.', 'error');
            return false;
        }
    }
    
    const session = getUserSession();
    if (!session || !session.user_id) {
        showMessage('User session not found. Please log in again.', 'error');
        return false;
    }
    
    const profileData = {
        name: formData.get('name'),
        bio: formData.get('bio'),
        user_id: session.user_id,
        meta: {
            data: metaData,
            tags: tags,
            hierarchies: hierarchies
        }
    };
    
    createProfile(profileData);
    return false;
}

async function createProfile(profileData) {
    const session = getUserSession();
    if (!session || !session.access_token) {
        showMessage('You must be logged in to create a profile.', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/core/profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${session.access_token}`
            },
            body: JSON.stringify(profileData)
        });
        
        if (response.ok) {
            const profile = await response.json();
            showMessage('Profile created successfully!', 'success');
            setTimeout(() => {
                window.location.href = `/profile/view.html?id=${profile.id}`;
            }, 1500);
        } else {
            const error = await response.text();
            showMessage(`Error creating profile: ${error}`, 'error');
        }
    } catch (error) {
        showMessage(`Network error: ${error.message}`, 'error');
    }
}

function handleEditProfile(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    
    // Parse tags and hierarchies from comma-separated strings
    const tagsStr = formData.get('tags') || '';
    const tags = tagsStr ? tagsStr.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
    
    const hierarchiesStr = formData.get('hierarchies') || '';
    const hierarchies = hierarchiesStr ? hierarchiesStr.split(',').map(h => h.trim()).filter(h => h) : [];
    
    // Parse meta data JSON
    let metaData = {};
    const metaDataStr = formData.get('metaData');
    if (metaDataStr && metaDataStr.trim()) {
        try {
            metaData = JSON.parse(metaDataStr);
        } catch (e) {
            showMessage('Invalid JSON format in Additional Data field.', 'error');
            return false;
        }
    }
    
    const profileData = {
        id: formData.get('profileId'),
        name: formData.get('name'),
        bio: formData.get('bio'),
        user_id: formData.get('userId'),
        meta: {
            data: metaData,
            tags: tags,
            hierarchies: hierarchies
        }
    };
    
    updateProfile(profileData);
    return false;
}

async function updateProfile(profileData) {
    const session = getUserSession();
    if (!session || !session.access_token) {
        showMessage('You must be logged in to update a profile.', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/core/profile/${profileData.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${session.access_token}`
            },
            body: JSON.stringify(profileData)
        });
        
        if (response.ok) {
            showMessage('Profile updated successfully!', 'success');
            setTimeout(() => {
                window.location.href = `/profile/view.html?id=${profileData.id}`;
            }, 1500);
        } else {
            const error = await response.text();
            showMessage(`Error updating profile: ${error}`, 'error');
        }
    } catch (error) {
        showMessage(`Network error: ${error.message}`, 'error');
    }
}

async function loadProfiles() {
    try {
        const offset = currentPage * pageSize;
        const response = await fetch(`/api/core/profile?offset=${offset}&limit=${pageSize}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const profiles = await response.json();
            displayProfiles(profiles);
            updatePaginationButtons();
        } else {
            const error = await response.text();
            showMessage(`Error loading profiles: ${error}`, 'error');
        }
    } catch (error) {
        showMessage(`Network error: ${error.message}`, 'error');
    }
}

function displayProfiles(profiles) {
    const tableBody = document.getElementById('profileTableBody');
    tableBody.innerHTML = '';
    
    profiles.forEach(profile => {
        const row = document.createElement('tr');
        
        const nameCell = document.createElement('td');
        nameCell.textContent = profile.name;
        row.appendChild(nameCell);
        
        const bioCell = document.createElement('td');
        bioCell.textContent = profile.bio ? (profile.bio.length > 50 ? profile.bio.substring(0, 50) + '...' : profile.bio) : '-';
        row.appendChild(bioCell);
        
        const tagsCell = document.createElement('td');
        const tags = profile.meta && profile.meta.tags ? profile.meta.tags.slice(0, 3).join(', ') : '-';
        tagsCell.textContent = tags;
        row.appendChild(tagsCell);
        
        const actionsCell = document.createElement('td');
        actionsCell.innerHTML = `<button onclick="window.location.href='/profile/view.html?id=${profile.id}'" class="navbar-link">View</button>`;
        row.appendChild(actionsCell);
        
        tableBody.appendChild(row);
    });
}

async function readProfile(profileId) {
    try {
        const response = await fetch(`/api/core/profile/${profileId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const profile = await response.json();
            displayProfile(profile);
        } else {
            const error = await response.text();
            showMessage(`Error loading profile: ${error}`, 'error');
        }
    } catch (error) {
        showMessage(`Network error: ${error.message}`, 'error');
    }
}

async function readProfileForEdit(profileId) {
    const session = getUserSession();
    if (!session || !session.access_token) {
        showMessage('You must be logged in to edit a profile.', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/core/profile/${profileId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${session.access_token}`
            }
        });
        
        if (response.ok) {
            const profile = await response.json();
            populateEditForm(profile);
        } else {
            const error = await response.text();
            showMessage(`Error loading profile: ${error}`, 'error');
        }
    } catch (error) {
        showMessage(`Network error: ${error.message}`, 'error');
    }
}

//
// random functions
//

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