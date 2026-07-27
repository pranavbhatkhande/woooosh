// Hand-rolled SVG charts: time-series lines with crosshair tooltip, weekly bars.
const NS = 'http://www.w3.org/2000/svg';

function el(tag, attrs = {}) {
  const n = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  return n;
}

function niceTicks(min, max, count = 4) {
  if (min === max) { min -= 1; max += 1; }
  const span = max - min;
  const step0 = span / count;
  const mag = Math.pow(10, Math.floor(Math.log10(step0)));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => span / s <= count) || 10 * mag;
  const lo = Math.floor(min / step) * step;
  const ticks = [];
  for (let v = lo; v <= max + step * 0.5; v += step) if (v >= min - step * 0.5) ticks.push(v);
  return ticks;
}

const fmtDate = (t) => new Date(t).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });

export function lineChart(container, { series, yFmt = (v) => v, height = 240 }) {
  container.textContent = '';
  container.classList.add('chart');
  const all = series.flatMap((s) => s.points);
  if (all.length < 2) {
    container.innerHTML = '<div class="chart-empty">Log a few sessions and your progress will draw itself here.</div>';
    return;
  }
  const W = Math.max(container.clientWidth || 320, 280);
  const H = height;
  const pad = { t: 14, r: 12, b: 26, l: 40 };
  const xs = all.map((p) => p.t), ys = all.map((p) => p.y);
  const x0 = Math.min(...xs), x1 = Math.max(...xs);
  let yMin = Math.min(...ys), yMax = Math.max(...ys);
  const yPad = (yMax - yMin || yMax * 0.1 || 10) * 0.12;
  yMin -= yPad; yMax += yPad;
  const X = (t) => pad.l + ((t - x0) / (x1 - x0 || 1)) * (W - pad.l - pad.r);
  const Y = (v) => pad.t + (1 - (v - yMin) / (yMax - yMin)) * (H - pad.t - pad.b);

  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: 'img' });

  for (const v of niceTicks(yMin + yPad * 0.5, yMax - yPad * 0.5)) {
    if (Y(v) < pad.t - 2) continue;
    svg.append(el('line', { x1: pad.l, x2: W - pad.r, y1: Y(v), y2: Y(v), class: 'grid' }));
    const t = el('text', { x: pad.l - 6, y: Y(v) + 3, class: 'tick', 'text-anchor': 'end' });
    t.textContent = yFmt(v);
    svg.append(t);
  }
  const nx = Math.min(4, all.length);
  for (let i = 0; i < nx; i++) {
    const t = x0 + ((x1 - x0) * i) / Math.max(nx - 1, 1);
    const lbl = el('text', { x: X(t), y: H - 8, class: 'tick', 'text-anchor': i === 0 ? 'start' : i === nx - 1 ? 'end' : 'middle' });
    lbl.textContent = fmtDate(t);
    svg.append(lbl);
  }
  svg.append(el('line', { x1: pad.l, x2: W - pad.r, y1: Y(yMin) , y2: Y(yMin), class: 'baseline' }));

  const cross = el('line', { class: 'crosshair', y1: pad.t, y2: H - pad.b, visibility: 'hidden' });
  svg.append(cross);

  const hoverDots = [];
  const maxPts = Math.max(...series.map((s) => s.points.length));
  const showDots = maxPts <= 16 && (W - pad.l - pad.r) / maxPts > 24;
  for (const s of series) {
    const pts = [...s.points].sort((a, b) => a.t - b.t);
    const d = pts.map((p, i) => `${i ? 'L' : 'M'}${X(p.t).toFixed(1)} ${Y(p.y).toFixed(1)}`).join(' ');
    svg.append(el('path', { d, class: 'series-line', stroke: s.color }));
    if (showDots) {
      for (const p of pts) svg.append(el('circle', { cx: X(p.t), cy: Y(p.y), r: 2.5, class: 'series-dot', fill: s.color }));
    }
    const hd = el('circle', { r: 5, class: 'hover-dot', stroke: s.color, visibility: 'hidden' });
    svg.append(hd);
    hoverDots.push({ s, pts, hd });
  }

  const tip = document.createElement('div');
  tip.className = 'chart-tip';
  tip.hidden = true;
  container.append(svg, tip);

  const move = (clientX) => {
    const rect = svg.getBoundingClientRect();
    const t = x0 + ((clientX - rect.left - pad.l) / (W - pad.l - pad.r)) * (x1 - x0);
    let rows = [], tx = null;
    for (const { s, pts, hd } of hoverDots) {
      let best = pts[0];
      for (const p of pts) if (Math.abs(p.t - t) < Math.abs(best.t - t)) best = p;
      hd.setAttribute('cx', X(best.t));
      hd.setAttribute('cy', Y(best.y));
      hd.setAttribute('visibility', 'visible');
      tx = tx ?? best.t;
      rows.push(`<span class="tip-row"><i style="background:${s.color}"></i>${s.name ? s.name + ' ' : ''}<b>${yFmt(best.y)}</b></span>`);
    }
    cross.setAttribute('x1', X(tx)); cross.setAttribute('x2', X(tx));
    cross.setAttribute('visibility', 'visible');
    tip.innerHTML = `<span class="tip-date">${fmtDate(tx)}</span>${rows.join('')}`;
    tip.hidden = false;
    const left = Math.min(Math.max(X(tx) - 40, 0), W - 130);
    tip.style.left = `${left}px`;
  };
  const leave = () => {
    tip.hidden = true;
    cross.setAttribute('visibility', 'hidden');
    hoverDots.forEach(({ hd }) => hd.setAttribute('visibility', 'hidden'));
  };
  svg.addEventListener('pointermove', (e) => move(e.clientX));
  svg.addEventListener('pointerdown', (e) => move(e.clientX));
  svg.addEventListener('pointerleave', leave);
}

export function barChart(container, { bars, yFmt = (v) => v, height = 200 }) {
  container.textContent = '';
  container.classList.add('chart');
  if (bars.length < 1) {
    container.innerHTML = '<div class="chart-empty">No sessions yet.</div>';
    return;
  }
  const W = Math.max(container.clientWidth || 320, 280);
  const H = height;
  const pad = { t: 14, r: 12, b: 26, l: 44 };
  const yMax = Math.max(...bars.map((b) => b.y)) * 1.1 || 10;
  const Y = (v) => pad.t + (1 - v / yMax) * (H - pad.t - pad.b);
  const bw = Math.min(28, ((W - pad.l - pad.r) / bars.length) - 2);
  const X = (i) => pad.l + ((i + 0.5) / bars.length) * (W - pad.l - pad.r) - bw / 2;

  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: 'img' });
  for (const v of niceTicks(0, yMax)) {
    svg.append(el('line', { x1: pad.l, x2: W - pad.r, y1: Y(v), y2: Y(v), class: 'grid' }));
    const t = el('text', { x: pad.l - 6, y: Y(v) + 3, class: 'tick', 'text-anchor': 'end' });
    t.textContent = yFmt(v);
    svg.append(t);
  }
  const tip = document.createElement('div');
  tip.className = 'chart-tip';
  tip.hidden = true;

  bars.forEach((b, i) => {
    const y = Y(b.y);
    const r = el('rect', {
      x: X(i), y, width: Math.max(bw, 3), height: Math.max(H - pad.b - y, 2),
      rx: 4, class: 'bar',
    });
    r.addEventListener('pointerenter', () => {
      tip.innerHTML = `<span class="tip-date">${b.label}</span><span class="tip-row"><b>${yFmt(b.y)}</b></span>`;
      tip.hidden = false;
      tip.style.left = `${Math.min(Math.max(X(i) - 30, 0), W - 130)}px`;
    });
    r.addEventListener('pointerleave', () => { tip.hidden = true; });
    svg.append(r);
    if (bars.length <= 8 || i % Math.ceil(bars.length / 6) === 0) {
      const t = el('text', { x: X(i) + bw / 2, y: H - 8, class: 'tick', 'text-anchor': 'middle' });
      t.textContent = b.label;
      svg.append(t);
    }
  });
  svg.append(el('line', { x1: pad.l, x2: W - pad.r, y1: H - pad.b, y2: H - pad.b, class: 'baseline' }));
  container.append(svg, tip);
}
