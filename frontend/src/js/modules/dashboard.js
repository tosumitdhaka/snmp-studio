window.DashboardModule = {
    refreshInterval: null,
    lastLoadTime: null,
    
    init: function() {
        this.loadStats();
        // Refresh every 30 seconds
        this.refreshInterval = setInterval(() => this.loadStats(), 30000);
    },
    
    destroy: function() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    },
    
    loadStats: async function() {
        this.lastLoadTime = Date.now();
        
        try {
            // Fetch all stats in parallel
            const [mibRes, simRes, trapRecRes] = await Promise.all([
                fetch('/api/mibs/status').catch(() => null),
                fetch('/api/simulator/status').catch(() => null),
                fetch('/api/traps/status').catch(() => null)
            ]);
            
            // Update MIB count
            if (mibRes && mibRes.ok) {
                const mibData = await mibRes.json();
                const loadedEl = document.getElementById('stat-mibs');
                const trapCountEl = document.getElementById('stat-traps');
                
                if (loadedEl) {
                    loadedEl.textContent = mibData.loaded || 0;
                    loadedEl.className = 'mb-0';
                }
                
                // Count traps from all loaded MIBs
                if (trapCountEl && mibData.mibs) {
                    const trapCount = mibData.mibs.reduce((sum, mib) => sum + (mib.traps || 0), 0);
                    trapCountEl.textContent = trapCount;
                    trapCountEl.className = 'mb-0';
                }
            } else {
                this.showError('stat-mibs', 'Error');
                this.showError('stat-traps', 'Error');
            }
            
            // Update Simulator status
            if (simRes && simRes.ok) {
                const simData = await simRes.json();
                const simEl = document.getElementById('stat-simulator');
                if (simEl) {
                    if (simData.running) {
                        simEl.textContent = 'Online';
                        simEl.className = 'mb-0 text-success fw-bold';
                    } else {
                        simEl.textContent = 'Offline';
                        simEl.className = 'mb-0 text-secondary';
                    }
                }
            } else {
                this.showError('stat-simulator', 'Error');
            }
            
            // Update Trap Receiver status
            if (trapRecRes && trapRecRes.ok) {
                const trapRecData = await trapRecRes.json();
                const recEl = document.getElementById('stat-receiver');
                if (recEl) {
                    if (trapRecData.running) {
                        recEl.textContent = 'Running';
                        recEl.className = 'mb-0 text-info fw-bold';
                    } else {
                        recEl.textContent = 'Stopped';
                        recEl.className = 'mb-0 text-secondary';
                    }
                }
            } else {
                this.showError('stat-receiver', 'Error');
            }
            
        } catch (e) {
            console.error('Dashboard stats error:', e);
            // Show generic error state
            ['stat-mibs', 'stat-traps', 'stat-simulator', 'stat-receiver'].forEach(id => {
                this.showError(id, 'N/A');
            });
        }
    },
    
    showError: function(elementId, text) {
        const el = document.getElementById(elementId);
        if (el) {
            el.textContent = text;
            el.className = 'mb-0 text-danger';
        }
    }
};