import { useCallback } from 'react';
import { useStore } from '../store/useStore';
import { useWebSocket } from '../hooks/useWebSocket';
import { useTranslation } from '../i18n/useTranslation';
import { Camera, Wifi, WifiOff, Moon, Activity, Monitor } from 'lucide-react';
import type { SystemStats } from '../types';

export default function CameraHealth() {
  const stats    = useStore((s) => s.stats);
  const setStats = useStore((s) => s.setStats);
  const { t }    = useTranslation();

  const onStatsMessage = useCallback(
    (event: MessageEvent) => {
      try { setStats(JSON.parse(event.data) as SystemStats); }
      catch { /* parse error */ }
    },
    [setStats]
  );

  const { status: wsStatus } = useWebSocket({ url: '/ws/stats', onMessage: onStatsMessage });

  const cameras = stats?.cameras ? Object.entries(stats.cameras) : [];

  const getFpsColor = (fps: number) =>
    fps >= 20 ? 'bg-green-500' : fps >= 10 ? 'bg-yellow-500' : 'bg-red-500';

  const getFpsTextColor = (fps: number) =>
    fps >= 20 ? 'text-green-400' : fps >= 10 ? 'text-yellow-400' : 'text-red-400';

  const getFpsLabel = (fps: number) =>
    fps >= 20 ? t('health.fps_good') : fps >= 10 ? t('health.fps_medium') : t('health.fps_low');

  const currentHour = new Date().getHours();
  const isNightTime = currentHour >= 21 || currentHour < 6;

  const wsLabel =
    wsStatus === 'connected'    ? t('health.ws_connected')    :
    wsStatus === 'connecting'   ? t('health.ws_connecting')   :
                                  t('health.ws_disconnected');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Monitor className="w-6 h-6 text-blue-400" />
          <h2 className="text-xl font-bold">{t('health.title')}</h2>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${wsStatus === 'connected' ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-xs text-gray-500">{wsLabel}</span>
        </div>
      </div>

      {/* Camera cards */}
      {cameras.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <Camera className="w-12 h-12 mx-auto mb-3 text-gray-700" />
          <p className="text-sm">{t('health.no_cameras')}</p>
          <p className="text-xs text-gray-600 mt-1">{t('health.waiting_ws')}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {cameras.map(([id, cam]) => {
            const fps = cam.fps ?? 0;
            const fpsPercent = Math.min((fps / 30) * 100, 100);
            return (
              <div key={id} className="bg-gray-900 rounded-lg border border-gray-800 p-5 hover:border-gray-700 transition-colors">
                {/* Card header */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${cam.connected ? 'bg-green-900/30' : 'bg-red-900/30'}`}>
                      <Camera className={`w-5 h-5 ${cam.connected ? 'text-green-400' : 'text-red-400'}`} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-sm text-white">{cam.name}</h3>
                      <p className="text-xs text-gray-500">ID: {id}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className={`w-2.5 h-2.5 rounded-full ${cam.connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                    <span className={`text-xs font-medium ${cam.connected ? 'text-green-400' : 'text-red-400'}`}>
                      {cam.connected ? t('health.online') : t('health.offline')}
                    </span>
                  </div>
                </div>

                {/* FPS bar */}
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-1.5">
                      <Activity className="w-3.5 h-3.5 text-gray-500" />
                      <span className="text-xs text-gray-400">{t('health.fps_label')}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-mono font-bold ${getFpsTextColor(fps)}`}>
                        {fps.toFixed(1)} FPS
                      </span>
                      <span className={`text-xs px-1.5 py-0.5 rounded ${
                        fps >= 20 ? 'bg-green-900/40 text-green-400' :
                        fps >= 10 ? 'bg-yellow-900/40 text-yellow-400' :
                                    'bg-red-900/40 text-red-400'
                      }`}>
                        {getFpsLabel(fps)}
                      </span>
                    </div>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2.5 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${getFpsColor(fps)}`}
                      style={{ width: `${fpsPercent}%` }}
                    />
                  </div>
                  <div className="flex justify-between mt-1 text-xs text-gray-600">
                    <span>0</span><span>10</span><span>20</span><span>30</span>
                  </div>
                </div>

                {/* Connection + night mode */}
                <div className="space-y-2 border-t border-gray-800 pt-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {cam.connected
                        ? <Wifi className="w-3.5 h-3.5 text-green-400" />
                        : <WifiOff className="w-3.5 h-3.5 text-red-400" />}
                      <span className="text-xs text-gray-400">{t('health.connection')}</span>
                    </div>
                    <span className={`text-xs font-medium ${cam.connected ? 'text-green-400' : 'text-red-400'}`}>
                      {cam.connected ? t('health.stable') : t('health.no_signal')}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Moon className="w-3.5 h-3.5 text-gray-500" />
                      <span className="text-xs text-gray-400">{t('health.night_mode')}</span>
                    </div>
                    <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                      isNightTime ? 'bg-purple-900/40 text-purple-400' : 'bg-gray-800 text-gray-500'
                    }`}>
                      {isNightTime ? t('health.night_active') : t('health.night_off')}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* System summary */}
      {stats && (
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-5">
          <h3 className="text-sm font-semibold text-gray-400 mb-3">{t('health.system_resources')}</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-gray-500 mb-0.5">CPU</p>
              <p className="text-lg font-bold text-yellow-400">{stats.cpu ?? 0}%</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 mb-0.5">RAM</p>
              <p className="text-lg font-bold text-blue-400">{stats.ram ?? 0} GB</p>
            </div>
            {stats.gpu !== undefined && (
              <div>
                <p className="text-xs text-gray-500 mb-0.5">GPU</p>
                <p className="text-lg font-bold text-green-400">{stats.gpu}%</p>
              </div>
            )}
            {stats.vram !== undefined && (
              <div>
                <p className="text-xs text-gray-500 mb-0.5">VRAM</p>
                <p className="text-lg font-bold text-purple-400">{stats.vram} GB</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
