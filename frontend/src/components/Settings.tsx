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
      // hata
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
    <div className="max-w-2xl mx-auto space-y-4">
      <h2 className="text-xl font-bold">{t('settings.title')}</h2>

      {CAMERA_IDS.map((camId) => (
        <div key={camId} className="bg-gray-900 rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-base">
              {t('settings.camera_section')} {camId} — {t(`camera.${camId}` as Parameters<typeof t>[0])}
            </h3>
            <button
              onClick={() => handleSave(camId)}
              className={`px-4 py-1.5 rounded text-sm font-medium transition-all ${
                saved[camId]
                  ? 'bg-green-700 text-green-200'
                  : 'bg-blue-600 hover:bg-blue-500 text-white'
              }`}
            >
              {saved[camId] ? t('settings.saved') : t('settings.save')}
            </button>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">{t('settings.violation_duration')}</span>
              <span className="font-mono text-blue-400 font-semibold">
                {formatDuration(durations[camId] ?? 300)}
              </span>
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

            <div className="flex justify-between text-xs text-gray-600">
              <span>30 {t('settings.seconds')}</span>
              <span>30 {t('settings.minutes')}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
