
window.SimulatorModule = {
    intervalId: null,

    init: function() {
        this.destroy();
        
        // 1. Restore Logs
        const area = document.getElementById("sim-log-area");
        if (area && window.AppState.logs.length > 0) {
            area.innerHTML = window.AppState.logs.join("");
            area.scrollTop = area.scrollHeight;
        } else if (area) {
            area.innerHTML = '<div class="text-muted small p-2">Waiting for events...</div>';
        }

        // 2. Load Cached State
        if (window.AppState.simulator) {
            this.updateUI(window.AppState.simulator);
        } else {
            this.setButtons(false); 
        }

        // 3. Start Polling
        this.fetchStatus();
        this.intervalId = setInterval(() => this.fetchStatus(), 10000);
    },

    destroy: function() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    },

    fetchStatus: async function() {
        try {
            const res = await fetch('/api/simulator/status');
            if (!res.ok) return;
            const data = await res.json();
            
            // Update Cache
            window.AppState.simulator = data;
            
            this.updateUI(data);
        } catch (e) {
            console.error("Sim status error", e);
        }
    },

    updateUI: function(data) {
        const badge = document.getElementById("sim-badge");
        const stateText = document.getElementById("sim-state-text");
        const detailText = document.getElementById("sim-detail-text");
        
        // Guard for navigation
        if (!badge) return;

        if (data.running) {
            badge.className = "badge bg-success";
            badge.textContent = "RUNNING";
            stateText.textContent = "Online";
            stateText.className = "mb-0 text-success fw-bold";
            detailText.innerHTML = `Listening on <strong>UDP ${data.port}</strong> <br> Community: <code>${data.community}</code> <br> PID: ${data.pid}`;
            
            this.setButtons(true);
            
            // Sync inputs (only if not focused)
            const pInput = document.getElementById("sim-config-port");
            const cInput = document.getElementById("sim-config-comm");
            if(pInput && document.activeElement !== pInput) pInput.value = data.port;
            if(cInput && document.activeElement !== cInput) cInput.value = data.community;

        } else {
            badge.className = "badge bg-secondary";
            badge.textContent = "STOPPED";
            stateText.textContent = "Offline";
            stateText.className = "mb-0 text-secondary fw-bold";
            detailText.textContent = "Service is stopped.";
            
            this.setButtons(false);
        }
    },

    setButtons: function(isRunning) {
        const btnStart = document.getElementById("btn-start");
        const btnStop = document.getElementById("btn-stop");
        const btnRestart = document.getElementById("btn-restart");
        
        if(!btnStart) return;

        // Force boolean state to avoid "undefined" issues
        btnStart.disabled = isRunning;
        btnStop.disabled = !isRunning;
        btnRestart.disabled = !isRunning;
    },
    
    log: function(msg) {
        const area = document.getElementById("sim-log-area");
        const time = new Date().toLocaleTimeString();
        const html = `<div class="border-bottom py-1 px-2"><span class="text-muted small">[${time}]</span> ${msg}</div>`;
        
        // Save to State (Keep last 50 lines)
        window.AppState.logs.push(html);
        if (window.AppState.logs.length > 50) window.AppState.logs.shift();

        // Update UI if visible
        if(area) {
            // Remove "Waiting..." placeholder if it exists
            if(area.textContent.includes("Waiting for events")) area.innerHTML = "";
            
            area.innerHTML += html;
            area.scrollTop = area.scrollHeight;
        }
    },

    start: async function() {
        const port = document.getElementById("sim-config-port").value;
        const comm = document.getElementById("sim-config-comm").value;
        
        this.log(`Starting simulator on Port ${port}...`);
        
        await fetch('/api/simulator/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ port: parseInt(port), community: comm })
        });
        this.fetchStatus();
    },

    stop: async function() {
        this.log("Stopping simulator...");
        await fetch('/api/simulator/stop', { method: 'POST' });
        this.fetchStatus();
    },

    restart: async function() {
        this.log("Restarting...");
        await this.stop();
        setTimeout(() => this.start(), 1000);
    }
};
