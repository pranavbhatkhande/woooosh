/**
 * woooosh sync — Netlify Function v2
 * Zero-knowledge KV: stores only { account_id → encrypted_blob }.
 * Backed by Netlify Blobs for durable, cross-deploy persistence.
 *
 * Routes (via config.path):
 *   GET    /sync/:id  → { exists, ciphertext, iv, version }
 *   PUT    /sync/:id  body: { ciphertext, iv, version }
 *   DELETE /sync/:id
 */

import { getStore } from "@netlify/blobs";

const CORS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Methods": "GET, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json",
};

export default async (req, context) => {
    if (req.method === "OPTIONS") {
        return new Response("{}", { status: 200, headers: CORS });
    }

    const id = context.params.id;
    if (!id || !/^[a-zA-Z0-9_-]{32,64}$/.test(id)) {
        return Response.json({ error: "Not found" }, { status: 404, headers: CORS });
    }

    const store = getStore("woooosh-sync");

    if (req.method === "GET") {
        const entry = await store.get(id, { type: "json" }).catch(() => null);
        return Response.json(
            entry ? { exists: true, ...entry } : { exists: false },
            { headers: CORS }
        );
    }

    if (req.method === "PUT") {
        let body;
        try { body = await req.json(); } catch {
            return Response.json({ error: "Bad request" }, { status: 400, headers: CORS });
        }
        const { ciphertext, iv, version } = body || {};
        if (!ciphertext || !iv || !version) {
            return Response.json({ error: "Missing fields" }, { status: 400, headers: CORS });
        }
        if (JSON.stringify({ ciphertext, iv, version }).length > 1_000_000) {
            return Response.json({ error: "Payload too large" }, { status: 413, headers: CORS });
        }
        await store.setJSON(id, { ciphertext, iv, version, savedAt: Date.now() });
        return Response.json({ ok: true }, { headers: CORS });
    }

    if (req.method === "DELETE") {
        await store.delete(id).catch(() => null);
        return Response.json({ ok: true }, { headers: CORS });
    }

    return Response.json({ error: "Method not allowed" }, { status: 405, headers: CORS });
};

export const config = { path: "/sync/:id" };
