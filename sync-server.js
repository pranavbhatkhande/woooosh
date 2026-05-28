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

// In-memory store (swap for Redis/KV in production)
const store = new Map();

const ACCOUNT_ID_RE = /^[a-f0-9]{32}$/;

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
        const entry = store.get(accountId);
        send(res, 200, entry ? { exists: true, ...entry } : { exists: false });
        return;
    }

    if (req.method === 'PUT') {
        try {
            const body = await readBody(req);
            const { ciphertext, iv, version } = body;
            if (!ciphertext || !iv || !version) { send(res, 400, { error: 'Missing fields' }); return; }
            store.set(accountId, { ciphertext, iv, version, savedAt: Date.now() });
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
    console.log('Zero-knowledge: server stores only encrypted blobs.\n');
});
