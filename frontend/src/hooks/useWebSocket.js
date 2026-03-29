import { useEffect, useRef, useCallback } from 'react'

export function useWebSocket(onMessage) {
  const wsRef = useRef(null)
  const onMessageRef = useRef(onMessage)
  const mountedRef = useRef(true)
  onMessageRef.current = onMessage

  const connect = useCallback(() => {
    if (!mountedRef.current) return
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${protocol}://${window.location.host}/ws/dashboard/ws`)

    ws.onopen = () => {
      onMessageRef.current({ event: '__connected__', data: {} })
    }
    ws.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data)
        onMessageRef.current(payload)
      } catch {}
    }
    ws.onclose = () => {
      if (mountedRef.current) {
        setTimeout(connect, 3000)
      }
    }
    ws.onerror = () => ws.close()
    wsRef.current = ws
  }, [])

  useEffect(() => {
    mountedRef.current = true
    connect()
    return () => {
      mountedRef.current = false
      wsRef.current?.close()
    }
  }, [connect])
}
