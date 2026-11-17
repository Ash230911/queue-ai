import { useEffect, useState } from 'react'
import { get, post } from '../api'

const FIELDS = [
  ['n', 'Customers', 20, 2000, 10], ['rate', 'Arrivals per hour', 1, 300, 1], ['svc', 'Mean service time (min)', 0.5, 60, 0.5],
  ['cv', 'Service variability', 0.05, 3, 0.05], ['c', 'Regular counters', 1, 20, 1], ['flex', 'Flex counters', 0, 10, 1],
  ['prio', 'Priority customers (%)', 0, 100, 1], ['mult', 'Surge multiplier', 1, 5, 0.25], ['s0', 'Surge starts (min)', 0, 1000, 5],
  ['sl', 'Surge length (min)', 0, 500, 5], ['seed', 'Random seed', 0, 1000000, 1],
]

export default function Setup({ params, setParams, setResult, go }) {
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [saved, setSaved] = useState([])
  useEffect(() => { get('/api/scenarios').then(setSaved).catch(() => {}) }, [])

  const set = (k, v) => setParams({ ...params, [k]: v === '' ? '' : Number(v) })
  const run = async () => {
    setBusy(true); setErr('')
    try { setResult(await post('/api/simulate', { params, save: true, scenario_name: `Run ${new Date().toLocaleTimeString()}` })); go('compare') }
    catch (e) { setErr(e.message) } finally { setBusy(false) }
  }

  return (
    <div className="grid2">
      <section>
        <h2>Describe the service desk</h2>
        <p className="sub">Customers arrive at random, with a busy period you control. Every strategy is tested on the same customers.</p>
        <div className="fields">
          {FIELDS.map(([k, l, min, max, step]) => (
            <label key={k}>{l}<input type="number" value={params[k]} min={min} max={max} step={step} onChange={e => set(k, e.target.value)} /></label>
          ))}
        </div>
        {err && <p className="err" role="alert">{err}</p>}
        <button className="primary" onClick={run} disabled={busy}>{busy ? 'Simulating…' : 'Run simulation'}</button>
      </section>
      <section>
        <h2>Saved scenarios</h2>
        <p className="sub">Load a scenario to reuse its settings. Demo scenarios are included.</p>
        <ul className="list">
          {saved.slice(0, 12).map(s => <li key={s.id}><span>{s.name}</span><button onClick={() => setParams(s.params)}>Load</button></li>)}
          {!saved.length && <li className="sub">No saved scenarios yet. Run a simulation to save one.</li>}
        </ul>
      </section>
    </div>
  )
}
