const API_BASE = "/api";
let currentModule = null; 

window.AppState = {
    simulator: null,
    logs: []
};

// ==================== Fetch Interceptor (Auth Token Injection) ====================

const originalFetch = window.fetch;
window.fetch = async function(url, options = {}) {
    const token = sessionStorage.getItem("snmp_token");
    if (token) {
        if (!options.headers) options.headers = {};
        if (options.headers instanceof Headers) {
            options.headers.append("X-Auth-Token", token);
        } else {
            options.headers["X-Auth-Token"] = token;
        }
    }

    const response = await originalFetch(url, options);
    
    if (response.status === 401 && !url.includes("/login")) {
        logout(false); 
    }

    return response;
};

// ==================== App Initialization ====================

document.addEventListener("DOMContentLoaded", () => {
    initAuth();
});

async function initAuth() {
    const loginScreen = document.getElementById("login-screen");
    const wrapper = document.getElementById("wrapper");
    const token = sessionStorage.getItem("snmp_token");

    if (!token) {
        loginScreen.style.display = "flex";
        wrapper.style.display = "none";
    } else {
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
            logout(false); 
        }
    }
}

// ==================== Login Handler ====================

window.handleLogin = async function(e) {
    e.preventDefault();
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
            sessionStorage.setItem("snmp_token", data.token);
            updateUserUI(data.username);
            showApp(); 
        } else {
            err.textContent = data.detail || "Login Failed";
            err.classList.remove("d-none");
        }
    } catch (e) {
        err.textContent = "Connection Error";
        err.classList.remove("d-none");
    } finally {
        btn.disabled = false;
    }
};

// ==================== Show App After Login ====================

function showApp() {
    const loginScreen = document.getElementById("login-screen");
    const wrapper = document.getElementById("wrapper");

    if (loginScreen) {
        loginScreen.classList.remove("d-flex"); 
        loginScreen.style.display = "none";
    }

    if (wrapper) {
        wrapper.style.display = "flex";
    }

    initializeAppLogic();
}

// ==================== Logout ====================

window.logout = async function(callApi = true) {
    if (callApi) {
        try { await fetch('/api/settings/logout', { method: 'POST' }); } catch(e){}
    }
    sessionStorage.removeItem("snmp_token");
    window.location.reload();
};

// ==================== Update User UI ====================

function updateUserUI(username) {
    const el = document.getElementById("nav-user-name");
    if(el) el.textContent = username;
}

// ==================== Initialize App Logic ====================

function initializeAppLogic() {
    // Sidebar toggle
    const sidebarToggle = document.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', e => {
            e.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
        });
    }

    // Load app metadata and check backend health
    loadAppMetadata();
    
    // Check backend health periodically
    setInterval(checkBackendHealth, 60000);

    // Handle routing
    window.addEventListener('hashchange', handleRouting);
    handleRouting(); 
}

// ==================== Load App Metadata ====================

async function loadAppMetadata() {
    const versionEl = document.getElementById("app-version");
    const badge = document.getElementById("backend-status");
    
    try {
        const res = await fetch(`${API_BASE}/meta`);
        const data = await res.json();
        
        if (badge) {
            badge.className = "badge bg-success";
            badge.textContent = "Online";
        }
        
        if (versionEl) {
            versionEl.textContent = `v${data.version}`;
            versionEl.title = `${data.name} v${data.version}`;
        }
        
        document.title = data.name;
        
        window.AppMetadata = {
            name: data.name,
            version: data.version,
            author: data.author,
            description: data.description
        };
        
        console.log(`🔱 ${data.name} v${data.version} loaded successfully`);
        
    } catch (e) {
        console.error("Failed to load app metadata:", e);
        
        if (badge) {
            badge.className = "badge bg-danger";
            badge.textContent = "Offline";
        }
        
        if (versionEl) {
            versionEl.textContent = "Offline";
            versionEl.style.color = "#ef4444";
            versionEl.title = "Backend is offline";
        }
    }
}

// ==================== Check Backend Health ====================

async function checkBackendHealth() {
    const badge = document.getElementById("backend-status");
    const versionEl = document.getElementById("app-version");
    
    try {
        const res = await fetch(`${API_BASE}/meta`);
        const data = await res.json();
        
        if (badge) {
            badge.className = "badge bg-success";
            badge.textContent = "Online";
        }
        
        if (versionEl && versionEl.textContent !== `v${data.version}`) {
            versionEl.textContent = `v${data.version}`;
            versionEl.title = `${data.name} v${data.version}`;
            // console.log(`🔄 Version updated to v${data.version}`);
        }
        
        if (document.title !== data.name) {
            document.title = data.name;
        }
        
    } catch (e) {
        if (badge && badge.classList.contains("bg-success")) {
            console.error("Backend went offline:", e);
        }
        
        if (badge) {
            badge.className = "badge bg-danger";
            badge.textContent = "Offline";
        }
        
        if (versionEl && versionEl.textContent !== "Offline") {
            versionEl.textContent = "Offline";
            versionEl.style.color = "#ef4444";
            versionEl.title = "Backend is offline";
        }
    }
}

// ==================== Routing ====================

async function handleRouting() {
    let moduleName = window.location.hash.substring(1) || 'dashboard';
    
    if (currentModule && typeof currentModule.destroy === 'function') {
        currentModule.destroy();
    }
    
    document.querySelectorAll('.list-group-item').forEach(el => {
        el.classList.remove('active');
        if(el.getAttribute('href') === `#${moduleName}`) el.classList.add('active');
    });

    await loadModule(moduleName);
}

// ==================== Module Loading (NO CACHE) ====================

async function loadModule(moduleName) {
    const container = document.getElementById("main-content");
    const title = document.getElementById("page-title");

    const titles = {
        'dashboard': 'Trishul SNMP Studio',
        'simulator': 'SNMP Simulator',
        'walker': 'Walk & Parse',
        'traps': 'Trap Manager',
        'mibs': 'MIB Manager',
        'settings': 'Settings'
    };

    title.textContent = titles[moduleName] || 'Trishul SNMP Studio';

    // Always fetch fresh HTML (no cache)
    try {
        container.innerHTML = '<div class="text-center mt-5"><div class="spinner-border text-primary"></div></div>';
        
        const res = await fetch(`${moduleName}.html`);
        
        if (!res.ok) throw new Error("Module not found");
        
        const html = await res.text();
        container.innerHTML = html;
        
    } catch (e) {
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error loading module: ${e.message}
            </div>
        `;
        return;
    }

    // Initialize module
    const moduleMap = {
        'dashboard': window.DashboardModule,
        'simulator': window.SimulatorModule,
        'walker': window.WalkerModule,
        'traps': window.TrapsModule,
        'mibs': window.MibsModule,
        'settings': window.SettingsModule
    };

    if (moduleMap[moduleName]) {
        currentModule = moduleMap[moduleName];
        if(typeof currentModule.init === 'function') {
            currentModule.init();
        }
    }
}
