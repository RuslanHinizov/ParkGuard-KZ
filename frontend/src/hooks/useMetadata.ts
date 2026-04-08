import { useEffect, useRef, useState } from 'react';
import type { StreamMetadata, WSStatus } from '../types';

const RECONNECT_DELAY = 3000;

export function useMetadata(cameraId: number, enabled: boolean = true) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const pingTimer = useRef<ReturnType<typeof setInterval>>();
  const [status, setStatus] = useState<WSStatus>('disconnected');
  const [metadata, setMetadata] = useState<StreamMetadata | null>(null);

  useEffect(() => {
    let cancelled = false;

    const cleanup = () => {
      clearTimeout(reconnectTimer.current);
      clearInterval(pingTimer.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };

    const connect = () => {
      if (!enabled || cancelled) {
        return;
      }

      setStatus('connecting');

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const ws = new WebSocket(`${protocol}//${host}/ws/metadata/${cameraId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('connected');
        pingTimer.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 10000);
      };

      ws.onmessage = (event) => {
        if (typeof event.data !== 'string') {
          return;
        }
        if (event.data.includes('"type":"pong"')) {
          return;
        }
        try {
          setMetadata(JSON.parse(event.data) as StreamMetadata);
        } catch {
          // noop
        }
      };

      ws.onclose = () => {
        clearInterval(pingTimer.current);
        setStatus('disconnected');
        wsRef.current = null;
        if (enabled && !cancelled) {
          reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    };

    connect();

    return () => {
      cancelled = true;
      cleanup();
      setStatus('disconnected');
    };
  }, [cameraId, enabled]);

  return { status, metadata };
}
