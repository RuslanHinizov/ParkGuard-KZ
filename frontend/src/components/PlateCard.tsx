import { useState } from 'react';
import { useStore } from '../store/useStore';
import { useTranslation } from '../i18n/useTranslation';
import type { Alarm } from '../types';

const API_BASE = '/api';

function timeAgo(dateStr: string, minutesAgo: string, hoursAgo: string, daysAgo: string, justNow: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return justNow;
  if (mins < 60) return `${mins} ${minutesAgo}`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} ${hoursAgo}`;
  return `${Math.floor(hours / 24)} ${daysAgo}`;
}

interface PlateCardProps {
  alarm: Alarm;
}

export default function PlateCard({ alarm }: PlateCardProps) {
  const resolveAlarm = useStore((s) => s.resolveAlarm);
  const removeAlarm = useStore((s) => s.removeAlarm);
  const { t } = useTranslation();
  const [showScreenshot, setShowScreenshot] = useState(false);
  const [loading, setLoading] = useState(false);

  const isActive = alarm.status === 'active';

  const ago = timeAgo(
    alarm.created_at,
    t('plate.minutes_ago'),
    t('plate.hours_ago'),
    t('plate.days_ago'),
    t('plate.just_now'),
  );

  const handleResolve = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/alarms/${alarm.id}/resolve`, {
        method: 'PUT',
      });
      if (res.ok) resolveAlarm(alarm.id);
    } catch {
      // hata
    }
    setLoading(false);
  };

  const handleDelete = async () => {
    try {
      const res = await fetch(`${API_BASE}/alarms/${alarm.id}`, { method: 'DELETE' });
      if (res.ok) removeAlarm(alarm.id);
    } catch {
      // hata
    }
  };

  return (
    <div
      className={`rounded-lg p-3 border transition-all ${
        isActive
          ? 'bg-red-950/40 border-red-500/50 alarm-blink'
          : 'bg-gray-800/50 border-gray-700 opacity-60'
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <div>
          <div className="text-lg font-bold font-mono tracking-wider">
            {alarm.plate ?? t('plate.no_plate')}
          </div>
          {alarm.plate_conf && (
            <span className="text-xs text-gray-400">
              {t('plate.confidence')} {(alarm.plate_conf * 100).toFixed(0)}%
            </span>
          )}
        </div>
        <div className="text-right text-xs text-gray-400">
          <div>{ago}</div>
          <div className="mt-1">{alarm.duration_sec} {t('plate.in_zone')}</div>
        </div>
      </div>

      <div className="flex items-center gap-2 text-xs text-gray-400 mb-2">
        <span className="bg-gray-700 px-1.5 py-0.5 rounded">
          {t(`camera.${alarm.camera_id}` as Parameters<typeof t>[0])}
        </span>
        <span className="bg-gray-700 px-1.5 py-0.5 rounded">{alarm.zone_name}</span>
        <span className="bg-gray-700 px-1.5 py-0.5 rounded capitalize">{alarm.vehicle_class}</span>
      </div>

      {showScreenshot && (
        <div className="mb-2">
          <img
            src={`${API_BASE}/alarms/${alarm.id}/screenshot`}
            alt="screenshot"
            className="w-full rounded border border-gray-700"
          />
        </div>
      )}

      <div className="flex items-center gap-2">
        <button
          onClick={() => setShowScreenshot(!showScreenshot)}
          className="text-xs px-2 py-1 rounded bg-gray-700 hover:bg-gray-600 text-gray-300"
        >
          {showScreenshot ? t('plate.hide_image') : t('plate.show_image')}
        </button>

        {isActive && (
          <button
            onClick={handleResolve}
            disabled={loading}
            className="text-xs px-2 py-1 rounded bg-green-700 hover:bg-green-600 text-white disabled:opacity-50"
          >
            {loading ? '...' : t('plate.resolve')}
          </button>
        )}

        <button
          onClick={handleDelete}
          className="text-xs px-2 py-1 rounded bg-gray-700 hover:bg-red-700 text-gray-400 hover:text-white ml-auto"
        >
          {t('plate.delete')}
        </button>
      </div>
    </div>
  );
}
