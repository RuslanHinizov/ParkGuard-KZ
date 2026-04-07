import { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, BarChart3, Camera, Clock, Search, X } from 'lucide-react';
import { useStore } from '../store/useStore';

const API_BASE = '/api';

interface PlateStats {
  plate: string;
  total_violations: number;
  unique_cameras: number;
  first_seen: string;
  last_seen: string;
  avg_duration_sec: number;
  camera_distribution: Record<string, number>;
}

interface PlateAlarm {
  id: string;
  camera_id: number;
  camera_name: string;
  zone_name: string;
  duration_sec: number;
  status: string;
  screenshot: string;
  created_at: string;
}

interface TopPlate {
  plate: string;
  count: number;
}

function normalizeTopPlates(data: any): TopPlate[] {
  const rawList = Array.isArray(data) ? data : data?.plates ?? [];
  return rawList.map((item: any) => ({
    plate: item?.plate ?? '',
    count: item?.count ?? item?.total_violations ?? 0,
  }));
}

function normalizeStats(payload: any): PlateStats {
  const stats = payload?.stats ?? payload ?? {};
  const cameraRows = payload?.by_camera ?? [];

  return {
    plate: payload?.plate ?? '',
    total_violations: stats?.total_violations ?? stats?.total ?? 0,
    unique_cameras: stats?.unique_cameras ?? stats?.cameras ?? 0,
    first_seen: stats?.first_seen ?? '',
    last_seen: stats?.last_seen ?? '',
    avg_duration_sec: stats?.avg_duration_sec ?? stats?.avg_duration ?? 0,
    camera_distribution: Object.fromEntries(
      cameraRows.map((row: any) => [
        row?.camera_name ?? `Camera ${row?.camera_id ?? '?'}`,
        row?.count ?? 0,
      ])
    ),
  };
}

function normalizeAlarms(payload: any): PlateAlarm[] {
  const rawList = payload?.alarms ?? [];
  return rawList.map((alarm: any) => ({
    id: String(alarm?.id ?? crypto.randomUUID()),
    camera_id: alarm?.camera_id ?? 0,
    camera_name: alarm?.camera_name ?? `Camera ${alarm?.camera_id ?? '?'}`,
    zone_name: alarm?.zone_name ?? '-',
    duration_sec: alarm?.duration_sec ?? 0,
    status: alarm?.status ?? 'active',
    screenshot: alarm?.screenshot ? `${API_BASE}/alarms/${alarm.id}/screenshot` : '',
    created_at: alarm?.created_at ?? '',
  }));
}

export default function PlateHistory() {
  const selectedPlateQuery = useStore((s) => s.selectedPlateQuery);
  const setSelectedPlateQuery = useStore((s) => s.setSelectedPlateQuery);

  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [stats, setStats] = useState<PlateStats | null>(null);
  const [alarms, setAlarms] = useState<PlateAlarm[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [topPlates, setTopPlates] = useState<TopPlate[]>([]);
  const [previewImg, setPreviewImg] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/plates/top`)
      .then((res) => res.json())
      .then((data) => setTopPlates(normalizeTopPlates(data)))
      .catch(() => {});
  }, []);

  const searchPlate = useCallback(async (plateNum?: string) => {
    const searchValue = (plateNum ?? query).trim().toUpperCase();
    if (!searchValue) return;

    setSearching(true);
    setError(null);
    setStats(null);
    setAlarms([]);

    try {
      const res = await fetch(`${API_BASE}/plates/${encodeURIComponent(searchValue)}/history`);
      if (!res.ok) {
        setError(res.status === 404 ? 'Plate not found' : `Request failed: ${res.status}`);
        return;
      }

      const data = await res.json();
      const normalizedStats = normalizeStats(data);
      const normalizedAlarms = normalizeAlarms(data);

      if (normalizedStats.total_violations === 0 && normalizedAlarms.length === 0) {
        setError('Plate not found');
        return;
      }

      setStats(normalizedStats);
      setAlarms(normalizedAlarms);
    } catch {
      setError('Network error');
    } finally {
      setSearching(false);
    }
  }, [query]);

  useEffect(() => {
    if (!selectedPlateQuery) return;
    setQuery(selectedPlateQuery);
    void searchPlate(selectedPlateQuery);
    setSelectedPlateQuery('');
  }, [searchPlate, selectedPlateQuery, setSelectedPlateQuery]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      void searchPlate();
    }
  };

  const formatDate = (iso: string) => {
    if (!iso) return '-';
    try {
      return new Date(iso).toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return iso;
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    if (mins === 0) return `${secs} sec`;
    return `${mins} min ${secs} sec`;
  };

  const maxCameraCount = stats
    ? Math.max(...Object.values(stats.camera_distribution), 1)
    : 1;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-3">
        <BarChart3 className="w-6 h-6 text-blue-400" />
        <h2 className="text-xl font-bold">Plate History</h2>
      </div>

      <div className="bg-gray-900 rounded-lg p-5 border border-gray-800">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value.toUpperCase())}
              onKeyDown={handleKeyDown}
              placeholder="Enter plate number"
              className="w-full bg-gray-800 text-white placeholder-gray-600 rounded-lg pl-10 pr-4 py-2.5 text-sm border border-gray-700 focus:outline-none focus:border-blue-500 font-mono tracking-wider"
            />
          </div>
          <button
            onClick={() => void searchPlate()}
            disabled={searching || !query.trim()}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium px-6 py-2 rounded-lg transition-colors"
          >
            <Search className="w-4 h-4" />
            {searching ? 'Searching...' : 'Search'}
          </button>
        </div>

        {topPlates.length > 0 && !stats && (
          <div className="mt-4">
            <p className="text-xs text-gray-500 mb-2">Top violators:</p>
            <div className="flex flex-wrap gap-2">
              {topPlates.map((item) => (
                <button
                  key={item.plate}
                  onClick={() => {
                    setQuery(item.plate);
                    void searchPlate(item.plate);
                  }}
                  className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-1.5 rounded-lg transition-colors border border-gray-700 font-mono"
                >
                  {item.plate} <span className="text-red-400 ml-1">({item.count})</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 text-sm text-red-400">
          {error}
        </div>
      )}

      {stats && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
              <p className="text-xs text-gray-500 mb-1">Violations</p>
              <p className="text-2xl font-bold text-red-400">{stats.total_violations}</p>
            </div>
            <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
              <p className="text-xs text-gray-500 mb-1">Cameras</p>
              <p className="text-2xl font-bold text-blue-400">{stats.unique_cameras}</p>
            </div>
            <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
              <p className="text-xs text-gray-500 mb-1">First seen</p>
              <p className="text-sm font-medium text-gray-300 mt-1">{formatDate(stats.first_seen)}</p>
            </div>
            <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
              <p className="text-xs text-gray-500 mb-1">Last seen</p>
              <p className="text-sm font-medium text-gray-300 mt-1">{formatDate(stats.last_seen)}</p>
            </div>
            <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
              <p className="text-xs text-gray-500 mb-1">Avg duration</p>
              <p className="text-lg font-bold text-yellow-400">{formatDuration(stats.avg_duration_sec)}</p>
            </div>
          </div>

          {Object.keys(stats.camera_distribution).length > 0 && (
            <div className="bg-gray-900 rounded-lg p-5 border border-gray-800">
              <h3 className="text-sm font-semibold text-gray-400 mb-4 flex items-center gap-2">
                <Camera className="w-4 h-4" />
                Camera distribution
              </h3>
              <div className="space-y-3">
                {Object.entries(stats.camera_distribution).map(([cameraName, count]) => (
                  <div key={cameraName} className="flex items-center gap-3">
                    <span className="text-sm text-gray-300 w-32 truncate">{cameraName}</span>
                    <div className="flex-1 bg-gray-800 rounded-full h-5 overflow-hidden">
                      <div
                        className="bg-blue-600 h-full rounded-full transition-all duration-500 flex items-center justify-end pr-2"
                        style={{ width: `${Math.max((count / maxCameraCount) * 100, 10)}%` }}
                      >
                        <span className="text-xs text-white font-medium">{count}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {alarms.length > 0 && (
        <div className="bg-gray-900 rounded-lg border border-gray-800">
          <div className="px-5 py-4 border-b border-gray-800">
            <h3 className="text-sm font-semibold text-gray-400 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              Violations ({alarms.length})
            </h3>
          </div>
          <div className="divide-y divide-gray-800">
            {alarms.map((alarm) => (
              <div
                key={alarm.id}
                className="px-5 py-3 flex items-center gap-4 hover:bg-gray-800/50 transition-colors"
              >
                {alarm.screenshot && (
                  <button onClick={() => setPreviewImg(alarm.screenshot)} className="flex-shrink-0">
                    <img
                      src={alarm.screenshot}
                      alt="Violation screenshot"
                      className="w-20 h-14 object-cover rounded border border-gray-700 hover:border-blue-500 transition-colors cursor-pointer"
                    />
                  </button>
                )}

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <Camera className="w-3 h-3 text-gray-500" />
                    <span className="text-sm text-gray-300">{alarm.camera_name}</span>
                    <span className="text-xs text-gray-600">&middot;</span>
                    <span className="text-xs text-gray-500">{alarm.zone_name}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <Clock className="w-3 h-3 text-gray-500" />
                    <span className="text-xs text-gray-400">{formatDate(alarm.created_at)}</span>
                    <span className="text-xs text-yellow-500">{formatDuration(alarm.duration_sec)}</span>
                  </div>
                </div>

                <span
                  className={`text-xs px-2 py-0.5 rounded font-medium flex-shrink-0 ${
                    alarm.status === 'active'
                      ? 'bg-red-900/50 text-red-400'
                      : 'bg-green-900/50 text-green-400'
                  }`}
                >
                  {alarm.status === 'active' ? 'Active' : 'Resolved'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {previewImg && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
          onClick={() => setPreviewImg(null)}
        >
          <div className="relative max-w-4xl max-h-[90vh]" onClick={(event) => event.stopPropagation()}>
            <button
              onClick={() => setPreviewImg(null)}
              className="absolute -top-3 -right-3 bg-gray-800 text-white rounded-full p-1 hover:bg-gray-700 transition-colors z-10"
            >
              <X className="w-5 h-5" />
            </button>
            <img
              src={previewImg}
              alt="Violation screenshot"
              className="max-w-full max-h-[85vh] object-contain rounded-lg"
            />
          </div>
        </div>
      )}
    </div>
  );
}
