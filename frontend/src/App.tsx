import { useState, useEffect } from 'react';
import { useStore } from './store/useStore';
import { useTranslation } from './i18n/useTranslation';
import type { Lang } from './i18n/translations';
import VideoGrid from './components/VideoGrid';
import AlarmPanel from './components/AlarmPanel';
import AlarmSearch from './components/AlarmSearch';
import ZoneEditor from './components/ZoneEditor';
import StatsChart from './components/StatsChart';
import Settings from './components/Settings';
import LogViewer from './components/LogViewer';

export default function App() {
  const activeTab = useStore((s) => s.activeTab);
  const setActiveTab = useStore((s) => s.setActiveTab);
  const language = useStore((s) => s.language);
  const setLanguage = useStore((s) => s.setLanguage);
  const alarms = useStore((s) => s.alarms);
  const activeAlarmCount = alarms.filter((a) => a.status === 'active').length;

  const { t } = useTranslation();

  const TABS = [
    { key: 'live' as const,     label: t('nav.live') },
    { key: 'alarms' as const,   label: t('nav.alarms') },
    { key: 'zones' as const,    label: t('nav.zones') },
    { key: 'stats' as const,    label: t('nav.stats') },
    { key: 'settings' as const, label: t('nav.settings') },
    { key: 'logs' as const,     label: t('nav.logs') },
  ];

  const LANGS: { code: Lang; flag: string }[] = [
    { code: 'ru', flag: '🇷🇺' },
    { code: 'kk', flag: '🇰🇿' },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-4 py-3">
        <div className="max-w-[1920px] mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold tracking-tight">
              <span className="text-blue-500">ParkGuard</span>{' '}
              <span className="text-gray-400">KZ</span>
            </h1>
            <span className="text-xs bg-gray-800 px-2 py-0.5 rounded text-gray-400">
              v2.0
            </span>
          </div>

          {/* Navigation tabs */}
          <nav className="flex gap-1">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab.key
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                {tab.label}
                {tab.key === 'alarms' && activeAlarmCount > 0 && (
                  <span className="ml-2 bg-red-600 text-white text-xs px-1.5 py-0.5 rounded-full">
                    {activeAlarmCount}
                  </span>
                )}
              </button>
            ))}
          </nav>

          {/* Dil seçici + Saat */}
          <div className="flex items-center gap-4">
            {/* Dil butonları */}
            <div className="flex gap-1">
              {LANGS.map(({ code, flag }) => (
                <button
                  key={code}
                  onClick={() => setLanguage(code)}
                  title={code.toUpperCase()}
                  className={`text-lg px-2 py-1 rounded transition-all ${
                    language === code
                      ? 'bg-gray-700 ring-1 ring-blue-500'
                      : 'opacity-50 hover:opacity-100 hover:bg-gray-800'
                  }`}
                >
                  {flag}
                </button>
              ))}
            </div>

            <Clock />
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-[1920px] mx-auto p-4">
        {activeTab === 'live' && (
          <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
            <div className="xl:col-span-3">
              <VideoGrid />
            </div>
            <div className="xl:col-span-1">
              <AlarmPanel />
            </div>
          </div>
        )}

        {activeTab === 'alarms' && <AlarmSearch />}

        {activeTab === 'zones' && <ZoneEditor />}

        {activeTab === 'stats' && <StatsChart />}

        {activeTab === 'settings' && <Settings />}

        {activeTab === 'logs' && <LogViewer />}
      </main>
    </div>
  );
}

function Clock() {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const time = now.toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
  const date = now.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });

  return (
    <div className="text-right text-xs text-gray-400">
      <div className="font-mono text-sm text-gray-300">{time}</div>
      <div>{date}</div>
    </div>
  );
}
