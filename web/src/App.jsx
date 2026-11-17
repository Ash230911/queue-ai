import { useEffect, useState } from 'react'
import { get, FALLBACK_PARAMS } from './api'
import Setup from './pages/Setup.jsx'
import Live from './pages/Live.jsx'
import Compare from './pages/Compare.jsx'
import Forecast from './pages/Forecast.jsx'
import Optimise from './pages/Optimise.jsx'

const TABS = [['setup', 'Scenario'], ['live', 'Live simulation'], ['compare', 'Compare strategies'], ['forecast', 'Congestion forecast'], ['optimise', 'Optimise and validate']]

export default function App() {
  const [tab, setTab] = useState('setup')
  const [params, setParams] = useState(FALLBACK_PARAMS)
  const [result, setResult] = useState(null)

  useEffect(() => { get('/api/defaults').then(setParams).catch(() => {}) }, [])

  const shared = { params, setParams, result, setResult, go: setTab }
  return (
    <>
      <header className="top">
        <div><h1>Queue Lab</h1><p>Predict waits, spot congestion early and compare how counters are allocated.</p></div>
        <span className="tag">Simulated data</span>
      </header>
      <nav role="tablist">
        {TABS.map(([k, l]) => <button key={k} role="tab" aria-selected={tab === k} className={tab === k ? 'on' : ''} onClick={() => setTab(k)}>{l}</button>)}
      </nav>
      <main>
        {tab === 'setup' && <Setup {...shared} />}
        {tab === 'live' && <Live {...shared} />}
        {tab === 'compare' && <Compare {...shared} />}
        {tab === 'forecast' && <Forecast {...shared} />}
        {tab === 'optimise' && <Optimise {...shared} />}
      </main>
    </>
  )
}
