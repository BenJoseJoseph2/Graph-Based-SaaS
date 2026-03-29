import React from 'react'
import { Users, GitBranch, ShieldAlert, Coins, CheckCircle, XCircle } from 'lucide-react'

const Card = ({ icon: Icon, label, value, color, sub }) => (
  <div className="bg-slate-800 rounded-xl p-5 flex items-start gap-4 shadow-lg border border-slate-700">
    <div className={`p-3 rounded-lg ${color}`}>
      <Icon size={20} className="text-white" />
    </div>
    <div>
      <p className="text-slate-400 text-xs uppercase tracking-wider">{label}</p>
      <p className="text-2xl font-bold text-white mt-0.5">{value}</p>
      {sub && <p className="text-slate-500 text-xs mt-0.5">{sub}</p>}
    </div>
  </div>
)

export default function MetricsPanel({ metrics }) {
  if (!metrics) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        {Array(6).fill(0).map((_, i) => (
          <div key={i} className="bg-slate-800 rounded-xl p-5 h-24 animate-pulse border border-slate-700" />
        ))}
      </div>
    )
  }

  const acceptRate = metrics.total_referrals > 0
    ? ((metrics.valid_referrals / metrics.total_referrals) * 100).toFixed(1)
    : '0.0'

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
      <Card icon={Users}        label="Total Users"         value={metrics.total_users}                      color="bg-blue-600" />
      <Card icon={GitBranch}    label="Total Referrals"     value={metrics.total_referrals}                  color="bg-violet-600" />
      <Card icon={CheckCircle}  label="Valid Referrals"     value={metrics.valid_referrals}   sub={`${acceptRate}% accept rate`} color="bg-emerald-600" />
      <Card icon={XCircle}      label="Rejected"            value={metrics.rejected_referrals}               color="bg-orange-600" />
      <Card icon={ShieldAlert}  label="Fraud Attempts"      value={metrics.fraud_attempts}                   color="bg-red-600" />
      <Card icon={Coins}        label="Rewards Distributed" value={`₹${metrics.total_rewards_distributed}`} color="bg-amber-600" />
    </div>
  )
}
