import { useEffect, useRef, useCallback, useState } from 'react';
import type { WSStatus } from '../types';

const RECONNECT_DELAY = 3000;

interface UseWebSocketOptions {
  url: string;
  onMessage?: (data: MessageEvent) => void;
  onOpen?: () => void;
  onClose?: () => void;
  enabled?: boolean;
}

export function useWebSocket({ url, onMessage, onOpen, onClose, enabled = true }: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const [status, setStatus] = useState<WSStatus>('disconnected');

  // Callback'leri ref'te tut — her render'da yeni referans olsa da connect yeniden oluşmaz
  const onMessageRef = useRef(onMessage);
  const onOpenRef = useRef(onOpen);
  const onCloseRef = useRef(onClose);
  const enabledRef = useRef(enabled);

  useEffect(() => {
    onMessageRef.current = onMessage;
    onOpenRef.current = onOpen;
    onCloseRef.current = onClose;
    enabledRef.current = enabled;
  });

  const connect = useCallback(() => {
    if (!enabledRef.current) return;

    try {
      setStatus('connecting');

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const fullUrl = `${protocol}//${host}${url}`;

      const ws = new WebSocket(fullUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('connected');
        onOpenRef.current?.();
      };

      ws.onmessage = (event) => {
        onMessageRef.current?.(event);
      };

      ws.onclose = () => {
        setStatus('disconnected');
        onCloseRef.current?.();
        wsRef.current = null;

        // Otomatik reconnect (3sn bekle)
        if (enabledRef.current) {
          reconnectTimer.current = setTimeout(() => {
            connect();
          }, RECONNECT_DELAY);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      setStatus('disconnected');
      if (enabledRef.current) {
        reconnectTimer.current = setTimeout(() => {
          connect();
        }, RECONNECT_DELAY);
      }
    }
  }, [url]); // Sadece url değişirse yeniden bağlan

  useEffect(() => {
    connect();

    return () => {
      clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  const send = useCallback((data: string | ArrayBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(data);
    }
  }, []);

  return { status, send, ws: wsRef };
}
