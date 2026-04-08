import { useState, useEffect } from 'react';
import { useTranslation } from '../i18n/useTranslation';

const API_BASE = '/api';

const CAMERA_IDS = [1, 2, 3];

export default function Settings() {
  const { t } = useTranslation();

  const [durations, setDurations] = useState<Record<number, number>>({
    1: 300, 2: 300, 3: 300,
  });
  const [saved, setSaved] = useState<Record<number, boolean>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/settings`)
      .then((r) => r.json())
      .then((data) => {
        if (data?.cameras) {
          const d: Record<number, number> = {};
          for (const [id, cam] of Object.entries(data.cameras)) {
            d[Number(id)] = (cam as { violation_duration: number }).violation_duration;
          }
          setDurations(d);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async (cameraId: number) => {
    try {
      const res = await fetch(`${API_BASE}/settings/camera/${cameraId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ violation_duration: durations[cameraId] }),
      });
      if (res.ok) {
        setSaved((prev) => ({ ...prev, [cameraId]: true }));
        setTimeout(() => setSaved((prev) => ({ ...prev, [cameraId]: false })), 2000);
      }
    } catch {
      // noop
    }
  };

  const formatDuration = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    if (s === 0) return `${m} ${t('settings.minutes')}`;
    return `${m} ${t('settings.minutes')} ${s} ${t('settings.seconds')}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-500">
        {t('stats.loading')}
      </div>
    );
  }

  return (
    <section className="space-y-4">
      <div className="flex items-end justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold">{t('settings.title')}</h2>
          <p className="text-sm text-gray-500 mt-1">
            {CAMERA_IDS.length} {t('settings.camera_section').toLowerCase()}
          </p>
        </div>
        <div className="hidden xl:flex items-center gap-2 text-xs text-gray-500">
          <span className="w-2 h-2 rounded-full bg-blue-500" />
          <span>{t('settings.violation_duration')}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {CAMERA_IDS.map((camId) => (
          <div
            key={camId}
            className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-[0_0_0_1px_rgba(255,255,255,0.02)]"
          >
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <h3 className="font-semibold text-base">
                  {t('settings.camera_section')} {camId} - {t(`camera.${camId}` as Parameters<typeof t>[0])}
                </h3>
                <p className="text-xs text-gray-500 mt-1">ID: {camId}</p>
              </div>
              <button
                onClick={() => handleSave(camId)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                  saved[camId]
                    ? 'bg-green-700 text-green-200'
                    : 'bg-blue-600 hover:bg-blue-500 text-white'
                }`}
              >
                {saved[camId] ? t('settings.saved') : t('settings.save')}
              </button>
            </div>

            <div className="space-y-4">
              <div className="rounded-lg border border-gray-800 bg-gray-950/60 p-3">
                <div className="flex items-center justify-between text-sm gap-4">
                  <span className="text-gray-400">{t('settings.violation_duration')}</span>
                  <span className="font-mono text-blue-400 font-semibold text-right">
                    {formatDuration(durations[camId] ?? 300)}
                  </span>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between text-xs text-gray-500">
                  <span>30 {t('settings.seconds')}</span>
                  <span>30 {t('settings.minutes')}</span>
                </div>
                <input
                  type="range"
                  min={30}
                  max={1800}
                  step={30}
                  value={durations[camId] ?? 300}
                  onChange={(e) =>
                    setDurations((prev) => ({ ...prev, [camId]: Number(e.target.value) }))
                  }
                  className="w-full accent-blue-500"
                />
                <div className="grid grid-cols-3 gap-2 text-[11px] text-gray-500">
                  <div className="rounded-md bg-gray-800/80 px-2 py-1 text-center">30s</div>
                  <div className="rounded-md bg-gray-800/80 px-2 py-1 text-center">5m</div>
                  <div className="rounded-md bg-gray-800/80 px-2 py-1 text-center">30m</div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
