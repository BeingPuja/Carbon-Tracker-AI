// Function to handle fetching and displaying data
async function fetchData(url, method = 'GET', data = null) {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }


  const options = {
    method,
    headers,
  };


  if (data) {
    options.body = JSON.stringify(data);
  }


  try {
    const response = await fetch(url, options);
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || 'Something went wrong');
    }
    return result;
  } catch (error) {
    console.error('Fetch error:', error);
    alert(error.message);
    return null;
  }
}


// Function to handle logout
function handleLogout() {
  localStorage.removeItem('token');
  localStorage.removeItem('username');
  window.location.href = 'index.html';
}


// Check if the user is logged in
function checkAuth() {
  const token = localStorage.getItem('token');
  if (!token && window.location.pathname !== '/index.html' && window.location.pathname !== '/forgot.html') {
    window.location.href = 'index.html';
  }
}


// Global listeners for auth and logout
document.addEventListener('DOMContentLoaded', () => {
  checkAuth();
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', handleLogout);
  }
});


// --- User Authentication (Login/Signup/Forgot) ---


// Login form handler
const loginForm = document.getElementById('login-form');
if (loginForm) {
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const result = await fetchData('/login', 'POST', { username, password });
    if (result) {
      localStorage.setItem('token', result.access_token);
      localStorage.setItem('username', result.username);
      window.location.href = 'dashboard.html';
    }
  });
}


// Signup form handler
const signupForm = document.getElementById('signup-form');
if (signupForm) {
  signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('signup-username').value;
    const password = document.getElementById('signup-password').value;
    const result = await fetchData('/register', 'POST', { username, password });
    if (result) {
      alert('Registration successful! Please log in.');
      // Clear form and switch to login view
      document.getElementById('login-username').value = username;
      document.getElementById('login-password').focus();
    }
  });
}


// Forgot password form handler (front-end)
const forgotForm = document.getElementById('forgot-form');
if (forgotForm) {
  forgotForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    alert('This is a demo feature. A reset link would be sent to your email or a password reset flow would be initiated.');
    window.location.href = 'index.html';
  });
}


// --- Daily Emission Page ---


const calcBtn = document.getElementById('calc-btn');
if (calcBtn) {
  calcBtn.addEventListener('click', async () => {
    const date = document.getElementById('date').value;
    const distance = document.getElementById('distance').value;
    const mode = document.getElementById('mode').value;
    const kwh = document.getElementById('kwh').value;
    const meals = document.getElementById('meals').value;
    const diet = document.getElementById('diet').value;


    const data = { date, distance, mode, kwh, meals, diet };
    const result = await fetchData('/calculate', 'POST', data);
    const emissionResult = document.getElementById('emission-result');


    if (result) {
      emissionResult.innerHTML = `
        <h3>Your Emissions:</h3>
        <p>🚗 Transport: ${result.transport_em} kg CO2</p>
        <p>💡 Energy: ${result.energy_em} kg CO2</p>
        <p>🥗 Diet: ${result.diet_em} kg CO2</p>
        <p><strong>🌳 Total: ${result.total} kg CO2</strong></p>
      `;
    }
  });
}


// --- History Page ---


const historyList = document.getElementById('history-list');
if (historyList) {
  document.addEventListener('DOMContentLoaded', async () => {
    const result = await fetchData('/history');
    if (result && result.history) {
      if (result.history.length === 0) {
        historyList.innerHTML = '<p>No emission history found. Log your daily emissions to see them here!</p>';
        return;
      }
      result.history.forEach(entry => {
        const item = document.createElement('div');
        item.className = 'history-item';
        item.innerHTML = `
          <strong>📅 Date: ${entry.date}</strong><br>
          <p><strong>Total Emissions: ${entry.total} kg CO2</strong></p>
          <ul>
            <li>🚗 Transport: ${entry.transport_em} kg CO2 (${entry.distance} km by ${entry.mode})</li>
            <li>💡 Energy: ${entry.energy_em} kg CO2 (${entry.kwh} kWh)</li>
            <li>🥗 Diet: ${entry.diet_em} kg CO2 (${entry.meals} meals, ${entry.diet} diet)</li>
          </ul>
        `;
        historyList.appendChild(item);
      });
    }
  });
}


// --- Forecast Page ---


const forecastBtn = document.getElementById('forecast-btn');
const forecastResultDiv = document.getElementById('forecast-result');
if (forecastBtn && forecastResultDiv) {
  forecastBtn.addEventListener('click', async () => {
    const result = await fetchData('/forecast');
    if (result) {
      if (result.message) {
        forecastResultDiv.innerHTML = `<p class="alert">${result.message}</p>`;
        return;
      }
     
      const historicalHtml = result.historical.map(item =>
        `<li>📅 ${item.date}: ${item.total} kg CO2</li>`
      ).join('');


      forecastResultDiv.innerHTML = `
        <p>Your forecast for tomorrow's carbon footprint is:</p>
        <h3>🔮 ${result.forecast} kg CO2</h3>
        <h4>Based on your last few entries:</h4>
        <ul class="history-list">
          ${historicalHtml}
        </ul>
      `;
    }
  });
}


// --- Chatbot Page ---


const chatSendBtn = document.getElementById('chat-send');
const chatInput = document.getElementById('chat-input');
const chatBox = document.getElementById('chat-box');


if (chatSendBtn && chatInput && chatBox) {
  // Initial message
  const initialMessage = document.createElement('div');
  initialMessage.className = 'chat-message bot';
  initialMessage.textContent = 'Hello! I am your Carbon Assistant. I can help you with tips to reduce your footprint or answer questions based on your recent activity.';
  chatBox.appendChild(initialMessage);


  chatSendBtn.addEventListener('click', sendMessage);
  chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  });


  async function sendMessage() {
    const userMessage = chatInput.value.trim();
    if (!userMessage) return;


    // Display user message
    const userMsgEl = document.createElement('div');
    userMsgEl.className = 'chat-message user';
    userMsgEl.textContent = userMessage;
    chatBox.appendChild(userMsgEl);


    // Clear input
    chatInput.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;


    // Fetch bot response
    const result = await fetchData('/chat', 'POST', { message: userMessage });


    // Display bot response
    if (result) {
      const botMsgEl = document.createElement('div');
      botMsgEl.className = 'chat-message bot';
      botMsgEl.textContent = result.response;
      chatBox.appendChild(botMsgEl);
      chatBox.scrollTop = chatBox.scrollHeight;
    }
  }
}
