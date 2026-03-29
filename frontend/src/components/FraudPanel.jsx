import React from 'react'
import { ShieldAlert, AlertTriangle, Zap, Copy, RefreshCw } from 'lucide-react'

const REASON_META = {
  cycle: { label: 'Cycle Detected', icon: RefreshCw, color: 'text-red-400 bg-red-900/30' },
  self_referral: { label: 'Self-Referral', icon: AlertTriangle, color: 'text-orange-400 bg-orange-900/30' },
  velocity_limit: { label: 'Velocity Limit', icon: Zap, color: 'text-yellow-400 bg-yellow-900/30' },
  duplicate: { label: 'Duplicate', icon: Copy, color: 'text-purple-400 bg-purple-900/30' },
}

function FraudRow({ flag }) {
  const meta = REASON_META[flag.reason] || { label: flag.reason, icon: ShieldAlert, color: 'text-slate-400 bg-slate-900/30' }
  const Icon = meta.icon
  const ts = new Date(flag.created_at).toLocaleString()

  return (
    <div className="flex items-start gap-3 p-3 hover:bg-slate-750 rounded-lg transition-colors">
      <div className={`p-1.5 rounded-md mt-0.5 ${meta.color}`}>
        <Icon size={14} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${meta.color}`}>
            {meta.label}
          </span>
          <span className="text-slate-500 text-xs">{ts}</span>
        </div>
        <p className="text-slate-300 text-xs mt-0.5 truncate">{flag.details || 'No details'}</p>
        <p className="text-slate-500 text-xs">User: {flag.user_id.slice(0, 8)}…</p>
      </div>
    </div>
  )
}

export default function FraudPanel({ flags }) {
  if (!flags) {
    return (
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
        <div className="animate-pulse space-y-2">
          {Array(4).fill(0).map((_, i) => (
            <div key={i} className="h-14 bg-slate-700 rounded-lg" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700">
      <div className="p-4 border-b border-slate-700 flex items-center gap-2">
        <ShieldAlert size={16} className="text-red-400" />
        <h2 className="text-white font-semibold text-sm">Fraud Monitor</h2>
        <span className="ml-auto bg-red-900/40 text-red-300 text-xs px-2 py-0.5 rounded-full">
          {flags.length} flags
        </span>
      </div>

      <div className="max-h-80 overflow-y-auto divide-y divide-slate-700/50">
        {flags.length === 0 ? (
          <div className="p-6 text-center text-slate-500 text-sm">No fraud flags yet</div>
        ) : (
          flags.map(f => <FraudRow key={f.id} flag={f} />)
        )}
      </div>
    </div>
  )
}
