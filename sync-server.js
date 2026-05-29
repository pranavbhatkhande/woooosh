/**
 * woooosh sync server — zero-knowledge key-value store.
 * Stores only: { account_id → encrypted_blob }.
 * Never sees plaintext tasks or any user identity.
 *
 * Endpoints:
 *   GET  /sync/:id          → { exists, ciphertext, iv, version }
 *   PUT  /sync/:id          body: { ciphertext, iv, version }
 *   DELETE /sync/:id
 *
 * Run: node sync-server.js
 */

import http from 'http';

// In-memory store (swap for Redis/KV in production).
// Each entry holds an append-only list of writes, each tagged with the time it
// becomes globally visible. This lets us faithfully simulate eventual
// consistency for testing (see STALE_MS below).
const store = new Map();   // accountId → [ { value, visibleAt } ]

// When > 0, a write only becomes visible to GETs STALE_MS later — mimicking an
// eventually-consistent backend (e.g. Netlify Blobs with its default
// consistency). Set to 0 (default) for strong consistency, which is what the
// production Netlify function now uses (consistency: "strong").
const STALE_MS = Number(process.env.SYNC_STALE_MS || 0);

const ACCOUNT_ID_RE = /^[a-f0-9]{32}$/;

// Returns the newest write that has already become visible, honoring the
// simulated staleness window. With STALE_MS = 0 every write is visible
// immediately, so this always returns the latest write (strong consistency).
function visibleEntry(accountId) {
    const writes = store.get(accountId);
    if (!writes || writes.length === 0) return null;
    const now = Date.now();
    for (let i = writes.length - 1; i >= 0; i--) {
        if (writes[i].visibleAt <= now) return writes[i].value;
    }
    return null;   // nothing has propagated yet
}

function send(res, status, body) {
    const payload = JSON.stringify(body);
    res.writeHead(status, {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload),
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    });
    res.end(payload);
}

function readBody(req) {
    return new Promise((resolve, reject) => {
        let raw = '';
        req.setEncoding('utf8');
        req.on('data', c => { raw += c; if (raw.length > 1_000_000) reject(new Error('too large')); });
        req.on('end', () => {
            try { resolve(JSON.parse(raw)); }
            catch (e) { reject(e); }
        });
        req.on('error', reject);
    });
}

const server = http.createServer(async (req, res) => {
    // CORS preflight
    if (req.method === 'OPTIONS') { send(res, 200, {}); return; }

    const match = req.url.match(/^\/sync\/([a-zA-Z0-9_-]{32,64})$/);
    if (!match) { send(res, 404, { error: 'Not found' }); return; }

    const accountId = match[1];

    if (req.method === 'GET') {
        const entry = visibleEntry(accountId);
        send(res, 200, entry ? { exists: true, ...entry } : { exists: false });
        return;
    }

    if (req.method === 'PUT') {
        try {
            const body = await readBody(req);
            const { ciphertext, iv, version } = body;
            if (!ciphertext || !iv || !version) { send(res, 400, { error: 'Missing fields' }); return; }
            const writes = store.get(accountId) || [];
            writes.push({
                value: { ciphertext, iv, version, savedAt: Date.now() },
                visibleAt: Date.now() + STALE_MS,
            });
            store.set(accountId, writes);
            console.log(`[sync] stored ${accountId.slice(0,8)}… v${version}`);
            send(res, 200, { ok: true });
        } catch (e) {
            send(res, 400, { error: 'Bad request' });
        }
        return;
    }

    if (req.method === 'DELETE') {
        store.delete(accountId);
        send(res, 200, { ok: true });
        return;
    }

    send(res, 405, { error: 'Method not allowed' });
});

const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
    console.log(`woooosh sync server  http://localhost:${PORT}`);
    console.log('Zero-knowledge: server stores only encrypted blobs.');
    console.log(STALE_MS > 0
        ? `⚠ Simulating EVENTUAL consistency: ${STALE_MS}ms stale-read window.\n`
        : 'Strong consistency (reads always see the latest write).\n');
});
