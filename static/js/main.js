// main.js - Core JavaScript: Dark Mode, Chatbot, UI interactions

// ─────────────────────────────────────────────
// DARK MODE (stored in localStorage)
// ─────────────────────────────────────────────
const THEME_KEY = 'rcoem_theme';

function initTheme() {
    const saved = localStorage.getItem(THEME_KEY) || 'light';
    applyTheme(saved);
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const icon = document.getElementById('theme-icon');
    if (icon) icon.textContent = theme === 'dark' ? '☀️' : '🌙';
    localStorage.setItem(THEME_KEY, theme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    applyTheme(current === 'dark' ? 'light' : 'dark');
}

// ─────────────────────────────────────────────
// CHATBOT WIDGET
// ─────────────────────────────────────────────
let chatOpen = false;
let chatHistory = [];
let labelTimeout;

const chatWindow = document.getElementById('chat-window');
const chatToggleBtn = document.getElementById('chat-toggle-btn');
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const chatLabel = document.getElementById('chat-label');

function toggleChat() {
    chatOpen = !chatOpen;
    if (chatWindow) {
        chatWindow.classList.toggle('open', chatOpen);
    }

    // Hide label when opened
    if (chatLabel) {
        chatLabel.style.display = chatOpen ? 'none' : 'block';
    }

    // Show welcome message on first open
    if (chatOpen && chatHistory.length === 0) {
        setTimeout(() => {
            sendBotMessage("👋 Hello! I'm your <b>RCOEM Assistant</b>.<br>Ask me anything about the college! Use the quick chips below or type your question. 😊");
        }, 300);
    }

    if (chatOpen && chatInput) {
        setTimeout(() => chatInput.focus(), 400);
    }
}

function sendBotMessage(text) {
    if (!chatMessages) return;

    // Show typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot';
    typingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>`;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    setTimeout(() => {
        typingDiv.remove();
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message bot';
        msgDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-bubble">${text}</div>`;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        chatHistory.push({ role: 'bot', text });
    }, 800 + Math.random() * 600);
}

function sendUserMessage(text) {
    if (!chatMessages || !text.trim()) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = 'message user';
    msgDiv.innerHTML = `
        <div class="message-avatar" style="background:#6366f1">👤</div>
        <div class="message-bubble">${text}</div>`;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    chatHistory.push({ role: 'user', text });
}

async function sendChatMessage() {
    if (!chatInput) return;
    const message = chatInput.value.trim();
    if (!message) return;

    sendUserMessage(message);
    chatInput.value = '';
    chatInput.style.height = 'auto';

    try {
        const res = await fetch('/chatbot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        const data = await res.json();
        sendBotMessage(data.response);
    } catch (err) {
        sendBotMessage('⚠️ Sorry, I encountered an error. Please try again or contact the college directly.');
    }
}

function sendChipQuery(query) {
    if (!chatInput) return;
    chatInput.value = query;
    sendChatMessage();
}

// Input event for auto-resize and Enter key
if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });

    chatInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 80) + 'px';
    });
}

// Show floating label after 5 seconds
setTimeout(() => {
    if (!chatOpen && chatLabel) {
        chatLabel.style.display = 'block';
        labelTimeout = setTimeout(() => {
            if (!chatOpen && chatLabel) chatLabel.style.display = 'none';
        }, 4000);
    }
}, 5000);

// ─────────────────────────────────────────────
// SIDEBAR ACTIVE STATE
// ─────────────────────────────────────────────
function setActiveSidebarLink() {
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar-menu a').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// ─────────────────────────────────────────────
// FLASH MESSAGE AUTO-DISMISS
// ─────────────────────────────────────────────
function initFlashMessages() {
    const alerts = document.querySelectorAll('.alert[data-autodismiss]');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 300);
        }, 4000);
    });
}

// ─────────────────────────────────────────────
// ADMIN: CONFIRM DELETE
// ─────────────────────────────────────────────
function confirmDelete(formId, itemName) {
    if (confirm(`Are you sure you want to delete "${itemName}"? This cannot be undone.`)) {
        document.getElementById(formId).submit();
    }
}

// ─────────────────────────────────────────────
// PROGRESS BAR ANIMATION
// ─────────────────────────────────────────────
function animateProgressBars() {
    const bars = document.querySelectorAll('.progress-bar[data-width]');
    bars.forEach(bar => {
        const width = bar.dataset.width;
        setTimeout(() => { bar.style.width = width + '%'; }, 200);

        // Color-code attendance
        const value = parseInt(width);
        if (value >= 80) bar.classList.add('good');
        else if (value >= 65) bar.classList.add('avg');
        else bar.classList.add('poor');
    });
}

// ─────────────────────────────────────────────
// INIT
// ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    setActiveSidebarLink();
  //  initFlashMessages();
    animateProgressBars();
});