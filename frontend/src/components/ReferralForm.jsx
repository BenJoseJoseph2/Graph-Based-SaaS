import React, { useState } from 'react'
import { claimReferral, createUser } from '../api/client'
import { UserPlus, Link } from 'lucide-react'

export default function ReferralForm({ onSuccess }) {
  const [tab, setTab] = useState('claim')

  // Claim referral
  const [claimForm, setClaimForm] = useState({ new_user_id: '', referrer_code: '' })
  const [claimResult, setClaimResult] = useState(null)

  // Create user
  const [userForm, setUserForm] = useState({ name: '', email: '' })
  const [userResult, setUserResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleClaim = async (e) => {
    e.preventDefault()
    setLoading(true)
    setClaimResult(null)
    try {
      const res = await claimReferral(claimForm)
      setClaimResult(res)
      if (res.success && onSuccess) onSuccess()
    } catch (err) {
      setClaimResult({ success: false, message: err.response?.data?.detail || 'Error' })
    }
    setLoading(false)
  }

  const handleCreateUser = async (e) => {
    e.preventDefault()
    setLoading(true)
    setUserResult(null)
    try {
      const res = await createUser(userForm)
      setUserResult({ success: true, user: res })
      if (onSuccess) onSuccess()
    } catch (err) {
      setUserResult({ success: false, message: err.response?.data?.detail || 'Error' })
    }
    setLoading(false)
  }

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700">
      <div className="flex border-b border-slate-700">
        {[
          { id: 'claim', label: 'Claim Referral', icon: Link },
          { id: 'user', label: 'Add User', icon: UserPlus },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm transition-colors ${
              tab === t.id
                ? 'text-indigo-400 border-b-2 border-indigo-400 font-medium'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            <t.icon size={14} />
            {t.label}
          </button>
        ))}
      </div>

      <div className="p-4">
        {tab === 'claim' && (
          <form onSubmit={handleClaim} className="space-y-3">
            <div>
              <label className="text-slate-400 text-xs block mb-1">New User ID</label>
              <input
                required
                value={claimForm.new_user_id}
                onChange={e => setClaimForm(f => ({ ...f, new_user_id: e.target.value }))}
                placeholder="UUID of new user"
                className="w-full bg-slate-900 text-slate-200 text-sm rounded-lg px-3 py-2 border border-slate-600 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="text-slate-400 text-xs block mb-1">Referrer Code</label>
              <input
                required
                value={claimForm.referrer_code}
                onChange={e => setClaimForm(f => ({ ...f, referrer_code: e.target.value }))}
                placeholder="e.g. ALICE001"
                className="w-full bg-slate-900 text-slate-200 text-sm rounded-lg px-3 py-2 border border-slate-600 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium py-2 rounded-lg transition-colors"
            >
              {loading ? 'Processing…' : 'Claim Referral'}
            </button>
            {claimResult && (
              <div className={`rounded-lg p-3 text-xs ${claimResult.success ? 'bg-emerald-900/40 text-emerald-300' : 'bg-red-900/40 text-red-300'}`}>
                <p className="font-medium">{claimResult.success ? '✓ Success' : '✗ Rejected'}</p>
                <p>{claimResult.message}</p>
                {claimResult.rewards_distributed?.length > 0 && (
                  <p className="mt-1 text-amber-300">
                    Rewards: {claimResult.rewards_distributed.map(r => `₹${r.amount} (L${r.depth})`).join(', ')}
                  </p>
                )}
              </div>
            )}
          </form>
        )}

        {tab === 'user' && (
          <form onSubmit={handleCreateUser} className="space-y-3">
            <div>
              <label className="text-slate-400 text-xs block mb-1">Name</label>
              <input
                required
                value={userForm.name}
                onChange={e => setUserForm(f => ({ ...f, name: e.target.value }))}
                placeholder="Full name"
                className="w-full bg-slate-900 text-slate-200 text-sm rounded-lg px-3 py-2 border border-slate-600 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="text-slate-400 text-xs block mb-1">Email</label>
              <input
                required
                type="email"
                value={userForm.email}
                onChange={e => setUserForm(f => ({ ...f, email: e.target.value }))}
                placeholder="user@example.com"
                className="w-full bg-slate-900 text-slate-200 text-sm rounded-lg px-3 py-2 border border-slate-600 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-white text-sm font-medium py-2 rounded-lg transition-colors"
            >
              {loading ? 'Creating…' : 'Create User'}
            </button>
            {userResult && (
              <div className={`rounded-lg p-3 text-xs ${userResult.success ? 'bg-emerald-900/40 text-emerald-300' : 'bg-red-900/40 text-red-300'}`}>
                {userResult.success ? (
                  <>
                    <p className="font-medium">✓ User Created</p>
                    <p>Code: <span className="font-mono text-white">{userResult.user.referral_code}</span></p>
                    <p>ID: <span className="font-mono text-slate-400">{userResult.user.id}</span></p>
                  </>
                ) : (
                  <p>{userResult.message}</p>
                )}
              </div>
            )}
          </form>
        )}
      </div>
    </div>
  )
}
