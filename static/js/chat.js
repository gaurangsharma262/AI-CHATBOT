// chat.js — NeuralChat AI Friend

document.addEventListener('DOMContentLoaded', () => {
    // ── Session ID ────────────────────────────────────────────────
    let sessionId = localStorage.getItem('chatSessionId');
    if (!sessionId) {
        sessionId = crypto.randomUUID
            ? crypto.randomUUID()
            : 'session-' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('chatSessionId', sessionId);
    }

    // ── DOM refs ──────────────────────────────────────────────────
    const messagesArea    = document.getElementById('messagesArea');
    const userInput       = document.getElementById('userInput');
    const sendBtn         = document.getElementById('sendBtn');
    const typingIndicator = document.getElementById('typingIndicator');
    const welcomeHero     = document.getElementById('welcomeHero');
    const chatStatus      = document.getElementById('chatStatus');

    // ── Check Gemini Status ───────────────────────────────────────
    fetch('/api/config')
        .then(r => r.json())
        .then(cfg => {
            const dot  = document.querySelector('.status-dot');
            const text = document.querySelector('.status-text');
            if (cfg.gemini_enabled) {
                if (dot)  dot.classList.add('active');
                if (text) text.textContent = 'AI Online';
                if (chatStatus) chatStatus.textContent = 'AI Friend · Online';
            } else {
                if (text) text.textContent = 'AI Offline';
                if (chatStatus) chatStatus.textContent = 'AI Offline · Check API Key';
            }
        })
        .catch(() => {});

    // ── Helpers ───────────────────────────────────────────────────
    function scrollBottom() {
        if (messagesArea) messagesArea.scrollTop = messagesArea.scrollHeight;
    }

    function hideWelcome() {
        if (welcomeHero) {
            welcomeHero.style.display = 'none';
        }
    }

    function appendMessage(text, sender, source) {
        hideWelcome();

        const row = document.createElement('div');
        row.className = `msg-row ${sender}`;

        const avatarContent = sender === 'user'
            ? 'U'
            : '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/></svg>';

        const geminiTag = '';

        row.innerHTML = `
            <div class="msg-avatar ${sender}">${avatarContent}</div>
            <div>
                <div class="msg-bubble">${formatText(text)}</div>
            </div>`;

        messagesArea.appendChild(row);
        scrollBottom();
    }

    function formatText(text) {
        // Basic formatting: convert newlines to <br> and escape HTML
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\n/g, '<br>');
    }

    function showTyping() {
        if (typingIndicator) {
            typingIndicator.style.display = 'flex';
            scrollBottom();
        }
    }

    function hideTyping() {
        if (typingIndicator) typingIndicator.style.display = 'none';
    }

    // ── Send Message ──────────────────────────────────────────────
    async function sendMessage(overrideText) {
        const msg = overrideText || (userInput ? userInput.value.trim() : '');
        if (!msg) return;

        appendMessage(msg, 'user');
        if (userInput) userInput.value = '';
        if (userInput) userInput.focus();

        showTyping();

        try {
            const res = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg, session_id: sessionId })
            });
            const data = await res.json();
            hideTyping();

            if (data.error) {
                appendMessage('Sorry, something went wrong: ' + data.error, 'bot', 'error');
            } else {
                appendMessage(data.response || 'Hmm, I got no response. Try again!', 'bot', data.source);
            }
        } catch (err) {
            hideTyping();
            appendMessage('Network error — is the server running? Check your terminal.', 'bot', 'error');
            console.error('Chat error:', err);
        }
    }

    // ── Globals for onclick ───────────────────────────────────────
    window.sendQuick = text => sendMessage(text);
    window.sendMessage = sendMessage;
    window.clearChat = () => {
        // Remove all messages
        const msgs = messagesArea.querySelectorAll('.msg-row');
        msgs.forEach(m => m.remove());

        // Show welcome hero again
        if (welcomeHero) welcomeHero.style.display = '';

        // Reset session
        sessionId = crypto.randomUUID
            ? crypto.randomUUID()
            : 'session-' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('chatSessionId', sessionId);
    };

    window.toggleSidebar = () => {
        const sidebar = document.querySelector('.sidebar');
        let overlay = document.querySelector('.sidebar-overlay');

        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            overlay.onclick = () => {
                sidebar.classList.remove('open');
                overlay.classList.remove('open');
            };
            document.body.appendChild(overlay);
        }

        sidebar.classList.toggle('open');
        overlay.classList.toggle('open');
    };

    // ── Event Listeners ───────────────────────────────────────────
    if (sendBtn) sendBtn.addEventListener('click', () => sendMessage());
    if (userInput) userInput.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});
