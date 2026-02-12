window.SimulatorModule = {
    intervalId: null,
    lastSavedJson: '{}',
    filteredLogs: [],

    init: function() {
        this.destroy();

        if (!window.AppState) {
            window.AppState = {};
        }
        
        // Load logs from localStorage for persistence
        if (!window.AppState.logs) {
            window.AppState.logs = this.loadLogsFromStorage();
        }

        const area = document.getElementById("sim-log-area");
        if (area && window.AppState.logs.length > 0) {
            area.innerHTML = window.AppState.logs.join("");
            area.scrollTop = area.scrollHeight;
        } else if (area) {
            area.innerHTML = '<div class="text-muted small p-2">Waiting for events...</div>';
        }

        if (window.AppState.simulator) {
            this.updateUI(window.AppState.simulator);
        } else {
            this.setButtons(false);
        }

        this.loadCustomData();
        this.attachEditorEvents();
        this.updateLogStats();

        this.fetchStatus();
        this.intervalId = setInterval(() => this.fetchStatus(), 10000);
    },

    destroy: function() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    },

    // ==================== Log Persistence ====================

    loadLogsFromStorage: function() {
        try {
            const stored = localStorage.getItem('trishul_simulator_logs');
            if (stored) {
                return JSON.parse(stored);
            }
        } catch (e) {
            console.error('Failed to load logs from storage:', e);
        }
        return [];
    },

    saveLogsToStorage: function() {
        try {
            // Keep only last 500 logs in storage
            const logsToSave = window.AppState.logs.slice(-500);
            localStorage.setItem('trishul_simulator_logs', JSON.stringify(logsToSave));
        } catch (e) {
            console.error('Failed to save logs to storage:', e);
        }
    },

    clearStoredLogs: function() {
        try {
            localStorage.removeItem('trishul_simulator_logs');
        } catch (e) {
            console.error('Failed to clear logs from storage:', e);
        }
    },

    // ==================== Relative Time Formatting ====================

    formatRelativeTime: function(dateString) {
        if (!dateString) return '--';
        
        try {
            const date = new Date(dateString);
            const now = new Date();
            const diffMs = now - date;
            const diffSec = Math.floor(diffMs / 1000);
            const diffMin = Math.floor(diffSec / 60);
            const diffHour = Math.floor(diffMin / 60);
            const diffDay = Math.floor(diffHour / 24);

            if (diffSec < 5) return 'just now';
            if (diffSec < 60) return `${diffSec}s ago`;
            if (diffMin < 60) return `${diffMin}m ago`;
            if (diffHour < 24) return `${diffHour}h ago`;
            if (diffDay < 7) return `${diffDay}d ago`;
            
            return date.toLocaleDateString();
        } catch (e) {
            return '--';
        }
    },

    attachEditorEvents: function() {
        const editor = document.getElementById('custom-data-editor');
        const unsaved = document.getElementById('unsaved-indicator');
        const jsonError = document.getElementById('json-error-indicator');

        if (!editor) return;

        editor.addEventListener('input', () => {
            const current = editor.value;
            // Unsaved indicator
            if (current.trim() !== this.lastSavedJson.trim()) {
                unsaved && unsaved.classList.remove('d-none');
            } else {
                unsaved && unsaved.classList.add('d-none');
            }

            // JSON validation (soft)
            try {
                if (current.trim()) {
                    JSON.parse(current);
                    jsonError && jsonError.classList.add('d-none');
                    editor.classList.remove('is-invalid');
                } else {
                    jsonError && jsonError.classList.add('d-none');
                    editor.classList.remove('is-invalid');
                }
            } catch (e) {
                jsonError && jsonError.classList.remove('d-none');
                editor.classList.add('is-invalid');
            }
        });
    },

    beforeUnloadHandler: function(e) {
        const editor = document.getElementById('custom-data-editor');
        if (!editor) return;
        if (editor.value.trim() !== SimulatorModule.lastSavedJson.trim()) {
            e.preventDefault();
            e.returnValue = '';
        }
    },

    loadCustomData: async function() {
        const editor = document.getElementById('custom-data-editor');
        if (!editor) return;

        try {
            const res = await fetch('/api/simulator/data');
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }
            const data = await res.json();
            const pretty = JSON.stringify(data, null, 2);
            editor.value = pretty;
            this.lastSavedJson = pretty;
            window.addEventListener('beforeunload', this.beforeUnloadHandler);
        } catch (e) {
            console.error('Failed to load custom data:', e);
            const fallback = '{}';
            editor.value = fallback;
            this.lastSavedJson = fallback;
        }
    },

    saveCustomData: async function() {
        const editor = document.getElementById('custom-data-editor');
        const unsaved = document.getElementById('unsaved-indicator');
        const jsonError = document.getElementById('json-error-indicator');
        const content = editor.value;

        try {
            const json = JSON.parse(content);

            const res = await fetch('/api/simulator/data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(json)
            });

            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }

            const data = await res.json();

            this.lastSavedJson = content;
            unsaved && unsaved.classList.add('d-none');
            jsonError && jsonError.classList.add('d-none');
            editor.classList.remove('is-invalid');

            this.log(`Custom data saved: ${data.message}`, 'success');
            this.showToast('Custom data saved successfully');
        } catch (e) {
            console.error('Save error:', e);
            this.log('Failed to save custom data: ' + e.message, 'error');
            this.showToast('Failed to save custom data: ' + e.message, 'error');
        }
    },

    formatJson: function() {
        const editor = document.getElementById('custom-data-editor');
        try {
            const current = editor.value;
            if (!current.trim()) return;
            const parsed = JSON.parse(current);
            const pretty = JSON.stringify(parsed, null, 2);
            editor.value = pretty;
            this.log('JSON formatted successfully', 'success');
        } catch (e) {
            this.showToast('Invalid JSON: ' + e.message, 'error');
        }
    },

    start: async function() {
        const port = document.getElementById('sim-config-port').value;
        const comm = document.getElementById('sim-config-comm').value;

        this.log(`Starting simulator on Port ${port}...`);

        try {
            const res = await fetch('/api/simulator/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ port: parseInt(port), community: comm })
            });

            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }

            const data = await res.json();
            
            if (data.status === 'started') {
                this.log(data.message || 'Simulator started successfully', 'success');
                this.showToast(data.message || 'Simulator started successfully', 'success');
            } else if (data.status === 'already_running') {
                this.log(data.message || 'Simulator is already running', 'warning');
                this.showToast(data.message || 'Simulator is already running', 'warning');
            }
            
            this.fetchStatus();
        } catch (e) {
            console.error('Start error:', e);
            this.log('Failed to start simulator: ' + e.message, 'error');
            this.showToast('Failed to start simulator: ' + e.message, 'error');
        }
    },

    stop: async function() {
        this.log('Stopping simulator...');
        try {
            const res = await fetch('/api/simulator/stop', { method: 'POST' });
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }

            const data = await res.json();
            this.log(data.message || 'Simulator stopped successfully', 'success');
            this.showToast(data.message || 'Simulator stopped successfully', 'info');
            this.fetchStatus();
        } catch (e) {
            console.error('Stop error:', e);
            this.log('Failed to stop simulator: ' + e.message, 'error');
            this.showToast('Failed to stop simulator: ' + e.message, 'error');
        }
    },

    restart: async function() {
        this.log('Restarting simulator...');
        try {
            const res = await fetch('/api/simulator/restart', { method: 'POST' });
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }

            const data = await res.json();
            this.log(data.message || 'Simulator restarted successfully', 'success');
            this.showToast(data.message || 'Simulator restarted successfully', 'success');
            this.fetchStatus();
        } catch (e) {
            console.error('Restart error:', e);
            this.log('Failed to restart simulator: ' + e.message, 'error');
            this.showToast('Failed to restart simulator: ' + e.message, 'error');
        }
    },

    fetchStatus: async function() {
        try {
            const res = await fetch('/api/simulator/status');
            if (!res.ok) return;
            const data = await res.json();

            window.AppState.simulator = data;
            this.updateUI(data);
        } catch (e) {
            console.error('Sim status error', e);
            this.log('Error fetching simulator status: ' + e.message, 'error');
        }
    },

    updateUI: function(data) {
        const badge = document.getElementById('sim-badge');
        const stateText = document.getElementById('sim-state-text');
        const detailText = document.getElementById('sim-detail-text');
        const metrics = document.getElementById('sim-metrics');
        const uptimeEl = document.getElementById('sim-uptime');
        const reqEl = document.getElementById('sim-requests');
        const lastActEl = document.getElementById('sim-last-activity');
        const configHint = document.getElementById('config-hint');
        const configDisabledHint = document.getElementById('config-disabled-hint');
        const portInput = document.getElementById('sim-config-port');
        const commInput = document.getElementById('sim-config-comm');

        if (!badge || !stateText || !detailText) return;

        if (data.running) {
            badge.className = 'badge bg-success';
            badge.textContent = 'RUNNING';
            stateText.textContent = 'Online';
            stateText.className = 'mb-0 text-success fw-bold';
            detailText.innerHTML = `Listening on <strong>UDP ${data.port}</strong> <br> Community: <code>${data.community}</code> <br> PID: ${data.pid}`;

            this.setButtons(true);

            if (portInput) {
                portInput.value = data.port;
                portInput.disabled = true;
            }
            if (commInput) {
                commInput.value = data.community;
                commInput.disabled = true;
            }

            configHint && configHint.classList.add('d-none');
            configDisabledHint && configDisabledHint.classList.remove('d-none');

            if (metrics && uptimeEl && reqEl && lastActEl) {
                metrics.classList.remove('d-none');
                uptimeEl.textContent = data.uptime || '--';
                reqEl.textContent = data.requests || 0;
                // Format as relative time
                lastActEl.textContent = this.formatRelativeTime(data.last_activity);
            }
        } else {
            badge.className = 'badge bg-secondary';
            badge.textContent = 'STOPPED';
            stateText.textContent = 'Offline';
            stateText.className = 'mb-0 text-secondary fw-bold';
            detailText.textContent = 'Service is stopped.';

            this.setButtons(false);

            if (portInput) {
                portInput.disabled = false;
            }
            if (commInput) {
                commInput.disabled = false;
            }

            configDisabledHint && configDisabledHint.classList.add('d-none');
            if (portInput && commInput && (portInput.value || commInput.value)) {
                configHint && configHint.classList.add('d-none');
            }

            if (metrics) {
                metrics.classList.add('d-none');
            }
        }
    },

    setButtons: function(isRunning) {
        const btnStart = document.getElementById('btn-start');
        const btnStop = document.getElementById('btn-stop');
        const btnRestart = document.getElementById('btn-restart');

        if (!btnStart || !btnStop || !btnRestart) return;

        btnStart.disabled = isRunning;
        btnStop.disabled = !isRunning;
        btnRestart.disabled = !isRunning;
    },

    log: function(msg, type = 'info') {
        const area = document.getElementById('sim-log-area');
        const time = new Date().toLocaleTimeString();

        let icon = 'fa-info-circle';
        let color = 'text-muted';

        if (type === 'success') {
            icon = 'fa-check-circle';
            color = 'text-success';
        } else if (type === 'error') {
            icon = 'fa-exclamation-circle';
            color = 'text-danger';
        } else if (type === 'warning') {
            icon = 'fa-exclamation-triangle';
            color = 'text-warning';
        }

        const html = `
            <div class="border-bottom py-2 px-2 log-entry" data-level="${type}" data-text="${this.escapeHtml(msg)}">
                <span class="text-muted small">[${time}]</span>
                <i class="fas ${icon} ${color} ms-2"></i>
                <span class="ms-2">${msg}</span>
            </div>
        `;

        window.AppState.logs.push(html);
        if (window.AppState.logs.length > 500) window.AppState.logs.shift();

        // Persist to localStorage
        this.saveLogsToStorage();

        if (area) {
            if (area.textContent.includes('Waiting for events')) area.innerHTML = '';
            area.innerHTML += html;
            area.scrollTop = area.scrollHeight;
        }

        this.updateLogStats();
    },

    clearLog: function() {
        const area = document.getElementById('sim-log-area');
        window.AppState.logs = [];
        this.clearStoredLogs();
        if (area) {
            area.innerHTML = '<div class="text-muted small p-2">Waiting for events...</div>';
        }
        this.updateLogStats();
    },

    exportLog: function() {
        const blob = new Blob([this.getPlainLogText()], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `trishul-simulator-log-${new Date().toISOString()}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    },

    getPlainLogText: function() {
        const div = document.createElement('div');
        div.innerHTML = window.AppState.logs.join('');
        const entries = div.querySelectorAll('.log-entry');
        return Array.from(entries).map(e => e.innerText).join('\n');
    },

    filterLogs: function() {
        const searchInput = document.getElementById('log-search');
        const filterSelect = document.getElementById('log-filter');
        const area = document.getElementById('sim-log-area');

        if (!area) return;

        const searchTerm = (searchInput?.value || '').toLowerCase();
        const level = filterSelect?.value || 'all';

        const div = document.createElement('div');
        div.innerHTML = window.AppState.logs.join('');
        const entries = div.querySelectorAll('.log-entry');

        const filtered = Array.from(entries).filter(e => {
            const entryLevel = e.getAttribute('data-level') || 'info';
            const text = (e.getAttribute('data-text') || '').toLowerCase();
            const matchesLevel = level === 'all' || entryLevel === level;
            const matchesSearch = !searchTerm || text.includes(searchTerm);
            return matchesLevel && matchesSearch;
        });

        if (filtered.length === 0) {
            area.innerHTML = '<div class="text-muted small p-2">No log entries match current filter.</div>';
        } else {
            area.innerHTML = filtered.map(e => e.outerHTML).join('');
            area.scrollTop = area.scrollHeight;
        }

        this.updateLogStats(filtered.length);
    },

    updateLogStats: function(filteredCount) {
        const stats = document.getElementById('log-stats');
        const total = window.AppState.logs ? window.AppState.logs.length : 0;
        const current = typeof filteredCount === 'number' ? filteredCount : total;

        if (stats) {
            stats.textContent = `${current} entries${current !== total ? ` (of ${total})` : ''}`;
        }
    },

    showToast: function(message, type = 'success') {
        const banner = document.createElement('div');
        let icon = 'fa-check-circle';
        let cls = 'alert-success';

        if (type === 'error') {
            icon = 'fa-exclamation-circle';
            cls = 'alert-danger';
        } else if (type === 'info') {
            icon = 'fa-info-circle';
            cls = 'alert-info';
        } else if (type === 'warning') {
            icon = 'fa-exclamation-triangle';
            cls = 'alert-warning';
        }

        banner.className = `alert ${cls} alert-dismissible fade show position-fixed`;
        banner.style.cssText = 'top: 80px; right: 20px; z-index: 9999;';
        banner.innerHTML = `
            <i class="fas ${icon} me-2"></i> ${this.escapeHtml(message)}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(banner);
        setTimeout(() => banner.remove(), 4000);
    },

    escapeHtml: function(text) {
        if (text == null) return '';
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
};