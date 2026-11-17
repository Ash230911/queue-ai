import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid, ResponsiveContainer } from 'recharts'
import { COLORS, f } from '../api'

function merge(series) {
  const keys = Object.keys(series)
  const H = Math.ceil(Math.max(...keys.map(k => series[k][series[k].length - 1][0])))
  const idx = Object.fromEntries(keys.map(k => [k, 0]))
  const rows = []
  for (let m = 0; m <= H; m++) {
    const row = { t: m }
    keys.forEach(k => { const s = series[k]; while (idx[k] + 1 < s.length && s[idx[k] + 1][0] <= m) idx[k]++; row[k] = s[idx[k]][1] })
    rows.push(row)
  }
  return rows
}

export default function Compare({ result, go }) {
  if (!result) return <section><h2>No results yet</h2><p className="sub">Run a simulation first.</p><button className="primary" onClick={() => go('setup')}>Go to scenario</button></section>
  const { summary, series, theory, recommendation, warnings } = result
  const base = summary[0]
  return (
    <div className="stack">
      <section className="verdict">
        <h2>{recommendation}</h2>
        {warnings.map(w => <p key={w} className="err">{w}</p>)}
        {theory.stable
          ? <p className="sub">Theory (M/M/c, shared queue, ignores the surge): utilisation {f(theory.rho * 100, 0)}%, chance of waiting {f(theory.p_wait * 100, 0)}%, mean wait {f(theory.wq)} min.</p>
          : <p className="sub">Theory: average demand needs {f(theory.offered_load)} counters of work, so a steady state does not exist.</p>}
      </section>
      <section>
        <h2>Strategy comparison</h2>
        <p className="sub">Same customers for every strategy. Times in minutes.</p>
        <div className="scroll"><table>
          <thead><tr><th>Strategy</th><th>Avg wait</th><th>P90 wait</th><th>Max wait</th><th>Avg queue</th><th>Peak queue</th><th>Utilisation</th><th>Staff-min</th><th>Priority wait</th><th>Estimate error</th><th>Vs baseline</th></tr></thead>
          <tbody>{summary.map(r => (
            <tr key={r.key}><td><span className="sw" style={{ background: COLORS[r.key] }} />{r.name}</td>
              <td>{f(r.avg_wait)}</td><td>{f(r.p90_wait)}</td><td>{f(r.max_wait)}</td><td>{f(r.avg_queue)}</td><td>{r.peak_queue}</td>
              <td>{f(r.utilisation * 100, 0)}%</td><td>{f(r.staff_minutes, 0)}</td><td>{f(r.priority_wait)}</td><td>{f(r.est_error)}</td>
              <td className={r.improvement_pct > 0 ? 'good' : r.improvement_pct < 0 ? 'bad' : ''}>{r.key === 'baseline' ? 'baseline' : `${r.improvement_pct > 0 ? '-' : '+'}${f(Math.abs(r.improvement_pct), 0)}% wait`}</td></tr>))}</tbody>
        </table></div>
      </section>
      <section>
        <h2>Queue length over time</h2>
        <div style={{ height: 280 }}><ResponsiveContainer><LineChart data={merge(series)}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" /><XAxis dataKey="t" unit="m" stroke="var(--mute)" /><YAxis allowDecimals={false} stroke="var(--mute)" /><Tooltip /><Legend />
          {summary.map(r => <Line key={r.key} dataKey={r.key} name={r.name} stroke={COLORS[r.key]} dot={false} strokeWidth={r.key === 'baseline' ? 1.6 : 2.4} type="stepAfter" />)}
        </LineChart></ResponsiveContainer></div>
      </section>
      <section>
        <h2>Counter utilisation</h2>
        <p className="sub">Busy time divided by open time, per counter.</p>
        {summary.map(r => (
          <div className="ub" key={r.key}><span>{r.name}</span>
            <div className="bars">{r.counter_utilisation.map((u, i) => <i key={i} title={`${f(u * 100, 0)}%`} style={{ height: `${Math.max(2, u * 100)}%`, background: COLORS[r.key] }} />)}</div></div>))}
      </section>
      <p className="note">All data is simulated. Estimate error is the mean gap between the wait quoted on arrival and the wait actually experienced.</p>
    </div>
  )
}
