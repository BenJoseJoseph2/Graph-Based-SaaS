import React, { useState, useCallback } from 'react'
import MetricsPanel from './components/MetricsPanel'
import GraphView from './components/GraphView'
import FraudPanel from './components/FraudPanel'
import ActivityFeed from './components/ActivityFeed'
import SimulationTool from './components/SimulationTool'
import ReferralForm from './components/ReferralForm'
import { fetchMetrics, fetchActivity, fetchFraudFlags } from './api/client'
import { usePolling } from './hooks/usePolling'
import { useWebSocket } from './hooks/useWebSocket'
import { GitBranch } from 'lucide-react'

export default function App() {
  const [metrics, setMetrics] = useState(null)
  const [activity, setActivity] = useState(null)
  const [fraudFlags, setFraudFlags] = useState(null)
  const [liveEvents, setLiveEvents] = useState([])
  const [wsStatus, setWsStatus] = useState('connecting')

  const refresh = useCallback(async () => {
    const [m, a, f] = await Promise.all([
      fetchMetrics().catch(() => null),
      fetchActivity(40).catch(() => null),
      fetchFraudFlags().catch(() => null),
    ])
    if (m) setMetrics(m)
    if (a) setActivity(a)
    if (f) setFraudFlags(f)
  }, [])

  usePolling(refresh, 6000)

  useWebSocket((payload) => {
    if (payload.event === '__connected__') { setWsStatus('connected'); return }
    const event = {
      id: `live-${Date.now()}`,
      event_type: payload.event,
      description: JSON.stringify(payload.data),
      created_at: new Date().toISOString(),
    }
    setLiveEvents(prev => [event, ...prev].slice(0, 20))
    // Refresh metrics on any live event
    refresh()
  })

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      {/* Header */}
      <header className="border-b border-slate-800 px-6 py-4 flex items-center gap-3">
        <div className="p-2 bg-indigo-600 rounded-lg">
          <GitBranch size={18} className="text-white" />
        </div>
        <div>
          <h1 className="text-white font-bold text-lg leading-none">Referral Engine</h1>
          <p className="text-slate-500 text-xs">DAG-based cycle-safe referral monitoring</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${wsStatus === 'connected' ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'}`} />
          <span className="text-slate-500 text-xs">{wsStatus === 'connected' ? 'Live' : 'Connecting…'}</span>
        </div>
      </header>

      <main className="px-6 py-6 space-y-6 max-w-screen-2xl mx-auto">
        {/* Metrics */}
        <section>
          <MetricsPanel metrics={metrics} />
        </section>

        {/* Graph view — full width */}
        <section>
          <GraphView />
        </section>

        {/* Bottom row: Fraud + Activity + Forms + Simulation */}
        <section className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-6">
          <FraudPanel flags={fraudFlags} />
          <ActivityFeed events={activity} liveEvents={liveEvents} />
          <ReferralForm onSuccess={refresh} />
          <SimulationTool />
        </section>
      </main>
    </div>
  )
}
