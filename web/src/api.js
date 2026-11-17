// API client (member 5). Every page talks to the backend only through these helpers.
export const COLORS = { baseline: '#7b8698', jsq: '#b7791f', shared: '#0b6e8a', priority_flex: '#c2410c' }
export const FALLBACK_PARAMS = { n: 150, rate: 40, svc: 6, cv: 0.8, c: 5, flex: 1, prio: 15, mult: 2, s0: 40, sl: 30, seed: 7, dist: 'lognormal' }

function message(j) {
  if (Array.isArray(j?.detail)) return j.detail.map(d => `${(d.loc || []).slice(-1)[0]}: ${d.msg}`).join('; ')
  return j?.detail || 'Request failed'
}

export async function post(path, body) {
  let r
  try {
    r = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  } catch {
    throw new Error('Cannot reach the API. Is the backend running on port 8000?')
  }
  const j = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(message(j))
  return j
}

export async function get(path) {
  const r = await fetch(path)
  if (!r.ok) throw new Error(message(await r.json().catch(() => ({}))))
  return r.json()
}

export function liveSocket() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  return new WebSocket(`${proto}://${location.host}/ws/live`)
}

export const f = (v, d = 1) => (v == null || Number.isNaN(v) ? 'n/a' : Number(v).toFixed(d))
