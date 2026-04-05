import { useEffect, useRef, useCallback, useState } from 'react';
import type { WSStatus } from '../types';

const RECONNECT_DELAY = 3000;

/**
 * Kamera stream hook'u.
 * WebSocket üzerinden binary JPEG frame alır.
 * Frame'leri canvas veya img'ye çizer.
 */
export function useStream(cameraId: number, enabled: boolean = true) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const [status, setStatus] = useState<WSStatus>('disconnected');
  const [frameUrl, setFrameUrl] = useState<string>('');
  const prevBlobUrl = useRef<string>('');

  // enabled'ı ref'te tut — closure'lar hep güncel değeri okur
  const enabledRef = useRef(enabled);
  useEffect(() => {
    enabledRef.current = enabled;
  });

  const connect = useCallback(() => {
    if (!enabledRef.current) return;

    try {
      setStatus('connecting');

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const ws = new WebSocket(`${protocol}//${host}/ws/stream/${cameraId}`);
      ws.binaryType = 'arraybuffer';
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('connected');
        // Keep-alive ping
        ws.send('ping');
      };

      ws.onmessage = (event) => {
        if (event.data instanceof ArrayBuffer) {
          // Önceki blob URL'i temizle (memory leak önleme)
          if (prevBlobUrl.current) {
            URL.revokeObjectURL(prevBlobUrl.current);
          }
          const blob = new Blob([event.data], { type: 'image/jpeg' });
          const url = URL.createObjectURL(blob);
          prevBlobUrl.current = url;
          setFrameUrl(url);
        }
      };

      ws.onclose = () => {
        setStatus('disconnected');
        wsRef.current = null;

        // enabledRef kullan — enabled prop'unun her zaman güncel değerini okur
        if (enabledRef.current) {
          reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      setStatus('disconnected');
      if (enabledRef.current) {
        reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY);
      }
    }
  }, [cameraId]); // enabled bağımlılıktan çıkarıldı — ref üzerinden okunuyor

  useEffect(() => {
    connect();

    return () => {
      clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (prevBlobUrl.current) {
        URL.revokeObjectURL(prevBlobUrl.current);
      }
    };
  }, [connect]);

  return { status, frameUrl };
}
