import { useEffect, useState, useCallback } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts';
import { useStore } from '../store/useStore';
import { useWebSocket } from '../hooks/useWebSocket';
import { useTranslation } from '../i18n/useTranslation';
import type { HourlyStat, CameraStat, SystemStats } from '../types';

const API_BASE = '/api';
const PIE_COLORS = ['#3b82f6', '#ef4444', '#22c55e', '#f59e0b'];

export default function StatsChart() {
  const stats = useStore((s) => s.stats);
  const setStats = useStore((s) => s.setStats);
  const todayStats = useStore((s) => s.todayStats);
  const setTodayStats = useStore((s) => s.setTodayStats);
  const { t } = useTranslation();

  const [hourly, setHourly] = useState<HourlyStat[]>([]);
  const [cameraStats, setCameraStats] = useState<CameraStat[]>([]);

  useEffect(() => {
    fetch(`${API_BASE}/stats/today`).then((r) => r.json()).then(setTodayStats).catch(() => {});
    fetch(`${API_BASE}/stats/hourly`).then((r) => r.json()).then((d) => { if (Array.isArray(d)) setHourly(d); }).catch(() => {});
    fetch(`${API_BASE}/stats/cameras`).then((r) => r.json()).then((d) => { if (Array.isArray(d)) setCameraStats(d); }).catch(() => {});
  }, [setTodayStats]);

  const onStatsMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data: SystemStats = JSON.parse(event.data);
        setStats(data);
      } catch { /* parse hatası */ }
    },
    [setStats]
  );

  useWebSocket({ url: '/ws/stats', onMessage: onStatsMessage });

  return (
    <div className="space-y-4">
      {/* Özet kartlar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard title={t('stats.total')}    value={todayStats?.total_alarms ?? 0} color="text-blue-400" />
        <StatCard title={t('stats.active')}   value={todayStats?.active ?? 0}        color="text-red-400" />
        <StatCard title={t('stats.resolved')} value={todayStats?.resolved ?? 0}      color="text-green-400" />
        <StatCard title={t('stats.cpu')}      value={`${stats?.cpu ?? 0}%`}          color="text-yellow-400" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* FPS */}
        <div className="bg-gray-900 rounded-lg p-4">
          <h3 className="text-sm font-bold text-gray-400 mb-3">{t('stats.camera_fps')}</h3>
          {stats?.cameras
            ? Object.entries(stats.cameras).map(([id, cam]) => (
                <div key={id} className="flex items-center justify-between py-1">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${cam.connected ? 'bg-green-500' : 'bg-red-500'}`} />
                    <span className="text-sm">{cam.name}</span>
                  </div>
                  <span className="font-mono text-sm">{cam.fps.toFixed(1)} FPS</span>
                </div>
              ))
            : <p className="text-sm text-gray-500">{t('stats.loading')}</p>
          }
        </div>

        {/* RAM & GPU */}
        <div className="bg-gray-900 rounded-lg p-4">
          <h3 className="text-sm font-bold text-gray-400 mb-3">{t('stats.system')}</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">{t('stats.ram')}</span>
              <span>{stats?.ram ?? '-'} GB</span>
            </div>
            {stats?.gpu !== undefined && (
              <div className="flex justify-between">
                <span className="text-gray-400">{t('stats.vram')}</span>
                <span>{stats.gpu} / {stats.vram ?? '?'} GB</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-gray-400">{t('stats.cpu')}</span>
              <span>{stats?.cpu ?? '-'}%</span>
            </div>
          </div>
        </div>

        {/* Kamera bazlı alarmlar */}
        <div className="bg-gray-900 rounded-lg p-4">
          <h3 className="text-sm font-bold text-gray-400 mb-3">{t('stats.camera_alarms')}</h3>
          {cameraStats.length > 0 ? (
            <ResponsiveContainer width="100%" height={150}>
              <PieChart>
                <Pie data={cameraStats} dataKey="alarm_count" nameKey="name" cx="50%" cy="50%" outerRadius={55}
                  label={({ name, value }) => `${name}: ${value}`}>
                  {cameraStats.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-gray-500">{t('stats.no_data')}</p>
          )}
        </div>
      </div>

      {/* Saatlik grafik */}
      <div className="bg-gray-900 rounded-lg p-4">
        <h3 className="text-sm font-bold text-gray-400 mb-3">{t('stats.hourly_title')}</h3>
        {hourly.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={hourly}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="hour" tick={{ fill: '#9ca3af', fontSize: 12 }} tickFormatter={(h) => `${h}:00`} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 12 }} />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }} />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-[250px] flex items-center justify-center text-gray-500">
            {t('stats.no_data')}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ title, value, color }: { title: string; value: string | number; color: string }) {
  return (
    <div className="bg-gray-900 rounded-lg p-4">
      <p className="text-xs text-gray-400 mb-1">{title}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}
