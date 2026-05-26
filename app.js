let ws = null;
let reconnectInterval = null;

// DOM Elements
const warningScreen = document.getElementById('warning-screen');
const loginScreen = document.getElementById('login-screen');
const dashboardScreen = document.getElementById('dashboard-screen');

const btnRunScript = document.getElementById('btn-run-script');
const btnSendCode = document.getElementById('btn-send-code');
const btnVerifyCode = document.getElementById('btn-verify-code');
const phoneInput = document.getElementById('phone-input');
const codeInput = document.getElementById('code-input');
const phoneGroup = document.getElementById('phone-group');
const codeGroup = document.getElementById('code-group');
const loginStatus = document.getElementById('login-status');

const globalBalanceEl = document.getElementById('global-balance');
const totalAccountsCountEl = document.getElementById('total-accounts-count');
const totalAdsCountEl = document.getElementById('total-ads-count');
const accountsContainer = document.getElementById('accounts-container');
const logsContainer = document.getElementById('logs-container');

// Multi Account Modal
const modal = document.getElementById('multi-modal');
const btnAddAccount = document.getElementById('btn-add-account');
const closeModal = document.getElementById('close-modal');
const mBtnSendCode = document.getElementById('m-btn-send-code');
const mBtnVerifyCode = document.getElementById('m-btn-verify-code');
const mPhoneInput = document.getElementById('m-phone-input');
const mCodeInput = document.getElementById('m-code-input');
const mPhoneGroup = document.getElementById('m-phone-group');
const mCodeGroup = document.getElementById('m-code-group');
const mStatus = document.getElementById('m-status');

// Init
function init() {
    btnRunScript.addEventListener('click', () => {
        switchScreen(loginScreen);
        connectWebSocket();
    });

    btnSendCode.addEventListener('click', () => {
        const phone = phoneInput.value.trim();
        if(!phone) return setStatus('Please enter phone number');
        setStatus('Requesting code...');
        sendMessage({ action: 'send_code', phone: phone, session: 'treward_main' });
    });

    btnVerifyCode.addEventListener('click', () => {
        const code = codeInput.value.trim();
        if(!code) return setStatus('Please enter OTP code');
        setStatus('Verifying code...');
        sendMessage({ action: 'verify_code', code: code, session: 'treward_main' });
    });

    // Modal
    btnAddAccount.addEventListener('click', () => {
        modal.classList.add('active');
        mPhoneGroup.classList.remove('hidden');
        mCodeGroup.classList.add('hidden');
        mStatus.innerText = '';
        mPhoneInput.value = '';
        mCodeInput.value = '';
    });
    
    closeModal.addEventListener('click', () => modal.classList.remove('active'));

    mBtnSendCode.addEventListener('click', () => {
        const phone = mPhoneInput.value.trim();
        if(!phone) return;
        mStatus.innerText = 'Requesting code...';
        sendMessage({ action: 'send_code', phone: phone, session: `treward_multi_${Date.now()}` });
    });

    mBtnVerifyCode.addEventListener('click', () => {
        const code = mCodeInput.value.trim();
        if(!code) return;
        mStatus.innerText = 'Verifying code...';
        sendMessage({ action: 'verify_code', code: code, session: window.currentMultiSession });
    });
}

function switchScreen(screenToActive) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    screenToActive.classList.add('active');
}

function setStatus(msg) {
    loginStatus.innerText = msg;
}

// WebSocket Logic
function connectWebSocket() {
    let protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    let host = window.location.host;
    
    // If opened via Live Preview (port 5500) or directly from file system
    if (!host || host.includes(':5500')) {
        host = '127.0.0.1:8000';
        protocol = 'ws:';
    }

    ws = new WebSocket(`${protocol}//${host}/ws`);

    ws.onopen = () => {
        console.log('Connected to server');
        if(reconnectInterval) clearInterval(reconnectInterval);
        sendMessage({ action: 'get_state' });
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };

    ws.onclose = () => {
        console.log('Disconnected from server. Reconnecting...');
        reconnectInterval = setTimeout(connectWebSocket, 3000);
    };
}

function sendMessage(msg) {
    if(ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(msg));
    }
}

function handleMessage(data) {
    switch(data.type) {
        case 'state_update':
            // If already authorized and has clients, go to dashboard
            if(data.has_clients && loginScreen.classList.contains('active')) {
                switchScreen(dashboardScreen);
            }
            updateDashboard(data);
            break;
        case 'code_requested':
            const detailMsg = data.detail ? `✅ Code sent via ${data.detail}!` : '✅ Code sent!';
            if (data.session === 'treward_main') {
                setStatus(detailMsg);
                phoneGroup.classList.add('hidden');
                codeGroup.classList.remove('hidden');
            } else {
                window.currentMultiSession = data.session;
                mStatus.innerText = detailMsg;
                mPhoneGroup.classList.add('hidden');
                mCodeGroup.classList.remove('hidden');
            }
            break;
        case 'login_success':
            if (data.session === 'treward_main') {
                setStatus('✅ Login Successful! Loading dashboard...');
                setTimeout(() => switchScreen(dashboardScreen), 1000);
            } else {
                mStatus.innerText = '✅ Account Added!';
                setTimeout(() => modal.classList.remove('active'), 1000);
            }
            break;
        case 'error':
            if (data.session === 'treward_main') setStatus('Error: ' + data.message);
            else mStatus.innerText = 'Error: ' + data.message;
            break;
        case 'countdown':
            updateCountdown(data.name, data.sec, data.log_id);
            break;
        case 'log':
            addLog(data.message, data.id);
            break;
    }
}

function updateDashboard(data) {
    globalBalanceEl.innerText = `💰 Total: ${data.global_balance}`;
    totalAccountsCountEl.innerText = data.clients.length;
    totalAdsCountEl.innerText = data.total_ads;

    // Render Accounts (preserve countdown badges if already rendered)
    const existingNames = [...accountsContainer.querySelectorAll('.account-item')].map(el => el.dataset.name);
    const newNames = data.clients.map(c => c.name);
    const needsRebuild = JSON.stringify(existingNames) !== JSON.stringify(newNames);

    if (needsRebuild) {
        accountsContainer.innerHTML = '';
        data.clients.forEach((acc, i) => {
            const div = document.createElement('div');
            div.className = 'account-item';
            div.dataset.name = acc.name;
            div.innerHTML = `
                <div class="acc-info">
                    <span class="acc-name">${acc.name}</span>
                    <span class="acc-bal" data-bal="${acc.name}">Balance: ${acc.balance}</span>
                </div>
                <div style="display:flex;align-items:center;gap:8px;">
                    <span class="countdown-badge" data-cd="${acc.name}">⏳ 5s</span>
                    <button class="btn btn-small ${acc.is_active ? 'btn-danger' : 'btn-success'}" onclick="toggleAcc(${i})">
                        ${acc.is_active ? 'Disconnect' : 'Connect'}
                    </button>
                </div>
            `;
            accountsContainer.appendChild(div);
        });
    } else {
        // Just update balances and button states
        data.clients.forEach((acc, i) => {
            const balEl = accountsContainer.querySelector(`[data-bal="${acc.name}"]`);
            if (balEl) balEl.innerText = `Balance: ${acc.balance}`;
            const btns = accountsContainer.querySelectorAll('.btn-small');
            if (btns[i]) {
                btns[i].className = `btn btn-small ${acc.is_active ? 'btn-danger' : 'btn-success'}`;
                btns[i].innerText = acc.is_active ? 'Disconnect' : 'Connect';
            }
        });
    }
}

function toggleAcc(index) {
    sendMessage({ action: 'toggle_account', index: index });
}

function updateCountdown(name, sec, log_id) {
    const el = accountsContainer.querySelector(`[data-cd="${name}"]`);
    if (el) {
        if (sec === 0) {
            el.innerText = '✅';
            el.style.color = '#2ecc71';
        } else {
            el.innerText = `⏳ ${sec}s`;
            el.style.color = sec <= 2 ? '#e74c3c' : '#f1c40f';
        }
    }
    if (log_id) {
        const logEl = document.getElementById(log_id);
        if (logEl) {
            logEl.innerText = logEl.innerText.replace(/sec:- \d+s|sec:- ✅/, sec === 0 ? 'sec:- ✅' : `sec:- ${sec}s`);
        }
    }
}

function addLog(msg, id) {
    const div = document.createElement('div');
    div.className = 'log-line';
    if(id) div.id = id;
    if(msg.includes('FAILED') || msg.includes('Error')) div.classList.add('log-error');
    else if(msg.includes('SUCCESS') || msg.includes('Mined: +')) div.classList.add('log-success');
    div.innerText = msg;
    logsContainer.appendChild(div);
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

init();
