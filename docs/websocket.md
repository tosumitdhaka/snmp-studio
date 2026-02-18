# WebSocket API

**Endpoint:** `ws://host/api/ws?token=<session_token>`

Provides real-time server-push for simulator status, trap receiver status,
newly received traps, and stats updates. Replaces polling in the frontend.

---

## Authentication

Pass the session token as a query parameter:
```
ws://localhost:8000/api/ws?token=<token-from-POST-/api/login>
```

If the token is missing or invalid the server closes the connection
immediately with code `4001` (policy violation).

---

## Connection flow

```
Client                          Server
  |                               |
  |--- WS handshake ?token=... -->|
  |<-- {type: "full_state", ...} -|  (sent immediately on connect)
  |                               |
  |           ...                 |  (server pushes on state changes)
  |<-- {type: "status", ...} -----|  (simulator/trap start or stop)
  |<-- {type: "trap", ...} -------|  (new trap received)
  |<-- {type: "stats", ...} ------|  (stats update)
  |                               |
  |--- "ping" ------------------->|  (client every 30s)
  |<-- "pong" --------------------|  (server response)
```

---

## Message Reference

### `full_state` — sent once on connect

```json
{
  "type": "full_state",
  "simulator": {
    "running": true,
    "pid": 42,
    "port": 1061,
    "community": "public",
    "uptime": "0:12:34"
  },
  "traps": {
    "running": true,
    "pid": 43,
    "port": 1162,
    "resolve_mibs": true
  },
  "stats": {
    "simulator": { "start_count": 2, "stop_count": 1, ... },
    "traps":     { "receiver_start_count": 2, "traps_received_total": 17, ... },
    "walker":    { "walks_executed": 5, "walks_failed": 0, "oids_returned": 32 },
    "mibs":      { "reload_count": 1, "upload_count": 1, "delete_count": 0,
                   "loaded_mibs": 1, "failed_mibs": 0, "total_mibs": 1 }
  }
}
```

### `status` — pushed on lifecycle changes

Triggered when: simulator or trap receiver starts, stops, or restarts.

```json
{
  "type": "status",
  "simulator": { "running": false, "pid": null, "port": null, "community": null },
  "traps":     { "running": true,  "pid": 43,   "port": 1162, "resolve_mibs": true }
}
```

### `trap` — pushed when a new trap arrives

Triggered by: `trap_receiver` worker → UDP datagram → main process → broadcast.

```json
{
  "type": "trap",
  "trap": {
    "timestamp": 1739890234.123,
    "time_str":  "2026-02-18 21:30:34",
    "source":    "192.168.1.10:52341",
    "trap_type": "linkDown",
    "resolved":  true,
    "varbinds": [
      { "oid": "1.3.6.1.2.1.2.2.1.1.1",
        "name": "IF-MIB::ifIndex.1",
        "value": "1",
        "resolved": true }
    ]
  }
}
```

### `stats` — pushed after stats updates

Triggered after: start/stop/restart of simulator or trap receiver.

```json
{
  "type": "stats",
  "data": {
    "simulator": { "start_count": 3, ... },
    "traps":     { "receiver_start_count": 2, ... },
    "walker":    { "walks_executed": 5, ... },
    "mibs":      { "reload_count": 1, ... }
  }
}
```

---

## Keepalive

The client should send a `"ping"` text message every 30 seconds.
The server responds with `"pong"`.
This prevents nginx from closing the idle connection (nginx default idle
timeout is 60s; the `/api/ws` location block sets `proxy_read_timeout 3600s`
but the ping also serves as a connection health check).

---

## Internal architecture

```
FastAPI process                         Worker subprocess
┌─────────────────────────────┐         ┌──────────────────────┐
│ ConnectionManager           │         │ trap_receiver.py     │
│  active: [ws1, ws2, ...]    │         │                      │
│                             │◄──UDP───│  _send_ws_datagram() │
│ _UDPListenerProtocol        │ loopback│  (127.0.0.1:19876)   │
│  port 19876                 │         └──────────────────────┘
│    │                        │
│    └─► manager.broadcast()  │
│         sends to all ws     │
└─────────────────────────────┘
```

### Why UDP loopback instead of a file watcher or Redis?

- **No extra dependencies** — stdlib `socket` only
- **Sub-millisecond latency** — loopback UDP is essentially zero-copy in the kernel
- **Fire-and-forget** — if the main process isn't listening yet, the datagram is
  silently dropped; the trap is already on disk so nothing is lost
- **Simple** — ~10 lines of code in the worker, ~30 lines in the listener

---

## Test with wscat

```bash
# Install
npm install -g wscat

# 1. Get a session token
TOKEN=$(curl -s -X POST http://localhost:8000/api/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

# 2. Connect
wscat -c "ws://localhost:8000/api/ws?token=$TOKEN"

# You will immediately receive a full_state message.
# Then start/stop the simulator or send a trap and watch the push events.
```

---

## Frontend integration (Phase 9 — frontend branch)

Frontend changes are tracked in a separate branch `phase-9-frontend`.
The polling-to-WebSocket migration plan:

| Module | Polling removed | WS events consumed |
|---|---|---|
| `dashboard.js` | `setInterval 30s` ×3 HTTP | `full_state`, `status`, `stats` |
| `simulator.js` | `setInterval 10s` ×1 HTTP | `full_state`, `status` |
| `traps.js` | `setInterval 3s` ×2 HTTP | `full_state`, `status`, `trap` |
