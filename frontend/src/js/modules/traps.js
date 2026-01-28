window.TrapsModule = {
    pollInterval: null,
    vbCount: 0,

    init: function() {
        this.checkStatus();
        this.loadTraps();
        this.pollInterval = setInterval(() => { this.checkStatus(); this.loadTraps(); }, 3000);
        
        this.loadSelectedTrap();
    },

    destroy: function() {
        if (this.pollInterval) clearInterval(this.pollInterval);
    },

    loadSelectedTrap: function() {
        const trapData = sessionStorage.getItem('selectedTrap');
        if (!trapData) {
            this.addVarbind("1.3.6.1.2.1.1.3.0", "TimeTicks", "0");
            return;
        }

        try {
            const trap = JSON.parse(trapData);
            sessionStorage.removeItem('selectedTrap');
            
            document.getElementById('ts-oid').value = trap.full_name;
            
            document.getElementById('vb-container').innerHTML = 
                '<div class="text-center text-muted small py-2" id="vb-empty" style="display:none;"></div>';
            
            this.addVarbind("1.3.6.1.2.1.1.3.0", "TimeTicks", "12345");
            
            if (trap.objects && trap.objects.length > 0) {
                trap.objects.forEach(obj => {
                    let type = "String";
                    const name = obj.name.toLowerCase();
                    
                    if (name.includes('index') || name.includes('count')) {
                        type = "Integer";
                    } else if (name.includes('status') || name.includes('state')) {
                        type = "Integer";
                    } else if (name.includes('addr') || name.includes('address')) {
                        type = "IpAddress";
                    }
                    
                    this.addVarbind(obj.full_name, type, "");
                });
            }
            
            this.showNotification(`Loaded trap: ${trap.name}`, 'success');
            
        } catch (e) {
            console.error('Failed to load selected trap:', e);
        }
    },

    showNotification: function(message, type = 'info') {
        const banner = document.createElement('div');
        banner.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        banner.style.cssText = 'top: 80px; right: 20px; z-index: 9999; min-width: 300px;';
        banner.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(banner);
        
        setTimeout(() => {
            banner.remove();
        }, 3000);
    },

    addVarbind: function(oid="", type="String", val="") {
        const container = document.getElementById("vb-container");
        document.getElementById("vb-empty").style.display = "none";
        
        const id = `vb-row-${this.vbCount++}`;
        const html = `
            <div class="card mb-2 border-secondary" id="${id}">
                <div class="card-body p-2">
                    <div class="input-group input-group-sm mb-1">
                        <span class="input-group-text bg-light">OID</span>
                        <input type="text" class="form-control vb-oid" value="${oid}" placeholder="1.3.6... or IF-MIB::ifIndex">
                        <button class="btn btn-outline-danger" onclick="document.getElementById('${id}').remove()">X</button>
                    </div>
                    <div class="input-group input-group-sm">
                        <select class="form-select vb-type" style="max-width: 120px;">
                            <option value="String" ${type==='String'?'selected':''}>String</option>
                            <option value="Integer" ${type==='Integer'?'selected':''}>Integer</option>
                            <option value="OID" ${type==='OID'?'selected':''}>OID</option>
                            <option value="TimeTicks" ${type==='TimeTicks'?'selected':''}>TimeTicks</option>
                            <option value="IpAddress" ${type==='IpAddress'?'selected':''}>IpAddress</option>
                            <option value="Counter" ${type==='Counter'?'selected':''}>Counter</option>
                            <option value="Gauge" ${type==='Gauge'?'selected':''}>Gauge</option>
                        </select>
                        <input type="text" class="form-control vb-val" value="${val}" placeholder="Value">
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', html);
    },

    resetForm: function() {
        document.getElementById("vb-container").innerHTML = '<div class="text-center text-muted small py-2" id="vb-empty">No VarBinds added</div>';
        document.getElementById("ts-oid").value = "IF-MIB::linkDown";
        this.addVarbind("1.3.6.1.2.1.1.3.0", "TimeTicks", "0");
    },

    lookupTrap: async function() {
        const oid = document.getElementById("ts-oid").value;
        if(!oid) return;
        
        const btn = document.querySelector("button[title='Auto-pick VarBinds']");
        const originalIcon = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            const res = await fetch(`/api/traps/definition?oid=${oid}`);
            const data = await res.json();
            
            if (data.found && data.objects.length > 0) {
                document.getElementById("vb-container").innerHTML = '<div class="text-center text-muted small py-2" id="vb-empty" style="display:none"></div>';
                
                this.addVarbind("1.3.6.1.2.1.1.3.0", "TimeTicks", "12345");
                data.objects.forEach(obj => {
                    this.addVarbind(obj.oid || obj.name, "String", "");
                });
            } else {
                alert("No definition found in loaded MIBs. Please enter VarBinds manually.");
            }
        } catch(e) {
            console.error(e);
        } finally {
            btn.innerHTML = originalIcon;
        }
    },

    sendTrap: async function(e) {
        e.preventDefault();
        const btn = e.target.querySelector("button[type='submit']");
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';

        const varbinds = [];
        document.querySelectorAll("#vb-container .card").forEach(row => {
            const oid = row.querySelector(".vb-oid").value.trim();
            const type = row.querySelector(".vb-type").value;
            const value = row.querySelector(".vb-val").value.trim();
            
            if (oid && value) {
                varbinds.push({ oid, type, value });
            }
        });

        const payload = {
            target: document.getElementById("ts-target").value,
            port: parseInt(document.getElementById("ts-port").value),
            community: document.getElementById("ts-comm").value,
            oid: document.getElementById("ts-oid").value,
            varbinds: varbinds
        };

        try {
            const res = await fetch('/api/traps/send', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            
            if (res.ok) {
                const data = await res.json();
                this.showNotification(`✓ Trap sent to ${data.target}:${data.port}`, 'success');
                
                if (payload.target === "127.0.0.1" || payload.target === "localhost") {
                    setTimeout(() => this.loadTraps(), 500); 
                }
            } else {
                const errorData = await res.json();
                const errorMsg = errorData.detail || 'Unknown error';
                
                alert(`Trap Send Failed\n\nError: ${errorMsg}\n\nTroubleshooting:\n• Check if the MIB is loaded in MIB Manager\n• Verify OID syntax (e.g., MODULE::trapName)\n• Ensure all VarBind values match their types`);
            }
        } catch (e) {
            console.error('Trap send error:', e);
            alert(`Connection Failed\n\n${e.message}`);
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    },

    checkStatus: async function() {
        try {
            const res = await fetch('/api/traps/status');
            const data = await res.json();
            this.updateStatusUI(data);
        } catch(e) {
            console.error('Status check failed:', e);
        }
    },

    updateStatusUI: function(status) {
        const badge = document.getElementById("tr-status-badge");
        const btnStart = document.getElementById("btn-tr-start");
        const btnStop = document.getElementById("btn-tr-stop");
        
        if (status.running) {
            badge.className = "badge bg-success";
            badge.innerHTML = `RUNNING <span class="small">(${status.resolve_mibs ? 'Resolved' : 'Raw'})</span>`;
            btnStart.disabled = true;
            btnStop.disabled = false;
        } else {
            badge.className = "badge bg-secondary";
            badge.textContent = "STOPPED";
            btnStart.disabled = false;
            btnStop.disabled = true;
        }
    },

    startReceiver: async function() {
        const port = parseInt(document.getElementById("tr-port").value);
        const resolve = document.getElementById("tr-resolve-toggle").checked;
        
        await fetch('/api/traps/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                port: port,
                community: "public",
                resolve_mibs: resolve
            })
        });
        
        this.checkStatus();
    },

    stopReceiver: async function() {
        await fetch('/api/traps/stop', {method:'POST'});
        this.checkStatus();
    },

    loadTraps: async function() {
        const tbody = document.getElementById("tr-table-body");
        const countBadge = document.getElementById("tr-count-badge");
        
        if (!tbody) return;
        
        try {
            const res = await fetch('/api/traps/');
            const json = await res.json();
            
            if (json.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted p-3">No traps received.</td></tr>';
                countBadge.textContent = '0';
                return;
            }
            
            countBadge.textContent = json.data.length;
            
            tbody.innerHTML = json.data.map(t => {
                let trapBadgeClass = 'bg-secondary';
                const trapType = t.trap_type || 'Unknown';
                
                if (trapType.toLowerCase().includes('up') || trapType.toLowerCase().includes('start')) {
                    trapBadgeClass = 'bg-success';
                } else if (trapType.toLowerCase().includes('down')) {
                    trapBadgeClass = 'bg-danger';
                } else if (trapType.toLowerCase().includes('auth') || trapType.toLowerCase().includes('fail')) {
                    trapBadgeClass = 'bg-warning text-dark';
                }
                
                return `
                    <tr>
                        <td class="small text-muted">${t.time_str}</td>
                        <td><code class="small">${t.source}</code></td>
                        <td>
                            <span class="badge ${trapBadgeClass}">${trapType}</span>
                        </td>
                        <td>
                            <div class="varbind-list">
                                ${t.varbinds.map(v => {
                                    if (v.oid.includes('1.3.6.1.6.3.1.1.4.1.0') || v.name.includes('snmpTrapOID')) {
                                        return '';
                                    }
                                    
                                    let displayName = v.oid;
                                    let nameClass = 'text-muted';
                                    
                                    if (t.resolved && v.resolved && v.name !== v.oid) {
                                        displayName = v.name;
                                        nameClass = 'text-primary fw-bold';
                                    }
                                    
                                    if (displayName.length > 40) {
                                        displayName = displayName.substring(0, 37) + '...';
                                    }
                                    
                                    return `
                                        <div class="d-flex justify-content-between align-items-start small mb-1 py-1 border-bottom">
                                            <span class="${nameClass} me-2" style="font-family: 'Courier New', monospace; font-size: 0.8rem;">
                                                ${displayName}
                                            </span>
                                            <span class="text-dark text-end" style="max-width: 200px; word-break: break-word;">
                                                ${v.value}
                                            </span>
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        } catch(e) {
            console.error('Failed to load traps:', e);
        }
    },

    clearTraps: async function() {
        await fetch('/api/traps/', {method:'DELETE'});
        this.loadTraps();
    }
};
