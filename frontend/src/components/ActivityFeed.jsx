import React from 'react'
import { GitBranch, RefreshCw, Coins, ShieldAlert, Activity } from 'lucide-react'

const EVENT_META = {
  referral_created: { icon: GitBranch, color: 'text-emerald-400', dot: 'bg-emerald-500' },
  cycle_prevented: { icon: RefreshCw, color: 'text-red-400', dot: 'bg-red-500' },
  reward_distributed: { icon: Coins, color: 'text-amber-400', dot: 'bg-amber-500' },
  fraud_detected: { icon: ShieldAlert, color: 'text-orange-400', dot: 'bg-orange-500' },
}

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const secs = Math.floor(diff / 1000)
  if (secs < 60) return `${secs}s ago`
  const mins = Math.floor(secs / 60)
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

function EventRow({ event }) {
  const meta = EVENT_META[event.event_type] || { icon: Activity, color: 'text-slate-400', dot: 'bg-slate-500' }
  const Icon = meta.icon

  return (
    <div className="flex items-start gap-3 py-2.5 px-4 hover:bg-slate-750 transition-colors">
      <div className={`mt-0.5 ${meta.color}`}>
        <Icon size={14} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-slate-200 text-xs leading-relaxed">{event.description}</p>
      </div>
      <span className="text-slate-500 text-xs shrink-0 mt-0.5">{timeAgo(event.created_at)}</span>
    </div>
  )
}

export default function ActivityFeed({ events, liveEvents = [] }) {
  const all = [...liveEvents, ...(events || [])].slice(0, 50)

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700">
      <div className="p-4 border-b border-slate-700 flex items-center gap-2">
        <Activity size={16} className="text-indigo-400" />
        <h2 className="text-white font-semibold text-sm">Activity Feed</h2>
        <span className="ml-2 flex items-center gap-1 text-xs text-emerald-400">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse inline-block" />
          Live
        </span>
      </div>

      <div className="max-h-80 overflow-y-auto divide-y divide-slate-700/40">
        {all.length === 0 ? (
          <div className="p-6 text-center text-slate-500 text-sm">No activity yet</div>
        ) : (
          all.map(e => <EventRow key={e.id} event={e} />)
        )}
      </div>
    </div>
  )
}
