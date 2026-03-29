import React, { useState, useCallback, useEffect } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { fetchUsers, fetchUserGraph } from '../api/client'

const STATUS_COLOR = {
  active: '#10b981',
  flagged: '#f59e0b',
  suspended: '#ef4444',
}

function buildLayout(graphData) {
  const depthMap = {}
  graphData.nodes.forEach(n => {
    if (!depthMap[n.depth]) depthMap[n.depth] = []
    depthMap[n.depth].push(n)
  })

  const rfNodes = graphData.nodes.map(n => {
    const siblings = depthMap[n.depth] || [n]
    const idx = siblings.findIndex(s => s.id === n.id)
    const total = siblings.length
    const x = (idx - (total - 1) / 2) * 200
    const y = n.depth * 120

    return {
      id: n.id,
      position: { x, y },
      data: {
        label: (
          <div className="text-center px-2 py-1">
            <div className="font-semibold text-sm">{n.name}</div>
            <div className="text-xs text-slate-400">{n.email}</div>
            <div className="text-xs mt-0.5" style={{ color: STATUS_COLOR[n.status] }}>
              ● {n.status}
            </div>
            <div className="text-xs text-amber-400">₹{n.reward_balance}</div>
          </div>
        ),
      },
      style: {
        background: n.id === graphData.root_user ? '#1e40af' : '#1e293b',
        border: `2px solid ${STATUS_COLOR[n.status]}`,
        borderRadius: 10,
        padding: 4,
        minWidth: 130,
        color: '#e2e8f0',
      },
    }
  })

  const rfEdges = graphData.edges.map(e => ({
    id: e.referral_id,
    source: e.source,
    target: e.target,
    animated: true,
    markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1' },
    style: { stroke: '#6366f1' },
  }))

  return { rfNodes, rfEdges }
}

export default function GraphView() {
  const [users, setUsers] = useState([])
  const [selectedUser, setSelectedUser] = useState('')
  const [depth, setDepth] = useState(3)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  useEffect(() => {
    fetchUsers().then(setUsers).catch(() => {})
  }, [])

  const loadGraph = useCallback(async (uid, d) => {
    if (!uid) return
    setLoading(true)
    setError(null)
    try {
      const data = await fetchUserGraph(uid, d)
      if (data.nodes.length === 0) {
        setError('No graph data found for this user')
        setNodes([])
        setEdges([])
        return
      }
      const { rfNodes, rfEdges } = buildLayout(data)
      setNodes(rfNodes)
      setEdges(rfEdges)
    } catch (e) {
      setError('Failed to load graph')
    } finally {
      setLoading(false)
    }
  }, [setNodes, setEdges])

  const handleUserChange = (e) => {
    setSelectedUser(e.target.value)
    loadGraph(e.target.value, depth)
  }

  const handleDepthChange = (e) => {
    const d = Number(e.target.value)
    setDepth(d)
    if (selectedUser) loadGraph(selectedUser, d)
  }

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
      <div className="p-4 border-b border-slate-700 flex flex-wrap items-center gap-3">
        <h2 className="text-white font-semibold text-sm">Referral Graph</h2>

        <select
          value={selectedUser}
          onChange={handleUserChange}
          className="bg-slate-900 text-slate-300 text-sm rounded-lg px-3 py-1.5 border border-slate-600 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">Select a user…</option>
          {users.map(u => (
            <option key={u.id} value={u.id}>{u.name} ({u.referral_code})</option>
          ))}
        </select>

        <label className="text-slate-400 text-xs flex items-center gap-1">
          Depth
          <input
            type="number"
            min={1}
            max={6}
            value={depth}
            onChange={handleDepthChange}
            className="w-14 bg-slate-900 text-slate-300 text-sm rounded-lg px-2 py-1 border border-slate-600 focus:outline-none"
          />
        </label>

        {loading && <span className="text-indigo-400 text-xs animate-pulse">Loading…</span>}
        {error && <span className="text-red-400 text-xs">{error}</span>}
      </div>

      <div style={{ height: 420 }}>
        {nodes.length === 0 && !loading ? (
          <div className="flex items-center justify-center h-full text-slate-500 text-sm">
            Select a user to view their referral graph
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            fitView
            attributionPosition="bottom-right"
          >
            <Background color="#334155" gap={16} />
            <Controls />
            <MiniMap
              nodeColor={(n) => n.style?.border?.replace('2px solid ', '') || '#6366f1'}
              style={{ background: '#0f172a' }}
            />
          </ReactFlow>
        )}
      </div>
    </div>
  )
}
