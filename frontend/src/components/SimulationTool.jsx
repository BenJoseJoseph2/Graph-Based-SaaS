import React, { useState } from 'react'
import { runSimulation } from '../api/client'
import { Calculator, TrendingUp } from 'lucide-react'

export default function SimulationTool() {
  const [form, setForm] = useState({
    referral_count: 100,
    reward_percent: 10,
    reward_depth: 3,
    base_reward_amount: 100,
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    setForm(f => ({ ...f, [e.target.name]: Number(e.target.value) }))
  }

  const handleRun = async () => {
    setLoading(true)
    try {
      const res = await runSimulation(form)
      setResult(res)
    } catch {}
    setLoading(false)
  }

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700">
      <div className="p-4 border-b border-slate-700 flex items-center gap-2">
        <Calculator size={16} className="text-indigo-400" />
        <h2 className="text-white font-semibold text-sm">Reward Simulation</h2>
      </div>

      <div className="p-4 grid grid-cols-2 gap-3">
        {[
          { name: 'referral_count', label: 'Referral Count', min: 1 },
          { name: 'reward_percent', label: 'Reward %', min: 0.1, step: 0.1 },
          { name: 'reward_depth', label: 'Depth Levels', min: 1, max: 6 },
          { name: 'base_reward_amount', label: 'Base Amount (₹)', min: 1 },
        ].map(field => (
          <div key={field.name}>
            <label className="text-slate-400 text-xs block mb-1">{field.label}</label>
            <input
              type="number"
              name={field.name}
              value={form[field.name]}
              onChange={handleChange}
              min={field.min}
              max={field.max}
              step={field.step || 1}
              className="w-full bg-slate-900 text-slate-200 text-sm rounded-lg px-3 py-1.5 border border-slate-600 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        ))}
      </div>

      <div className="px-4 pb-4">
        <button
          onClick={handleRun}
          disabled={loading}
          className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium py-2 rounded-lg transition-colors"
        >
          {loading ? 'Running…' : 'Run Simulation'}
        </button>
      </div>

      {result && (
        <div className="px-4 pb-4 space-y-3">
          <div className="bg-slate-900 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp size={14} className="text-emerald-400" />
              <span className="text-slate-300 text-xs font-medium">Projected Cost</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <p className="text-slate-500">Per referral</p>
                <p className="text-white font-semibold">₹{result.projected_cost_per_referral}</p>
              </div>
              <div>
                <p className="text-slate-500">Total ({result.total_referrals} referrals)</p>
                <p className="text-amber-400 font-bold text-base">₹{result.projected_total_cost}</p>
              </div>
            </div>
          </div>

          <div className="space-y-1">
            <p className="text-slate-500 text-xs uppercase tracking-wider">Breakdown by depth</p>
            {result.breakdown_by_depth.map(row => (
              <div key={row.depth} className="flex items-center gap-2 text-xs">
                <span className="text-slate-500 w-14">Level {row.depth}</span>
                <div className="flex-1 bg-slate-700 rounded-full h-1.5">
                  <div
                    className="bg-indigo-500 h-1.5 rounded-full"
                    style={{ width: `${Math.min(100, (row.reward_per_node / result.projected_cost_per_referral) * 100)}%` }}
                  />
                </div>
                <span className="text-slate-300 w-16 text-right">₹{row.reward_per_node}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
