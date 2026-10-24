// The browser never calls the model directly. If the function is disabled,
// slow, or unhappy, the round just keeps the bank rules.

const PROBE_MS = 2500;
const JUDGE_MS = 4000;

export async function probeJudge() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), PROBE_MS);
  try {
    const response = await fetch("/api/judge", { signal: controller.signal, cache: "no-store" });
    if (!response.ok) return false;
    const data = await response.json();
    return Boolean(data.enabled);
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

// Default on only when the server says the judge exists and the player
// has not switched it off.
export function judgePreferred(saved, available) {
  if (!available) return false;
  return saved !== false;
}

export async function askJudge(promptId, answer, signal) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), JUDGE_MS);
  const stop = () => controller.abort();
  if (signal) {
    if (signal.aborted) controller.abort();
    else signal.addEventListener("abort", stop, { once: true });
  }
  try {
    const response = await fetch("/api/judge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ promptId, answer }),
      signal: controller.signal,
    });
    if (!response.ok) return null;
    const data = await response.json();
    if (!data || !data.enabled || !data.valid || !data.tier) return null;
    return data;
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
    if (signal) signal.removeEventListener("abort", stop);
  }
}
