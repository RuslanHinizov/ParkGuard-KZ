import { useState, useEffect, useRef, useCallback } from 'react';
import { useTranslation } from '../i18n/useTranslation';
import { useWebSocket } from '../hooks/useWebSocket';

interface LogEntry {
  seq: number;
  time: string;
  level: string;
  name: string;
  message: string;
}

type LevelFilter = 'ALL' | 'INFO' | 'WARNING' | 'ERROR';

const LEVEL_COLORS: Record<string, string> = {
  DEBUG:    'text-gray-400',
  INFO:     'text-blue-400',
  WARNING:  'text-yellow-400',
  WARN:     'text-yellow-400',
  ERROR:    'text-red-400',
  CRITICAL: 'text-red-500',
};

const LEVEL_BG: Record<string, string> = {
  ERROR:    'bg-red-950/30',
  CRITICAL: 'bg-red-950/50',
  WARNING:  'bg-yellow-950/20',
  WARN:     'bg-yellow-950/20',
};

export default function LogViewer() {
  const { t } = useTranslation();
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [levelFilter, setLevelFilter] = useState<LevelFilter>('ALL');
  const [autoScroll, setAutoScroll] = useState(true);
  const [connected, setConnected] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const onMessage = useCallback((data: string) => {
    try {
      const msg = JSON.parse(data) as { entries: LogEntry[] };
      if (msg.entries?.length) {
        setEntries((prev) => {
          const combined = [...prev, ...msg.entries];
          // Keep last 500
          return combined.length > 500 ? combined.slice(-500) : combined;
        });
      }
    } catch {
      // ignore malformed
    }
  }, []);

  const onOpen = useCallback(() => setConnected(true), []);
  const onClose = useCallback(() => setConnected(false), []);

  useWebSocket('/ws/logs', { onMessage, onOpen, onClose });

  // Auto-scroll to bottom when new entries arrive
  useEffect(() => {
    if (autoScroll) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [entries, autoScroll]);

  const visible = entries.filter((e) => {
    if (levelFilter === 'ALL') return true;
    if (levelFilter === 'ERROR') return e.level === 'ERROR' || e.level === 'CRITICAL';
    if (levelFilter === 'WARNING') return e.level === 'WARNING' || e.level === 'WARN';
    if (levelFilter === 'INFO') return e.level === 'INFO' || e.level === 'DEBUG';
    return true;
  });

  const FILTERS: { key: LevelFilter; label: string }[] = [
    { key: 'ALL',     label: t('logs.filter_all') },
    { key: 'INFO',    label: t('logs.filter_info') },
    { key: 'WARNING', label: t('logs.filter_warn') },
    { key: 'ERROR',   label: t('logs.filter_error') },
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] bg-gray-950">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-800 flex-shrink-0">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-semibold text-gray-200">{t('logs.title')}</h2>
          {/* Connection badge */}
          <span className={`text-xs px-2 py-0.5 rounded-full ${
            connected ? 'bg-green-900 text-green-300' : 'bg-gray-800 text-gray-400'
          }`}>
            {connected ? 'LIVE' : t('logs.connecting')}
          </span>
          <span className="text-xs text-gray-500">{visible.length} / {entries.length}</span>
        </div>

        <div className="flex items-center gap-2">
          {/* Level filter */}
          <div className="flex gap-1">
            {FILTERS.map((f) => (
              <button
                key={f.key}
                onClick={() => setLevelFilter(f.key)}
                className={`text-xs px-2 py-1 rounded transition-all ${
                  levelFilter === f.key
                    ? 'bg-blue-700 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* Auto-scroll toggle */}
          <button
            onClick={() => setAutoScroll((v) => !v)}
            className={`text-xs px-3 py-1 rounded transition-all ${
              autoScroll
                ? 'bg-green-800 text-green-300'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            {t('logs.auto_scroll')}
          </button>

          {/* Clear */}
          <button
            onClick={() => setEntries([])}
            className="text-xs px-3 py-1 rounded bg-gray-800 text-gray-400 hover:bg-gray-700 transition-all"
          >
            {t('logs.clear')}
          </button>
        </div>
      </div>

      {/* Log list */}
      <div className="flex-1 overflow-y-auto font-mono text-xs">
        {visible.length === 0 ? (
          <div className="text-gray-600 text-center mt-16">{t('logs.no_logs')}</div>
        ) : (
          visible.map((entry) => (
            <div
              key={entry.seq}
              className={`flex gap-2 px-3 py-0.5 border-b border-gray-900 hover:bg-gray-900/50 ${
                LEVEL_BG[entry.level] ?? ''
              }`}
            >
              <span className="text-gray-600 flex-shrink-0 w-20">{entry.time}</span>
              <span className={`flex-shrink-0 w-14 font-bold ${LEVEL_COLORS[entry.level] ?? 'text-gray-300'}`}>
                {entry.level}
              </span>
              <span className="text-gray-500 flex-shrink-0 w-36 truncate" title={entry.name}>
                {entry.name}
              </span>
              <span className="text-gray-300 break-all">{entry.message}</span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
