/**
 * js/modules/utils.js
 * ~~~~~~~~~~~~~~~~~~~
 * Shared utility functions used across all Trishul modules.
 * Loaded FIRST (before ws-client.js and all module scripts) so every
 * module can call TrishulUtils.* without any import ceremony.
 */
window.TrishulUtils = {

    /**
     * Convert an ISO timestamp string to a human-readable relative time.
     * Returns strings like: 'just now', '34s ago', '5m ago', '2h ago',
     * '3d ago', or a locale date string for anything older than a week.
     *
     * @param {string|null} dateString  ISO 8601 timestamp (or null/undefined)
     * @returns {string}
     */
    formatRelativeTime: function(dateString) {
        if (!dateString) return '--';
        try {
            const date    = new Date(dateString);
            const now     = new Date();
            const diffMs  = now - date;
            const diffSec = Math.floor(diffMs / 1000);
            const diffMin = Math.floor(diffSec / 60);
            const diffHr  = Math.floor(diffMin / 60);
            const diffDay = Math.floor(diffHr  / 24);

            if (diffSec < 5)   return 'just now';
            if (diffSec < 60)  return `${diffSec}s ago`;
            if (diffMin < 60)  return `${diffMin}m ago`;
            if (diffHr  < 24)  return `${diffHr}h ago`;
            if (diffDay < 7)   return `${diffDay}d ago`;
            return date.toLocaleDateString();
        } catch (_) {
            return '--';
        }
    },

    /**
     * Convert a duration in whole seconds to a compact human-readable string.
     * Examples:
     *   45      → '45s'
     *   125     → '2m 5s'
     *   3600    → '1h'
     *   3900    → '1h 5m'
     *   90000   → '1d 1h'
     *   86400   → '1d'
     *
     * @param {number|null} seconds  Duration in seconds (null/undefined → '--')
     * @returns {string}
     */
    formatUptime: function(seconds) {
        if (seconds == null || seconds < 0) return '--';
        seconds = Math.floor(seconds);
        if (seconds < 60) {
            return `${seconds}s`;
        }
        if (seconds < 3600) {
            const m = Math.floor(seconds / 60);
            const s = seconds % 60;
            return s > 0 ? `${m}m ${s}s` : `${m}m`;
        }
        if (seconds < 86400) {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            return m > 0 ? `${h}h ${m}m` : `${h}h`;
        }
        const d = Math.floor(seconds / 86400);
        const h = Math.floor((seconds % 86400) / 3600);
        return h > 0 ? `${d}d ${h}h` : `${d}d`;
    },
};
