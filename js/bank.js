// Lazy shards. The index is small; a round only fetches the shards it needs.

export async function loadIndex() {
  const response = await fetch("/data/index.json", { cache: "no-cache" });
  if (!response.ok) throw new Error("bank index");
  return response.json();
}

const shards = new Map();

export async function loadPrompts(index, ids) {
  const need = new Set(ids);
  const found = new Map();
  for (const shard of index.shards || []) {
    if (!(shard.ids || []).some((id) => need.has(id))) continue;
    let prompts = shards.get(shard.file);
    if (!prompts) {
      const response = await fetch(`/${shard.file}`, { cache: "no-cache" });
      if (!response.ok) throw new Error(shard.file);
      prompts = await response.json();
      shards.set(shard.file, prompts);
    }
    for (const prompt of prompts) {
      if (need.has(prompt.id)) found.set(prompt.id, prompt);
    }
  }
  return ids.map((id) => found.get(id)).filter(Boolean);
}

export function allIds(index) {
  const ids = [];
  for (const shard of index.shards || []) ids.push(...(shard.ids || []));
  return ids;
}
