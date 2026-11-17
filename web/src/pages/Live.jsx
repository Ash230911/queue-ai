import { useEffect, useRef, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from 'recharts'
import { get, liveSocket, COLORS, f } from '../api'

const dots = n => Array.from({ length: Math.min(n, 24) }, (_, i) => <i key={i} />)

export default function Live({ params }) {
  const [strategies, setStrategies] = useState([{ key: 'baseline', name: 'Baseline' }])
  const [strategy, setStrategy] = useState('baseline')
  const [speed, setSpeed] = useState(30)
  const [frame, setFrame] = useState(null)
  const [hist, setHist] = useState([])
  const [summary, setSummary] = useState(null)
  const [err, setErr] = useState('')
  const ws = useRef(null)

  useEffect(() => { get('/api/strategies').then(setStrategies).catch(() => {}); return () => ws.current?.close() }, [])

  const start = () => {
    ws.current?.close(); setHist([]); setSummary(null); setErr(''); setFrame(null)
    const s = liveSocket(); ws.current = s
    s.onopen = () => s.send(JSON.stringify({ params, strategy, speed }))
    s.onmessage = e => {
      const m = JSON.parse(e.data)
      if (m.type === 'frame') { setFrame(m); setHist(h => [...h, { t: m.minute, queue: m.queue }]) }
      else if (m.type === 'done') setSummary(m.summary)
      else if (m.type === 'error') setErr(m.detail)
    }
    s.onerror = () => setErr('Could not reach the live feed. Is the API running?')
  }
  const dedicated = strategies.find(s => s.key === strategy)?.dedicated

  return (
    <section>
      <h2>Live simulation</h2>
      <p className="sub">Watch customers arrive, queue and get served. One real second is {speed} simulated minutes.</p>
      <div className="row">
        <label>Strategy<select value={strategy} onChange={e => setStrategy(e.target.value)}>{strategies.map(s => <option key={s.key} value={s.key}>{s.name}</option>)}</select></label>
        <label>Speed ({speed}×)<input type="range" min="5" max="200" value={speed} onChange={e => setSpeed(+e.target.value)} /></label>
        <button className="primary" onClick={start}>Start</button>
      </div>
      {err && <p className="err" role="alert">{err}</p>}
      {frame && (
        <>
          <p className="clock">Minute {frame.minute}. Waiting: <b>{frame.queue}</b>. Served: <b>{frame.served}</b>.</p>
          {!dedicated && <div className="pool" aria-label="Shared queue">{dots(frame.pool)}{frame.pool > 24 && <span>+{frame.pool - 24}</span>}</div>}
          <div className="counters">
            {frame.counters.map((c, i) => (
              <div key={i} className={`counter ${!c.open ? 'closed' : c.busy ? 'busy' : 'idle'}`}>
                <b>Counter {i + 1}</b><span>{!c.open ? 'Closed' : c.busy ? 'Serving' : 'Free'}</span>
                {dedicated && <div className="q">{dots(c.q)}</div>}
              </div>
            ))}
          </div>
          <div style={{ height: 180 }}>
            <ResponsiveContainer><LineChart data={hist}><CartesianGrid strokeDasharray="3 3" stroke="var(--line)" /><XAxis dataKey="t" stroke="var(--mute)" /><YAxis allowDecimals={false} stroke="var(--mute)" /><Tooltip /><Line dataKey="queue" stroke={COLORS[strategy]} dot={false} strokeWidth={2} isAnimationActive={false} name="Queue length" /></LineChart></ResponsiveContainer>
          </div>
        </>
      )}
      {summary && <p className="verdict">Finished: average wait {f(summary.avg_wait)} min, slowest 10% wait {f(summary.p90_wait)} min, peak queue {summary.peak_queue}.</p>}
    </section>
  )
}
