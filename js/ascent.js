// The ascent scene is paint only. It never waits, never locks a prompt,
// and never touches the round clock. Callers keep scoring and the pause
// in the engine and in submitAnswer.

import { TIERS } from "./tiers.js";

const CEILING_KM = 700;

export const TIER_RANK = Object.fromEntries(TIERS.map((tier, index) => [tier.id, index + 1]));

const TIER_COLOR = {
  taxi: "#d7d2c8",
  climb: "#3ddc84",
  burn: "#f5c542",
  stall: "#ff8a3d",
  apogee: "#c084fc",
  escape: "#7ee7ff",
};

// Particle counts follow the point values. STALL is worth more than BURN
// and uses a flat shape so the trap still reads as its own moment.
export const BURST_COUNT = {
  taxi: 8,
  climb: 14,
  burn: 22,
  stall: 26,
  apogee: 34,
  escape: 48,
};

const SCORE_STOPS = [
  { km: 0, t: 0.05 },
  { km: 35, t: 0.28 },
  { km: 70, t: 0.42 },
  { km: 175, t: 0.58 },
  { km: 280, t: 0.72 },
  { km: 420, t: 0.84 },
  { km: 700, t: 0.94 },
];

const FLIGHT_LINE = {
  low: "Clear of the pad.",
  mid: "Through the weather.",
  high: "High orbit.",
  escape: "Escape velocity.",
};

const FINALE_COLORS = ["#f5c542", "#7ee7ff", "#c084fc", "#ff8a3d", "#3ddc84"];

function lerpStops(stops, km) {
  const value = Math.max(0, Math.min(CEILING_KM, Number(km) || 0));
  let index = 1;
  while (index < stops.length && value > stops[index].km) index += 1;
  const start = stops[index - 1];
  const end = stops[index] || start;
  const span = end.km - start.km || 1;
  return start.t + ((value - start.km) / span) * (end.t - start.t);
}

export function scoreProgress(km) {
  return lerpStops(SCORE_STOPS, km);
}

// One answer of a tier lifts the rocket onto that rung, even when the
// kilometer total is still low. Stacked points can climb past it.
export function tierRung(tier) {
  const rank = TIER_RANK[tier] || 0;
  if (!rank) return 0;
  return 0.05 + (rank / 6) * 0.89;
}

export function rocketProgress(km, peakTierId) {
  return Math.max(scoreProgress(km), tierRung(peakTierId));
}

export function peakTier(rounds) {
  let best = null;
  let rank = 0;
  for (const round of rounds || []) {
    const next = TIER_RANK[round && round.tier] || 0;
    if (next > rank) {
      rank = next;
      best = round.tier;
    }
  }
  return best;
}

export function burstCount(tier) {
  return BURST_COUNT[tier] || 0;
}

export function burstShape(kind) {
  if (kind === "stall") return "flat";
  if (kind === "miss") return "fall";
  if (kind === "reject") return "cough";
  return "radial";
}

export function finalePops(km, peakTierId) {
  if ((Number(km) || 0) <= 0 && !peakTierId) return 1;
  const t = rocketProgress(km, peakTierId);
  const score = Math.max(0, Math.min(CEILING_KM, Number(km) || 0)) / CEILING_KM;
  return Math.max(2, Math.round(2 + t * 6 + score * 4));
}

export function flightMood(km, peakTierId) {
  const t = rocketProgress(km, peakTierId);
  if (t >= tierRung("escape") - 1e-4) return "escape";
  if (t >= tierRung("apogee") - 1e-4) return "high";
  if (t >= tierRung("climb") - 1e-4) return "mid";
  return "low";
}

export function flightLine(mood) {
  return FLIGHT_LINE[mood] || FLIGHT_LINE.low;
}

function hexAlpha(hex, alpha) {
  const value = parseInt(hex.slice(1), 16);
  const r = (value >> 16) & 255;
  const g = (value >> 8) & 255;
  const b = value & 255;
  return `rgba(${r},${g},${b},${alpha})`;
}

function mix(from, to, t) {
  const a = parseInt(from.slice(1), 16);
  const b = parseInt(to.slice(1), 16);
  const u = Math.max(0, Math.min(1, t));
  const channel = (shift) => Math.round(((a >> shift) & 255) * (1 - u) + ((b >> shift) & 255) * u);
  return `rgb(${channel(16)},${channel(8)},${channel(0)})`;
}

function mulberry32(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) | 0;
    let t = Math.imul(state ^ (state >>> 15), 1 | state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function makeStars(rng, count, depth) {
  const stars = [];
  for (let i = 0; i < count; i += 1) {
    stars.push({
      x: rng(),
      y: rng(),
      depth,
      size: depth === 2 ? 1.7 : depth === 1 ? 1.15 : 0.75,
      alpha: 0.22 + rng() * 0.5,
      phase: rng() * Math.PI * 2,
    });
  }
  return stars;
}

function prefersReduced() {
  return typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function mountAscent(canvas, initial) {
  const ctx = canvas.getContext("2d", { alpha: false });
  if (!ctx) return { set() {}, kick() {}, destroy() {} };

  const rng = mulberry32(0x574f4f53);
  const stars = [
    ...makeStars(rng, 42, 0),
    ...makeStars(rng, 24, 1),
    ...makeStars(rng, 12, 2),
  ];
  const motes = makeStars(rng, 14, 0);
  const particles = [];
  const rings = [];
  const trail = [];

  const state = {
    altitude: 0,
    displayT: 0.05,
    toT: 0.05,
    mood: "",
    tier: null,
    answerTier: null,
    moodAt: 0,
    pending: "",
    kickUntil: 0,
    flash: 0,
    finaleLeft: 0,
    finaleTotal: 0,
    finaleNext: 0,
    staticMark: null,
    easeMs: 280,
  };

  let viewW = 0;
  let viewH = 0;
  let dpr = 1;
  let alive = true;
  let raf = 0;
  let lastNow = 0;
  let lastTrail = 0;
  let reduced = prefersReduced();
  let observer = null;

  const media = typeof matchMedia === "function" ? matchMedia("(prefers-reduced-motion: reduce)") : null;
  const onMotion = (event) => {
    reduced = event.matches;
    if (reduced) state.displayT = state.toT;
    poke();
  };
  if (media && media.addEventListener) media.addEventListener("change", onMotion);

  function yAt(t) {
    const pad = 20;
    return pad + (1 - t) * (viewH - pad * 2);
  }

  function rocketX() {
    return Math.max(86, Math.min(viewW * 0.46, viewW - 96));
  }

  function pose(t) {
    return { x: rocketX(), y: yAt(t) };
  }

  function pushParticle(particle) {
    particles.push(particle);
    if (particles.length > 96) particles.splice(0, particles.length - 96);
  }

  function spawnBurst(tier, x, y) {
    const count = burstCount(tier);
    if (!count) return;
    const color = TIER_COLOR[tier] || "#f5c542";
    const rank = TIER_RANK[tier] || 1;
    const shape = burstShape(tier);
    for (let i = 0; i < count; i += 1) {
      let angle = (Math.PI * 2 * i) / count;
      let speed = (0.7 + Math.random() * 0.9) * (1 + rank * 0.06);
      if (shape === "flat") {
        angle = (i % 2 === 0 ? 0 : Math.PI) + (Math.random() - 0.5) * 0.45;
        speed = 1.5 + Math.random() * 0.8;
      }
      pushParticle({
        x,
        y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        life: 1,
        decay: tier === "escape" ? 0.01 : tier === "taxi" ? 0.034 : 0.02,
        color,
        size: tier === "escape" ? 3 : tier === "apogee" ? 2.2 : 1.6,
        streak: tier === "escape" || tier === "apogee",
      });
    }
    if (tier === "apogee" || tier === "escape") {
      rings.push({ x, y, r: 6, life: 1, wait: 0, color, speed: tier === "escape" ? 2.5 : 1.6 });
    }
    if (tier === "escape") {
      rings.push({ x, y, r: 4, life: 1, wait: 120, color: "#e7eef8", speed: 1.9 });
      state.flash = 0.55;
    }
  }

  function spawnFall(x, y, count, decay) {
    for (let i = 0; i < count; i += 1) {
      pushParticle({
        x,
        y,
        vx: (Math.random() - 0.5) * 1.4,
        vy: 0.35 + Math.random() * 1.3,
        life: 1,
        decay,
        color: "#8b93a7",
        size: 1.5,
      });
    }
  }

  function spawnPop(x, y, color, count) {
    for (let i = 0; i < count; i += 1) {
      const angle = (Math.PI * 2 * i) / count + Math.random() * 0.2;
      const speed = 0.9 + Math.random() * 1.8;
      pushParticle({
        x,
        y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        life: 1,
        decay: 0.01,
        color,
        size: 3.2,
        streak: true,
      });
    }
    rings.push({ x, y, r: 6, life: 1, wait: 0, color, speed: 2.1 });
  }

  function arm(mood) {
    state.moodAt = performance.now();
    if (mood === "hit") state.pending = "hit";
    else if (mood === "miss") state.pending = "miss";
    else if (mood === "finale") {
      state.finaleTotal = finalePops(state.altitude, state.tier);
      state.finaleLeft = state.finaleTotal;
      state.finaleNext = performance.now() + 120;
    }
  }

  function spawnReject(x, y) {
    for (let i = 0; i < 6; i += 1) {
      pushParticle({
        x,
        y,
        vx: (i % 2 === 0 ? -1 : 1) * (1.2 + Math.random()),
        vy: (Math.random() - 0.5) * 0.6,
        life: 1,
        decay: 0.08,
        color: "#ff5d73",
        size: 1.6,
      });
    }
  }

  function consumePending() {
    if (!state.pending || viewW < 2) return;
    const dest = pose(state.toT);
    if (reduced) {
      state.staticMark = { kind: state.pending, tier: state.answerTier, x: dest.x, y: dest.y };
      state.pending = "";
      return;
    }
    if (state.pending === "hit") spawnBurst(state.answerTier, dest.x, dest.y);
    else if (state.pending === "miss") spawnFall(dest.x, dest.y, 10, 0.05);
    else if (state.pending === "reject") spawnReject(dest.x, dest.y);
    state.pending = "";
  }

  function drawStaticMark(mark) {
    if (!mark) return;
    const shape = mark.kind === "hit" ? burstShape(mark.tier) : burstShape(mark.kind);
    const color = mark.kind === "hit" ? (TIER_COLOR[mark.tier] || "#f5c542") : mark.kind === "reject" ? "#ff5d73" : "#8b93a7";
    const count = mark.kind === "hit" ? Math.min(12, burstCount(mark.tier) || 8) : 6;
    ctx.fillStyle = color;
    for (let i = 0; i < count; i += 1) {
      let angle = (Math.PI * 2 * i) / count;
      let dist = 7 + (i % 4);
      if (shape === "flat" || shape === "cough") angle = i % 2 === 0 ? 0 : Math.PI;
      if (shape === "fall") {
        angle = Math.PI / 2;
        dist = 4 + i * 1.4;
      }
      ctx.fillRect(mark.x + Math.cos(angle) * dist, mark.y + Math.sin(angle) * dist, 2, 2);
    }
  }

  function resize() {
    const parent = canvas.parentElement;
    if (!parent) return false;
    const rect = parent.getBoundingClientRect();
    if (rect.width < 2 || rect.height < 2) return false;
    const next = Math.min(2, window.devicePixelRatio || 1);
    const width = Math.round(rect.width * next);
    const height = Math.round(rect.height * next);
    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width;
      canvas.height = height;
    }
    viewW = rect.width;
    viewH = rect.height;
    dpr = next;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return true;
  }

  function drawSky(t) {
    const gradient = ctx.createLinearGradient(0, 0, 0, viewH);
    gradient.addColorStop(0, mix("#10243f", "#05060c", t));
    gradient.addColorStop(0.55, mix("#1d5278", "#12182c", t));
    gradient.addColorStop(1, mix("#d26538", "#16324a", t));
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, viewW, viewH);
    const limb = viewH * (0.8 - t * 0.52);
    ctx.fillStyle = `rgba(255,138,61,${0.3 * (1 - t)})`;
    ctx.fillRect(0, limb, viewW, Math.max(0, viewH - limb));
    ctx.fillStyle = `rgba(126,231,255,${0.08 + t * 0.14})`;
    ctx.beginPath();
    ctx.ellipse(viewW / 2, limb, viewW * 0.72, 14, 0, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawStars(now, t) {
    const drift = 0.35 + t * 1.35;
    for (const star of stars) {
      const speed = (5 + star.depth * 11) * drift;
      const travel = reduced ? 0 : (now / 1000) * speed;
      const y = ((star.y * viewH + travel) % viewH + viewH) % viewH;
      let alpha = star.alpha;
      if (!reduced) alpha *= 0.8 + 0.2 * Math.sin(now / 520 + star.phase);
      ctx.globalAlpha = alpha;
      ctx.fillStyle = star.depth === 2 ? "#d8f7ff" : "#ffffff";
      ctx.fillRect(star.x * viewW, y, star.size, star.size);
    }
    ctx.globalAlpha = 1;
    if (t > 0.82) return;
    const fade = 1 - t;
    for (const mote of motes) {
      const travel = reduced ? 0 : (now / 1000) * 12 * fade;
      const y = ((viewH * (0.5 + mote.y * 0.5) + travel) % viewH + viewH) % viewH;
      if (y < viewH * 0.42) continue;
      ctx.globalAlpha = 0.18 * fade * mote.alpha;
      ctx.fillStyle = "#ffb07a";
      ctx.fillRect(mote.x * viewW, y, 1.5, 1.5);
    }
    ctx.globalAlpha = 1;
  }

  function drawRails(t) {
    ctx.font = "600 10px 'IBM Plex Mono', ui-monospace, monospace";
    const spacing = ctx.constructor && ctx.constructor.prototype;
    if (spacing && "letterSpacing" in spacing) ctx.letterSpacing = "1.2px";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    ctx.lineWidth = 1;
    for (const tier of TIERS) {
      const y = yAt(tierRung(tier.id));
      const on = t + 0.015 >= tierRung(tier.id);
      ctx.strokeStyle = on ? hexAlpha(TIER_COLOR[tier.id], 0.9) : "rgba(147,160,181,0.28)";
      ctx.beginPath();
      ctx.moveTo(12, y);
      ctx.lineTo(viewW - 78, y);
      ctx.stroke();
      ctx.fillStyle = on ? TIER_COLOR[tier.id] : "rgba(147,160,181,0.62)";
      ctx.fillText(tier.label, viewW - 8, y);
    }
    if (spacing && "letterSpacing" in spacing) ctx.letterSpacing = "0px";
  }

  function drawRocket(x, y, flame, tilt, color) {
    ctx.save();
    ctx.translate(Math.round(x), Math.round(y));
    ctx.rotate(tilt);
    const glow = ctx.createRadialGradient(0, 2, 2, 0, 6, 18);
    glow.addColorStop(0, hexAlpha(color, 0.38));
    glow.addColorStop(1, hexAlpha(color, 0));
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(0, 6, 18, 0, Math.PI * 2);
    ctx.fill();
    if (flame > 0.04) {
      const length = 7 + flame * 12;
      const flameFill = ctx.createLinearGradient(0, 7, 0, 7 + length);
      flameFill.addColorStop(0, "#fff6d8");
      flameFill.addColorStop(0.45, color);
      flameFill.addColorStop(1, hexAlpha(color, 0));
      ctx.fillStyle = flameFill;
      ctx.beginPath();
      ctx.moveTo(-3.5, 7);
      ctx.lineTo(0, 7 + length);
      ctx.lineTo(3.5, 7);
      ctx.closePath();
      ctx.fill();
    }
    ctx.fillStyle = "#f5c542";
    ctx.fillRect(-8, 1, 4, 6);
    ctx.fillRect(4, 1, 4, 6);
    ctx.fillStyle = "#e8eef8";
    ctx.beginPath();
    ctx.moveTo(-4, -11);
    ctx.lineTo(0, -17);
    ctx.lineTo(4, -11);
    ctx.fill();
    ctx.fillRect(-4, -11, 8, 18);
    ctx.fillStyle = "#7ee7ff";
    ctx.fillRect(-2, -7, 4, 4);
    ctx.restore();
  }

  function drawStillFinale(total) {
    const shown = Math.min(total, 6);
    for (let pop = 0; pop < shown; pop += 1) {
      const cx = viewW * (0.22 + (pop / Math.max(1, shown - 1 || 1)) * 0.42);
      const cy = 22 + (pop % 3) * 16;
      ctx.fillStyle = FINALE_COLORS[pop % FINALE_COLORS.length];
      for (let i = 0; i < 8; i += 1) {
        const angle = (Math.PI * 2 * i) / 8;
        ctx.fillRect(cx + Math.cos(angle) * 9 - 1, cy + Math.sin(angle) * 9 - 1, 2, 2);
      }
    }
  }

  function stepEffects(now, dt) {
    const step = dt / 16.67;
    let write = 0;
    for (let i = 0; i < particles.length; i += 1) {
      const particle = particles[i];
      particle.life -= particle.decay * step;
      if (particle.life <= 0) continue;
      particle.x += particle.vx * step;
      particle.y += particle.vy * step;
      particles[write] = particle;
      write += 1;
      ctx.globalAlpha = Math.max(0, particle.life);
      ctx.fillStyle = particle.color;
      if (particle.streak) {
        ctx.strokeStyle = particle.color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(particle.x, particle.y);
        ctx.lineTo(particle.x - particle.vx * 5, particle.y - particle.vy * 5);
        ctx.stroke();
      }
      ctx.fillRect(particle.x, particle.y, particle.size, particle.size);
    }
    particles.length = write;
    write = 0;
    for (let i = 0; i < rings.length; i += 1) {
      const ring = rings[i];
      if (ring.wait > 0) {
        ring.wait -= dt;
        rings[write] = ring;
        write += 1;
        continue;
      }
      ring.r += ring.speed * step;
      ring.life -= 0.018 * step;
      if (ring.life <= 0) continue;
      ctx.globalAlpha = Math.max(0, ring.life);
      ctx.strokeStyle = ring.color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(ring.x, ring.y, ring.r, 0, Math.PI * 2);
      ctx.stroke();
      rings[write] = ring;
      write += 1;
    }
    rings.length = write;
    ctx.globalAlpha = 1;
    if (state.flash > 0) {
      ctx.fillStyle = `rgba(126,231,255,${state.flash * 0.22})`;
      ctx.fillRect(0, 0, viewW, viewH);
      state.flash = Math.max(0, state.flash - dt / 220);
    }
  }

  function draw(now) {
    if (!resize()) return;
    if (!lastNow) lastNow = now;
    const dt = Math.min(50, now - lastNow);
    lastNow = now;
    if (reduced) state.displayT = state.toT;
    else {
      const gain = 1 - Math.exp(-dt / (state.easeMs || 280));
      state.displayT += (state.toT - state.displayT) * gain;
      if (Math.abs(state.toT - state.displayT) < 0.002) state.displayT = state.toT;
    }
    consumePending();
    const t = state.displayT;
    drawSky(t);
    drawStars(now, t);
    drawRails(t);
    if (reduced && state.staticMark) drawStaticMark(state.staticMark);
    let x = rocketX();
    let y = yAt(t);
    let tilt = 0;
    if (!reduced && state.answerTier === "stall" && state.mood === "hit") {
      const age = now - state.moodAt;
      const damp = Math.max(0, 1 - age / 680);
      x += Math.sin(age / 28) * 7 * damp;
      tilt += Math.sin(age / 28) * 0.2 * damp;
    }
    if (!reduced && state.mood === "miss") {
      const age = now - state.moodAt;
      const damp = Math.max(0, 1 - age / 380);
      tilt += Math.sin(age / 30) * 0.38 * damp;
    }
    if (!reduced && now < state.kickUntil) tilt += Math.sin(now / 22) * 0.24;
    if (!reduced && state.mood === "finale") {
      x += Math.sin(now / 700) * 4;
      y += Math.cos(now / 900) * 2.5;
    }
    const moving = Math.abs(state.toT - state.displayT) > 0.004 || state.mood === "finale";
    if (moving && now - lastTrail > 32) {
      lastTrail = now;
      trail.push({ x, y });
      if (trail.length > 14) trail.shift();
    }
    if (trail.length > 1) {
      ctx.lineWidth = 2;
      ctx.lineCap = "round";
      const trailColor = TIER_COLOR[state.answerTier] || TIER_COLOR[state.tier] || "#ff8a3d";
      for (let i = 1; i < trail.length; i += 1) {
        ctx.strokeStyle = hexAlpha(trailColor, (i / trail.length) * 0.45);
        ctx.beginPath();
        ctx.moveTo(trail[i - 1].x, trail[i - 1].y);
        ctx.lineTo(trail[i].x, trail[i].y);
        ctx.stroke();
      }
    }
    if (!reduced && state.mood === "finale" && state.finaleLeft > 0 && now >= state.finaleNext) {
      const count = 12 + Math.round(state.toT * 16);
      const color = FINALE_COLORS[state.finaleLeft % FINALE_COLORS.length];
      if (state.finaleLeft === state.finaleTotal) spawnPop(x, y, color, count);
      else spawnPop(viewW * (0.18 + Math.random() * 0.48), 18 + Math.random() * viewH * 0.4, color, count);
      state.finaleLeft -= 1;
      state.finaleNext = now + 200;
    }
    if (!reduced) stepEffects(now, dt);
    else if (state.mood === "finale") drawStillFinale(state.finaleTotal);
    let flame = 0.32;
    let flameColor = "#ff8a3d";
    if (state.mood === "miss") flame = 0;
    else if (state.mood === "judging") {
      flame = reduced ? 0.45 : 0.35 + 0.4 * (0.5 + 0.5 * Math.sin(now / 110));
      flameColor = "#f5c542";
    } else if (Math.abs(state.toT - state.displayT) > 0.01) {
      flame = 1;
      flameColor = TIER_COLOR[state.answerTier] || "#ff8a3d";
    } else if (state.mood === "finale") {
      flame = 0.75;
      flameColor = TIER_COLOR[state.tier] || "#7ee7ff";
    }
    if (!reduced && flame > 0 && state.mood !== "judging") {
      flame *= 0.75 + 0.25 * Math.sin(now / 55);
    }
    if (state.mood === "finale") {
      ctx.strokeStyle = hexAlpha(flameColor, 0.75);
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(x, y, 16 + state.toT * 8, 0, Math.PI * 2);
      ctx.stroke();
    }
    drawRocket(x, y, Math.max(0, flame), tilt, flameColor);
    if (!reduced && state.mood === "judging") {
      const sweep = (now % 1400) / 1400;
      const scanY = 12 + sweep * (viewH - 24);
      ctx.fillStyle = "rgba(245,197,66,0.06)";
      ctx.fillRect(0, scanY - 8, viewW, 18);
      ctx.fillStyle = "rgba(245,197,66,0.28)";
      ctx.fillRect(0, scanY, viewW, 2);
    }
  }

  function poke() {
    if (!alive) return;
    if (reduced) {
      draw(performance.now());
      return;
    }
    if (raf) return;
    raf = requestAnimationFrame(loop);
  }

  function loop(now) {
    raf = 0;
    if (!alive || document.hidden) return;
    try {
      draw(now);
    } catch {
      alive = false;
      return;
    }
    if (!reduced && alive) raf = requestAnimationFrame(loop);
  }

  function onVis() {
    if (document.hidden) {
      if (raf) cancelAnimationFrame(raf);
      raf = 0;
      return;
    }
    lastNow = 0;
    poke();
  }

  document.addEventListener("visibilitychange", onVis);
  if (typeof ResizeObserver === "function" && canvas.parentElement) {
    observer = new ResizeObserver(() => poke());
    observer.observe(canvas.parentElement);
  }

  function set(partial) {
    const previous = state.mood;
    if (partial.mood) state.mood = partial.mood;
    if (typeof partial.fromT === "number") state.displayT = partial.fromT;
    if (typeof partial.toT === "number") state.toT = partial.toT;
    if (typeof partial.fromT === "number" || typeof partial.toT === "number") {
      state.easeMs = 220 + Math.abs(state.toT - state.displayT) * 720;
    }
    if ("tier" in partial) state.tier = partial.tier || null;
    if ("answerTier" in partial) state.answerTier = partial.answerTier || null;
    if (typeof partial.altitude === "number") state.altitude = partial.altitude;
    if (partial.mood && partial.mood !== previous) arm(partial.mood);
    poke();
  }

  function kick(kind) {
    if (kind !== "reject") return;
    state.kickUntil = performance.now() + 280;
    const at = pose(state.displayT);
    if (viewW > 2 && !reduced) spawnReject(at.x, at.y);
    else state.pending = "reject";
    poke();
  }

  function destroy() {
    alive = false;
    if (raf) cancelAnimationFrame(raf);
    raf = 0;
    if (observer) observer.disconnect();
    document.removeEventListener("visibilitychange", onVis);
    if (media && media.removeEventListener) media.removeEventListener("change", onMotion);
  }

  set(initial || {});
  return { set, kick, destroy };
}
