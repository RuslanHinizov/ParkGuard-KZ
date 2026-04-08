import { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';
import { useTranslation } from '../i18n/useTranslation';
import type { Alarm, Penalty } from '../types';

const API_BASE = '/api';

function timeAgo(
  dateStr: string,
  minutesAgo: string,
  hoursAgo: string,
  daysAgo: string,
  justNow: string
): string {
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

const PENALTY_CLS: Record<string, string> = {
  pending: 'bg-yellow-900/60 text-yellow-300 border-yellow-700',
  sent: 'bg-green-900/60  text-green-300  border-green-700',
  cancelled: 'bg-gray-700/60   text-gray-400   border-gray-600',
};

export default function PlateCard({ alarm }: PlateCardProps) {
  const resolveAlarm = useStore((s) => s.resolveAlarm);
  const removeAlarm = useStore((s) => s.removeAlarm);
  const { t } = useTranslation();

  const [showScreenshot, setShowScreenshot] = useState(false);
  const [loading, setLoading] = useState(false);
  const [penalty, setPenalty] = useState<Penalty | null>(null);
  const [sendingFine, setSendingFine] = useState(false);

  useEffect(() => {
    if (!alarm.plate) {
      setPenalty(null);
      return;
    }

    fetch(`${API_BASE}/penalties?limit=1&alarm_id=${encodeURIComponent(alarm.id)}`)
      .then((res) => res.json())
      .then((data) => {
        setPenalty((data.penalties as Penalty[])[0] ?? null);
      })
      .catch(() => setPenalty(null));
  }, [alarm.id, alarm.plate]);

  const handleSendFine = async () => {
    if (!penalty) return;

    setSendingFine(true);
    try {
      const res = await fetch(`${API_BASE}/penalties/${penalty.id}/send`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setPenalty((prev) =>
          prev ? { ...prev, status: 'sent', sent_at: data.sent_at ?? prev.sent_at } : prev
        );
      }
    } catch {
      // noop
    }
    setSendingFine(false);
  };

  const handleCancelFine = async () => {
    if (!penalty) return;

    try {
      const res = await fetch(`${API_BASE}/penalties/${penalty.id}/cancel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'Operator cancel' }),
      });
      if (res.ok) {
        setPenalty((prev) => (prev ? { ...prev, status: 'cancelled' } : prev));
      }
    } catch {
      // noop
    }
  };

  const isActive = alarm.status === 'active';

  const ago = timeAgo(
    alarm.created_at,
    t('plate.minutes_ago'),
    t('plate.hours_ago'),
    t('plate.days_ago'),
    t('plate.just_now')
  );

  const handleResolve = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/alarms/${alarm.id}/resolve`, {
        method: 'PUT',
      });
      if (res.ok) {
        resolveAlarm(alarm.id);
      }
    } catch {
      // noop
    }
    setLoading(false);
  };

  const handleDelete = async () => {
    try {
      const res = await fetch(`${API_BASE}/alarms/${alarm.id}`, { method: 'DELETE' });
      if (res.ok) {
        removeAlarm(alarm.id);
      }
    } catch {
      // noop
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
          <div className="mt-1">
            {alarm.duration_sec} {t('plate.in_zone')}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 text-xs text-gray-400 mb-2">
        <span className="bg-gray-700 px-1.5 py-0.5 rounded">
          {t(`camera.${alarm.camera_id}` as Parameters<typeof t>[0])}
        </span>
        <span className="bg-gray-700 px-1.5 py-0.5 rounded">{alarm.zone_name}</span>
        <span className="bg-gray-700 px-1.5 py-0.5 rounded capitalize">
          {alarm.vehicle_class}
        </span>
      </div>

      {showScreenshot && (
        <div className="mb-2 grid grid-cols-1 md:grid-cols-2 gap-2">
          <div>
            <div className="text-[11px] uppercase tracking-wide text-gray-400 mb-1">
              Vehicle
            </div>
            <img
              src={`${API_BASE}/alarms/${alarm.id}/screenshot`}
              alt="vehicle screenshot"
              className="w-full rounded border border-gray-700"
            />
          </div>

          <div>
            <div className="text-[11px] uppercase tracking-wide text-gray-400 mb-1">
              Plate
            </div>
            {alarm.plate_screenshot ? (
              <img
                src={`${API_BASE}/alarms/${alarm.id}/plate-screenshot`}
                alt="plate screenshot"
                className="w-full rounded border border-gray-700 bg-gray-950"
              />
            ) : (
              <div className="w-full h-full min-h-24 rounded border border-dashed border-gray-700 bg-gray-900/60 text-xs text-gray-500 flex items-center justify-center">
                Plate crop unavailable
              </div>
            )}
          </div>
        </div>
      )}

      {penalty && (
        <div
          className={`flex items-center justify-between rounded px-2 py-1 mb-2 border text-xs ${PENALTY_CLS[penalty.status] ?? ''}`}
        >
          <span className="font-medium">
            {penalty.status === 'pending'
              ? t('penalty.status_pending')
              : penalty.status === 'sent'
                ? t('penalty.status_sent')
                : penalty.status === 'cancelled'
                  ? t('penalty.status_cancelled')
                  : penalty.status}
          </span>
          <span className="font-mono font-bold">
            {penalty.fine_amount.toLocaleString('ru-RU')} ₸
          </span>
        </div>
      )}

      <div className="flex items-center gap-2 flex-wrap">
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

        {penalty?.status === 'pending' && (
          <>
            <button
              onClick={handleSendFine}
              disabled={sendingFine}
              className="text-xs px-2 py-1 rounded bg-orange-700 hover:bg-orange-600 text-white disabled:opacity-50 font-medium"
            >
              {sendingFine ? '...' : t('penalty.btn_send_fine')}
            </button>
            <button
              onClick={handleCancelFine}
              className="text-xs px-2 py-1 rounded bg-gray-700 hover:bg-gray-600 text-gray-400 hover:text-white"
            >
              {t('penalty.btn_cancel')}
            </button>
          </>
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
