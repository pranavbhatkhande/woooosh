// Pull accepted AI-judge answers out of Netlify Blobs for the offline bank.
//
//   NETLIFY_SITE_ID=... NETLIFY_AUTH_TOKEN=... node deploy/pull-judged.mjs
//   python -m pipeline import-judged

import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { getStore } from "@netlify/blobs";

const siteID = process.env.NETLIFY_SITE_ID || "";
const token = process.env.NETLIFY_AUTH_TOKEN || process.env.NETLIFY_BLOB_TOKEN || "";
if (!siteID || !token) {
  console.error("Set NETLIFY_SITE_ID and NETLIFY_AUTH_TOKEN (a token that can read blobs).");
  process.exit(1);
}

const store = getStore({ name: "judge-accepted", siteID, token });
const records = [];
for await (const page of store.list({ paginate: true })) {
  for (const blob of page.blobs || []) {
    const data = await store.get(blob.key, { type: "json" });
    if (data && data.promptId && data.canonical) records.push(data);
  }
}

const dest = path.resolve("pipeline/cache/judged.json");
await mkdir(path.dirname(dest), { recursive: true });
await writeFile(dest, `${JSON.stringify(records, null, 2)}\n`);
console.log(`wrote ${records.length} judged answers to ${dest}`);
