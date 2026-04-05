import { useEffect, useCallback } from 'react';
import { useStore } from '../store/useStore';
import { useWebSocket } from '../hooks/useWebSocket';
import { useTranslation } from '../i18n/useTranslation';
import PlateCard from './PlateCard';
import type { Alarm } from '../types';

const API_BASE = '/api';

export default function AlarmPanel() {
  const alarms = useStore((s) => s.alarms);
  const addAlarm = useStore((s) => s.addAlarm);
  const setAlarms = useStore((s) => s.setAlarms);
  const setAlarmWsStatus = useStore((s) => s.setAlarmWsStatus);
  const soundEnabled = useStore((s) => s.soundEnabled);
  const toggleSound = useStore((s) => s.toggleSound);
  const { t } = useTranslation();

  useEffect(() => {
    fetch(`${API_BASE}/alarms?limit=50`)
      .then((r) => r.json())
      .then((data) => {
        if (data.alarms) setAlarms(data.alarms);
      })
      .catch(() => {});
  }, [setAlarms]);

  const onAlarmMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const alarm: Alarm = JSON.parse(event.data);
        addAlarm(alarm);

        if (soundEnabled) {
          const audio = new Audio(
            'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQ=='
          );
          audio.volume = 0.3;
          audio.play().catch(() => {});
        }
      } catch {
        // parse hatası
      }
    },
    [addAlarm, soundEnabled]
  );

  const onOpen = useCallback(() => setAlarmWsStatus('connected'), [setAlarmWsStatus]);
  const onClose = useCallback(() => setAlarmWsStatus('disconnected'), [setAlarmWsStatus]);

  const { status: wsStatus } = useWebSocket({
    url: '/ws/alarms',
    onMessage: onAlarmMessage,
    onOpen,
    onClose,
  });

  const activeAlarms = alarms.filter((a) => a.status === 'active');
  const resolvedAlarms = alarms.filter((a) => a.status === 'resolved');

  return (
    <div className="bg-gray-900 rounded-lg p-4 h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-bold">{t('alarms.title')}</h2>
          <span
            className={`w-2 h-2 rounded-full ${
              wsStatus === 'connected' ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          {activeAlarms.length > 0 && (
            <span className="bg-red-600 text-white text-xs px-2 py-0.5 rounded-full font-bold animate-pulse">
              {activeAlarms.length}
            </span>
          )}
        </div>
        <button
          onClick={toggleSound}
          className="text-gray-400 hover:text-white text-sm px-2 py-1 rounded hover:bg-gray-800"
        >
          {soundEnabled ? t('alarms.sound_on') : t('alarms.sound_off')}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {alarms.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p className="text-3xl mb-2">---</p>
            <p className="text-sm">{t('alarms.empty')}</p>
          </div>
        ) : (
          <>
            {activeAlarms.map((alarm) => (
              <PlateCard key={alarm.id} alarm={alarm} />
            ))}

            {resolvedAlarms.length > 0 && (
              <div className="border-t border-gray-700 pt-3 mt-3">
                <p className="text-xs text-gray-500 mb-2">
                  {t('alarms.resolved_section')} ({resolvedAlarms.length})
                </p>
                {resolvedAlarms.slice(0, 10).map((alarm) => (
                  <PlateCard key={alarm.id} alarm={alarm} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
