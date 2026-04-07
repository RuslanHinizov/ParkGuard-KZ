import { useEffect, useRef, useState } from 'react';
import {
  AlertTriangle,
  Bell,
  Check,
  Eye,
  TrendingUp,
  X,
  Zap,
} from 'lucide-react';

const API_BASE = '/api';

interface Anomaly {
  id: string;
  type: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  acknowledged: boolean;
  created_at: string;
}

const ANOMALY_ICONS: Record<string, typeof AlertTriangle> = {
  spike: TrendingUp,
  camera_down: AlertTriangle,
  unusual_activity: Eye,
  repeat_offender: Eye,
  system: Zap,
  other: Bell,
};

const SEVERITY_COLORS: Record<Anomaly['severity'], string> = {
  high: 'text-red-400',
  medium: 'text-yellow-400',
  low: 'text-blue-400',
};

const SEVERITY_BG: Record<Anomaly['severity'], string> = {
  high: 'bg-red-900/30 border-red-800',
  medium: 'bg-yellow-900/30 border-yellow-800',
  low: 'bg-blue-900/30 border-blue-800',
};

const TYPE_LABELS: Record<string, string> = {
  spike: 'Spike',
  camera_down: 'Camera down',
  unusual_activity: 'Unusual activity',
  repeat_offender: 'Repeat offender',
  system: 'System',
  other: 'Other',
};

function normalizeAnomaly(item: any): Anomaly {
  const type = item?.type ?? item?.anomaly_type ?? 'other';
  const severity: Anomaly['severity'] =
    item?.severity ??
    (type === 'spike' ? 'high' : type === 'repeat_offender' ? 'medium' : 'low');

  return {
    id: String(item?.id ?? crypto.randomUUID()),
    type,
    description: item?.description ?? '',
    severity,
    acknowledged: Boolean(item?.acknowledged),
    created_at: item?.created_at ?? new Date().toISOString(),
  };
}

export default function AnomalyBadge() {
  const [count, setCount] = useState(0);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  const fetchCount = async () => {
    try {
      const res = await fetch(`${API_BASE}/anomalies/count`);
      if (!res.ok) return;

      const data = await res.json();
      setCount(data.count ?? data.unacknowledged ?? 0);
    } catch {
      // noop
    }
  };

  const fetchAnomalies = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/anomalies`);
      if (!res.ok) return;

      const data = await res.json();
      const rawList = data.items ?? data.anomalies ?? (Array.isArray(data) ? data : []);
      setAnomalies(rawList.map(normalizeAnomaly));
    } catch {
      // noop
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchCount();
    const interval = setInterval(fetchCount, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handler = (event: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleToggle = () => {
    if (!open) {
      void fetchAnomalies();
    }
    setOpen((prev) => !prev);
  };

  const handleAcknowledge = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/anomalies/${id}/acknowledge`, {
        method: 'PUT',
      });
      if (!res.ok) return;

      setAnomalies((prev) =>
        prev.map((item) => (item.id === id ? { ...item, acknowledged: true } : item))
      );
      setCount((prev) => Math.max(0, prev - 1));
    } catch {
      // noop
    }
  };

  const formatDate = (iso: string) => {
    try {
      const date = new Date(iso);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMinutes = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);

      if (diffMinutes < 1) return 'Just now';
      if (diffMinutes < 60) return `${diffMinutes} min ago`;
      if (diffHours < 24) return `${diffHours} h ago`;

      return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return iso;
    }
  };

  const unacknowledged = anomalies.filter((item) => !item.acknowledged);
  const acknowledged = anomalies.filter((item) => item.acknowledged);

  return (
    <div ref={panelRef} className="relative">
      <button
        onClick={handleToggle}
        className="relative p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
        title="Anomalies"
      >
        <Bell className="w-5 h-5" />
        {count > 0 && (
          <span className="absolute -top-0.5 -right-0.5 bg-red-600 text-white text-[10px] font-bold min-w-[18px] h-[18px] flex items-center justify-center rounded-full px-1 animate-pulse">
            {count > 99 ? '99+' : count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute top-full right-0 mt-2 w-96 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl z-50 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-yellow-400" />
              <h3 className="text-sm font-semibold text-white">Anomalies</h3>
              {count > 0 && (
                <span className="text-xs bg-red-900/50 text-red-400 px-1.5 py-0.5 rounded-full">
                  {count}
                </span>
              )}
            </div>
            <button
              onClick={() => setOpen(false)}
              className="text-gray-500 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-8 text-gray-500 text-sm">
                Loading...
              </div>
            ) : anomalies.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Bell className="w-8 h-8 mx-auto mb-2 text-gray-700" />
                <p className="text-sm">No anomalies</p>
                <p className="text-xs text-gray-600 mt-1">System is operating normally</p>
              </div>
            ) : (
              <>
                {unacknowledged.length > 0 && (
                  <div>
                    <div className="px-4 py-2 bg-gray-800/50">
                      <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">
                        New ({unacknowledged.length})
                      </p>
                    </div>
                    {unacknowledged.map((anomaly) => {
                      const Icon = ANOMALY_ICONS[anomaly.type] ?? Bell;
                      return (
                        <div
                          key={anomaly.id}
                          className={`px-4 py-3 border-l-2 ${SEVERITY_BG[anomaly.severity]} hover:bg-gray-800/30 transition-colors`}
                        >
                          <div className="flex items-start gap-3">
                            <div className="mt-0.5">
                              <Icon className={`w-4 h-4 ${SEVERITY_COLORS[anomaly.severity]}`} />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-0.5">
                                <span className={`text-xs font-medium ${SEVERITY_COLORS[anomaly.severity]}`}>
                                  {TYPE_LABELS[anomaly.type] ?? anomaly.type}
                                </span>
                                <span className="text-xs text-gray-600">
                                  {formatDate(anomaly.created_at)}
                                </span>
                              </div>
                              <p className="text-sm text-gray-300 leading-snug">
                                {anomaly.description}
                              </p>
                            </div>
                            <button
                              onClick={() => void handleAcknowledge(anomaly.id)}
                              className="flex-shrink-0 p-1.5 rounded-lg text-gray-500 hover:text-green-400 hover:bg-green-900/20 transition-colors"
                              title="Acknowledge"
                            >
                              <Check className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {acknowledged.length > 0 && (
                  <div>
                    <div className="px-4 py-2 bg-gray-800/50">
                      <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">
                        Acknowledged ({acknowledged.length})
                      </p>
                    </div>
                    {acknowledged.slice(0, 5).map((anomaly) => {
                      const Icon = ANOMALY_ICONS[anomaly.type] ?? Bell;
                      return (
                        <div
                          key={anomaly.id}
                          className="px-4 py-3 border-l-2 border-gray-800 opacity-60 hover:opacity-80 transition-opacity"
                        >
                          <div className="flex items-start gap-3">
                            <div className="mt-0.5">
                              <Icon className="w-4 h-4 text-gray-500" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-0.5">
                                <span className="text-xs font-medium text-gray-500">
                                  {TYPE_LABELS[anomaly.type] ?? anomaly.type}
                                </span>
                                <span className="text-xs text-gray-600">
                                  {formatDate(anomaly.created_at)}
                                </span>
                              </div>
                              <p className="text-sm text-gray-500 leading-snug">
                                {anomaly.description}
                              </p>
                            </div>
                            <Check className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
