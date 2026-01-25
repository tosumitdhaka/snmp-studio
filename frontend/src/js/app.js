const API_BASE = "/api";
const HTML_CACHE = {}; 
let currentModule = null; 

window.AppState = {
    simulator: null,
    logs: []
};

// --- 1. Global Fetch Interceptor (Injects Token) ---
const originalFetch = window.fetch;
window.fetch = async function(url, options = {}) {
    
    // Add Token if exists
    const token = sessionStorage.getItem("snmp_token");
    if (token) {
        // FIX: Ensure headers object exists before accessing it
        if (!options.headers) options.headers = {};

        // Handle Headers object vs simple object
        if (options.headers instanceof Headers) {
            options.headers.append("X-Auth-Token", token);
        } else {
            options.headers["X-Auth-Token"] = token;
        }
    }

    const response = await originalFetch(url, options);

    // Handle 401 (Session Expired) globally
    if (response.status === 401 && !url.includes("/login")) {
        logout(false); 
    }
    return response;
};

// --- 2. Auth Logic ---
document.addEventListener("DOMContentLoaded", () => {
    initAuth();
});

async function initAuth() {
    const loginScreen = document.getElementById("login-screen");
    const wrapper = document.getElementById("wrapper");
    const token = sessionStorage.getItem("snmp_token");

    if (!token) {
        // No token? Show Login
        loginScreen.style.display = "flex";
        wrapper.style.display = "none";
    } else {
        // Token exists? Verify it
        try {
            const res = await fetch('/api/settings/check');
            if (res.ok) {
                const data = await res.json();
                updateUserUI(data.user);
                showApp();
            } else {
                logout(false);
            }
        } catch (e) {
            console.error("Auth Check Failed", e);
            // Allow retry if backend is just temporarily down? 
            // For now, assume session invalid if check fails
            logout(false); 
        }
    }
}

window.handleLogin = async function(e) {
    e.preventDefault();
    console.log("Attempting Login..."); // Debug

    const user = document.getElementById("login-user").value;
    const pass = document.getElementById("login-pass").value;
    const btn = document.getElementById("login-btn");
    const err = document.getElementById("login-error");

    btn.disabled = true;
    err.classList.add("d-none");

    try {
        const res = await originalFetch('/api/settings/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });

        const data = await res.json();

        if (res.ok) {
            console.log("Login Success. Token received:", data.token ? "YES" : "NO");
            sessionStorage.setItem("snmp_token", data.token);
            updateUserUI(data.username);
            
            // Explicitly call showApp and log it
            showApp(); 
        } else {
            console.warn("Login Failed:", data);
            err.textContent = data.detail || "Login Failed";
            err.classList.remove("d-none");
        }
    } catch (e) {
        console.error("Login Exception:", e);
        err.textContent = "Connection Error";
        err.classList.remove("d-none");
    } finally {
        btn.disabled = false;
    }
};

function showApp() {
    console.log("Switching to App View...");
    const loginScreen = document.getElementById("login-screen");
    const wrapper = document.getElementById("wrapper");

    if (loginScreen) {
        // FIX: Remove d-flex class to ensure it hides
        loginScreen.classList.remove("d-flex"); 
        loginScreen.style.display = "none";
    } else {
        console.error("CRITICAL: Element #login-screen not found. Did you update index.html?");
    }

    if (wrapper) {
        wrapper.style.display = "flex";
    }

    initializeAppLogic();
}

window.logout = async function(callApi = true) {
    if (callApi) {
        try { await fetch('/api/settings/logout', { method: 'POST' }); } catch(e){}
    }
    sessionStorage.removeItem("snmp_token");
    window.location.reload();
};

function updateUserUI(username) {
    const el = document.getElementById("nav-user-name");
    if(el) el.textContent = username;
}

function initializeAppLogic() {
    // 1. Sidebar Toggle
    const sidebarToggle = document.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', e => {
            e.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
        });
    }

    // 2. Health & Routing
    checkBackendHealth();
    window.addEventListener('hashchange', handleRouting);
    handleRouting(); 
}

async function handleRouting() {
    let moduleName = window.location.hash.substring(1) || 'dashboard';
    
    // 1. Cleanup Previous Module
    if (currentModule && typeof currentModule.destroy === 'function') {
        currentModule.destroy();
    }
    
    // 2. Update Sidebar Active State
    document.querySelectorAll('.list-group-item').forEach(el => {
        el.classList.remove('active');
        if(el.getAttribute('href') === `#${moduleName}`) el.classList.add('active');
    });

    // 3. Load Content
    await loadModule(moduleName);
}

async function loadModule(moduleName) {
    const container = document.getElementById("main-content");
    const title = document.getElementById("page-title");

    const titles = {
        'dashboard': 'System Overview',
        'simulator': 'Simulator Manager',
        'walker': 'Walk & Parse Studio',
        'files': 'File Manager',
        'settings': 'Settings'
    };
    title.textContent = titles[moduleName] || 'SNMP Studio';

    if (!HTML_CACHE[moduleName]) {
        try {
            container.innerHTML = '<div class="text-center mt-5"><div class="spinner-border text-primary"></div></div>';
            const res = await fetch(`${moduleName}.html`);
            if (!res.ok) throw new Error("Module not found");
            HTML_CACHE[moduleName] = await res.text();
        } catch (e) {
            container.innerHTML = `<div class="alert alert-danger">Error: ${e.message}</div>`;
            return;
        }
    }

    container.innerHTML = HTML_CACHE[moduleName];

    // 4. Initialize Logic
    const moduleMap = {
        'dashboard': window.DashboardModule,
        'simulator': window.SimulatorModule,
        'walker': window.WalkerModule,
        'files': window.FilesModule,
        'settings': window.SettingsModule
    };

    if (moduleMap[moduleName]) {
        currentModule = moduleMap[moduleName]; // Set active module
        if(typeof currentModule.init === 'function') {
            currentModule.init();
        }
    }
}

async function checkBackendHealth() {
    const badge = document.getElementById("backend-status");
    try {
        const res = await fetch(`${API_BASE}/meta`);
        await res.json();
        badge.className = "badge bg-success";
        badge.textContent = "Online";
    } catch (e) {
        badge.className = "badge bg-danger";
        badge.textContent = "Offline";
    }
}