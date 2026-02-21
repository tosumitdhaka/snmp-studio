window.DashboardModule = {
    _listeners: [],

    init: function () {
        this._registerListeners();
        // Always seed via REST on every page navigation.  On a page switch
        // the WS is already connected and trishul:ws:full_state was sent
        // before this module's listeners were registered, so we cannot rely
        // on WS events for the initial paint.  WS events then take over for
        // live updates.
        this._loadAllViaRest();
    },

    destroy: function () {
        this._listeners.forEach(function (pair) {
            window.removeEventListener(pair[0], pair[1]);
        });
        this._listeners = [];
    },

    _on: function (type, fn) {
        window.addEventListener(type, fn);
        this._listeners.push([type, fn]);
    },

    _registerListeners: function () {
        var self = this;

        // Full state on connect
        this._on('trishul:ws:full_state', function (e) {
            self._applyStatus(e.detail.simulator, e.detail.traps);
            if (e.detail.mibs)  self._applyMibs(e.detail.mibs);
            if (e.detail.stats) self._applyStats(e.detail.stats);
        });

        // Lightweight status on lifecycle change (start/stop)
        this._on('trishul:ws:status', function (e) {
            self._applyStatus(e.detail.simulator, e.detail.traps);
        });

        // MIB mutation broadcast
        this._on('trishul:ws:mibs', function (e) {
            if (e.detail.mibs) self._applyMibs(e.detail.mibs);
        });

        // Stats broadcast — sent after any stats write
        this._on('trishul:ws:stats', function (e) {
            if (e.detail.data) self._applyStats(e.detail.data);
        });

        // Re-seed everything via REST after every WS reconnect
        // (full_state arrives moments later but REST is faster for status)
        this._on('trishul:ws:open', function () {
            self._loadAllViaRest();
        });
    },

    _applyStatus: function (sim, trap) {
        var simEl = document.getElementById('stat-simulator');
        var recEl = document.getElementById('stat-receiver');

        if (simEl) {
            simEl.textContent = sim && sim.running ? 'Online' : 'Offline';
            simEl.className   = 'mb-0 ' + (sim && sim.running ? 'text-success fw-bold' : 'text-secondary');
        }
        if (recEl) {
            recEl.textContent = trap && trap.running ? 'Running' : 'Stopped';
            recEl.className   = 'mb-0 ' + (trap && trap.running ? 'text-info fw-bold' : 'text-secondary');
        }
    },

    _applyMibs: function (mibs) {
        var mibEl  = document.getElementById('stat-mibs');
        var trapEl = document.getElementById('stat-traps');
        if (mibEl)  { mibEl.textContent  = mibs.loaded         != null ? mibs.loaded         : 0; mibEl.className  = 'mb-0'; }
        if (trapEl) { trapEl.textContent = mibs.traps_available != null ? mibs.traps_available : 0; trapEl.className = 'mb-0'; }
    },

    _applyStats: function (stats) {
        if (!stats) return;
        var sim    = stats.simulator || {};
        var traps  = stats.traps     || {};
        var walker = stats.walker    || {};
        var mibs   = stats.mibs      || {};

        function set(id, val) {
            var el = document.getElementById(id);
            if (el) el.textContent = (val != null) ? val : '\u2014';
        }

        set('act-snmp-requests', sim.snmp_requests_served);
        set('act-oids-loaded',   sim.oids_loaded);
        set('act-traps-recv',    traps.traps_received_total);
        set('act-traps-sent',    traps.traps_sent_total);
        set('act-walks',         walker.walks_executed);
        set('act-oids-returned', walker.oids_returned);
        set('act-mibs-uploaded', mibs.upload_count);
        set('act-mibs-reloaded', mibs.reload_count);
    },

    resetStats: async function () {
        if (!confirm('Reset all activity counters?\n\nThis cannot be undone.')) return;
        try {
            var res = await fetch('/api/stats/', { method: 'DELETE' });
            if (!res.ok) throw new Error('HTTP ' + res.status);
            // Zero out UI immediately without waiting for a WS push
            this._applyStats({
                simulator: { snmp_requests_served: 0, oids_loaded: 0 },
                traps:     { traps_received_total: 0, traps_sent_total: 0 },
                walker:    { walks_executed: 0, oids_returned: 0 },
                mibs:      { upload_count: 0, reload_count: 0 }
            });
            TrishulUtils.showNotification('Activity stats reset', 'success');
        } catch (e) {
            TrishulUtils.showNotification('Reset failed: ' + e.message, 'error');
        }
    },

    // ---------------------------------------------------------------------------
    // REST helpers
    // ---------------------------------------------------------------------------

    // Full REST seed — calls the three focused helpers in parallel.
    // Used on init() and on every WS reconnect.
    _loadAllViaRest: function () {
        this._loadStatusViaRest();
        this._loadMibsViaRest();
        this._loadStatsViaRest();
    },

    // Simulator + trap-receiver running state
    _loadStatusViaRest: async function () {
        try {
            var results = await Promise.all([
                fetch('/api/simulator/status').catch(function () { return null; }),
                fetch('/api/traps/status').catch(function ()     { return null; })
            ]);
            var simRes  = results[0];
            var trapRes = results[1];
            if (simRes && simRes.ok && trapRes && trapRes.ok) {
                this._applyStatus(await simRes.json(), await trapRes.json());
            }
        } catch (e) {}
    },

    // MIB loaded + traps-available counts
    _loadMibsViaRest: async function () {
        try {
            var res = await fetch('/api/mibs/status');
            if (!res.ok) return;
            var d = await res.json();
            var trapsAvail = (d.mibs || []).reduce(function (s, m) { return s + (m.traps || 0); }, 0);
            this._applyMibs({ loaded: d.loaded || 0, traps_available: trapsAvail });
        } catch (e) {}
    },

    // All activity counters
    _loadStatsViaRest: async function () {
        try {
            var res = await fetch('/api/stats/');
            if (!res.ok) return;
            this._applyStats(await res.json());
        } catch (e) {}
    },

    showError: function (elementId, text) {
        var el = document.getElementById(elementId);
        if (el) { el.textContent = text; el.className = 'mb-0 text-danger'; }
    }
};
