import { useState } from 'react'
import { BarChart, Bar, Cell, XAxis, YAxis, Tooltip, ReferenceLine, CartesianGrid, ResponsiveContainer } from 'recharts'
import { post, f } from '../api'

export default function Forecast({ params }) {
  const [data, setData] = useState(null)
  const [threshold, setThreshold] = useState(0.85)
  const [err, setErr] = useState('')
  const run = async () => { setErr(''); try { setData(await post('/api/forecast', { params, threshold })) } catch (e) { setErr(e.message) } }
  return (
    <section>
      <h2>Congestion forecast</h2>
      <p className="sub">Each bar compares the arrival rate over the previous 15 minutes with counter capacity. Red bars are warnings. A warning is correct when the baseline queue then grows to at least the number of counters within 15 minutes.</p>
      <div className="row">
        <label>Warning threshold ({Math.round(threshold * 100)}% load)<input type="range" min="0.5" max="1.2" step="0.05" value={threshold} onChange={e => setThreshold(+e.target.value)} /></label>
        <button className="primary" onClick={run}>Run forecast</button>
      </div>
      {err && <p className="err" role="alert">{err}</p>}
      {data && <>
        <div style={{ height: 260 }}><ResponsiveContainer><BarChart data={data.windows}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" /><XAxis dataKey="t" unit="m" stroke="var(--mute)" /><YAxis stroke="var(--mute)" tickFormatter={v => `${Math.round(v * 100)}%`} />
          <Tooltip formatter={v => `${Math.round(v * 100)}%`} labelFormatter={l => `Minute ${l}`} /><ReferenceLine y={data.threshold} stroke="var(--mute)" strokeDasharray="4 4" />
          <Bar dataKey="load" name="Load">{data.windows.map((w, i) => <Cell key={i} fill={w.warning ? 'var(--bad)' : 'var(--pool)'} stroke={w.actual ? 'var(--ink)' : 'none'} strokeWidth={2} />)}</Bar>
        </BarChart></ResponsiveContainer></div>
        <p className="verdict">{data.first_warning != null ? `First warning at minute ${data.first_warning}. ` : 'No warnings with this threshold. '}
          Warnings: {data.warning_count}. Precision {data.precision == null ? 'n/a' : `${f(data.precision * 100, 0)}%`}, recall {data.recall == null ? 'n/a' : `${f(data.recall * 100, 0)}%`}. Outlined bars mark windows where congestion really followed.</p>
      </>}
    </section>
  )
}
