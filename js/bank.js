async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-cache" });
  if (!response.ok) throw new Error(`${url} returned ${response.status}`);
  return response.json();
}

export async function loadBank() {
  const [index, daily] = await Promise.all([
    fetchJson("/data/index.json"),
    fetchJson("/data/daily.json"),
  ]);
  const byId = new Map();
  for (const shard of index.shards || []) {
    for (const id of shard.ids || []) byId.set(id, shard.file);
  }
  const cache = new Map();

  async function promptsFor(ids) {
    const files = [...new Set(ids.map((id) => byId.get(id)).filter(Boolean))];
    await Promise.all(files.map(async (file) => {
      if (cache.has(file)) return;
      const payload = await fetchJson(`/data/${file}`);
      cache.set(file, payload.prompts || []);
    }));
    const all = new Map();
    for (const list of cache.values()) {
      for (const prompt of list) all.set(prompt.id, prompt);
    }
    const prompts = ids.map((id) => all.get(id)).filter(Boolean);
    if (prompts.length !== ids.length) {
      const missing = ids.filter((id) => !all.has(id));
      throw new Error(`Missing prompts: ${missing.join(", ")}`);
    }
    return prompts;
  }

  return {
    version: index.version,
    count: index.promptCount || byId.size,
    ids: [...byId.keys()],
    daily,
    promptsFor,
  };
}
