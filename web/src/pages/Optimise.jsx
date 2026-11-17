import { useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine, CartesianGrid, ResponsiveContainer } from 'recharts'
import { post, COLORS, f } from '../api'

export default function Optimise({ params }) {
  const [target, setTarget] = useState(5)
  const [opt, setOpt] = useState(null)
  const [val, setVal] = useState(null)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState('')
  const call = async (name, fn) => { setErr(''); setBusy(name); try { await fn() } catch (e) { setErr(e.message) } finally { setBusy('') } }

  return (
    <div className="stack">
      <section>
        <h2>Staffing optimiser</h2>
        <p className="sub">Finds the fewest counters that keep the average wait under your target, using a shared queue. Each level is averaged over 10 random scenarios.</p>
        <div className="row">
          <label>Target average wait (min)<input type="number" min="1" max="60" value={target} onChange={e => setTarget(+e.target.value)} /></label>
          <button className="primary" disabled={busy} onClick={() => call('o', async () => setOpt(await post('/api/optimise', { params, target_wait: target })))}>{busy === 'o' ? 'Searching…' : 'Find staffing level'}</button>
        </div>
        {opt && <>
          <p className="verdict">{opt.recommended_counters ? `Open ${opt.recommended_counters} counters: expected average wait ${f(opt.achieved_wait)} min.` : 'No staffing level up to the maximum meets this target.'}</p>
          <div style={{ height: 240 }}><ResponsiveContainer><LineChart data={opt.options}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" /><XAxis dataKey="counters" stroke="var(--mute)" label={{ value: 'Counters', position: 'insideBottom', offset: -2, fill: 'var(--mute)' }} /><YAxis stroke="var(--mute)" /><Tooltip />
            <ReferenceLine y={opt.target_wait} stroke="var(--good)" strokeDasharray="5 5" /><Line dataKey="avg_wait" name="Avg wait" stroke={COLORS.shared} strokeWidth={2.4} /><Line dataKey="p90_wait" name="P90 wait" stroke={COLORS.baseline} strokeWidth={1.6} />
          </LineChart></ResponsiveContainer></div></>}
      </section>
      <section>
        <h2>Validation across 30 random scenarios</h2>
        <p className="sub">One example proves little. This repeats your settings with 30 different seeds and reports means with 95% confidence intervals.</p>
        <button className="primary" disabled={busy} onClick={() => call('v', async () => setVal(await post('/api/validate', { params, runs: 30 })))}>{busy === 'v' ? 'Running…' : 'Run 30 scenarios'}</button>
        {val && <div className="scroll"><table><thead><tr><th>Strategy</th><th>Mean avg wait</th><th>95% CI</th><th>Mean improvement</th><th>Scenarios beating baseline</th></tr></thead>
          <tbody>{val.strategies.map(r => <tr key={r.key}><td><span className="sw" style={{ background: COLORS[r.key] }} />{r.name}</td><td>{f(r.mean_wait)}</td><td>±{f(r.ci95)}</td>
            <td className={r.mean_improvement_pct > 0 ? 'good' : ''}>{r.key === 'baseline' ? 'baseline' : `${f(r.mean_improvement_pct, 0)}%`}</td><td>{r.win_rate == null ? 'n/a' : `${Math.round(r.win_rate * val.runs)} of ${val.runs}`}</td></tr>)}</tbody></table></div>}
      </section>
      {err && <p className="err" role="alert">{err}</p>}
    </div>
  )
}
