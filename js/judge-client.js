// The browser never calls the model directly. Transport failures, timeouts,
// and rate limits are a fallback signal. A valid:false verdict is a reject.

const PROBE_MS = 2500;
// Cold model load is about 5s. The function waits 8s and Netlify allows 10s.
const JUDGE_MS = 9000;

export function classifyJudgeResponse(responseOk, data) {
  if (!responseOk || !data || data.enabled === false || data.error) return { status: "fallback" };
  if (data.valid === true && data.tier) return { status: "scored", data };
  if (data.valid === false) return { status: "reject" };
  return { status: "fallback" };
}

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

// Fire and forget. Starting a round loads the model during the preview
// so the first real answer is less likely to pay the cold-start cost.
export function warmJudge() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), JUDGE_MS);
  fetch("/api/judge", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ warm: true }),
    signal: controller.signal,
  })
    .catch(() => {})
    .finally(() => clearTimeout(timer));
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
    let data = null;
    try {
      data = await response.json();
    } catch {
      data = null;
    }
    return classifyJudgeResponse(response.ok, data);
  } catch {
    return { status: "fallback" };
  } finally {
    clearTimeout(timer);
    if (signal) signal.removeEventListener("abort", stop);
  }
}
