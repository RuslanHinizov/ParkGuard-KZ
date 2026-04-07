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
import ChatPanel from './components/ChatPanel';
import PlateHistory from './components/PlateHistory';
import GalleryPanel from './components/GalleryPanel';
import ReportPanel from './components/ReportPanel';
import WhitelistPanel from './components/WhitelistPanel';
import CameraHealth from './components/CameraHealth';
import QuickSearch from './components/QuickSearch';
import AnomalyBadge from './components/AnomalyBadge';
import PenaltyPanel from './components/PenaltyPanel';

export default function App() {
  const activeTab = useStore((s) => s.activeTab);
  const setActiveTab = useStore((s) => s.setActiveTab);
  const setSelectedPlateQuery = useStore((s) => s.setSelectedPlateQuery);
  const language = useStore((s) => s.language);
  const setLanguage = useStore((s) => s.setLanguage);
  const alarms = useStore((s) => s.alarms);
  const activeAlarmCount = alarms.filter((a) => a.status === 'active').length;

  const { t } = useTranslation();

  const TABS = [
    { key: 'live' as const,     label: t('nav.live') },
    { key: 'alarms' as const,   label: t('nav.alarms') },
    { key: 'plates' as const,   label: t('nav.plates') },
    { key: 'gallery' as const,  label: t('nav.gallery') },
    { key: 'zones' as const,    label: t('nav.zones') },
    { key: 'stats' as const,    label: t('nav.stats') },
    { key: 'reports' as const,   label: t('nav.reports') },
    { key: 'penalties' as const, label: t('nav.penalties') },
    { key: 'settings' as const,  label: t('nav.settings') },
    { key: 'logs' as const,      label: t('nav.logs') },
    { key: 'chat' as const,      label: t('nav.chat') },
  ];

  const LANGS: { code: Lang; flag: string }[] = [
    { code: 'ru', flag: '🇷🇺' },
    { code: 'kk', flag: '🇰🇿' },
    { code: 'en', flag: '🇬🇧' },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-4 py-3">
        <div className="max-w-[1920px] mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Korgen Vision Logo */}
            <img src="/korgen-icon.svg" alt="Korgen Vision" className="w-9 h-9" />
            <div>
              <h1 className="text-lg font-bold tracking-widest leading-none">
                <span className="text-blue-400">KORGEN</span>{' '}
                <span className="text-white">VISION</span>
              </h1>
              <p className="text-[10px] text-gray-500 tracking-wider leading-none mt-0.5">
                МОНИТОРИНГ ПАРКОВОК
              </p>
            </div>
            <span className="text-xs bg-blue-950 border border-blue-800 px-2 py-0.5 rounded text-blue-400">
              v1.0
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

          {/* Arama + Anomali + Dil + Saat */}
          <div className="flex items-center gap-4">
            <QuickSearch
              onNavigate={(plate) => {
                setSelectedPlateQuery(plate);
                setActiveTab('plates');
              }}
            />
            <AnomalyBadge />
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

        {activeTab === 'plates' && <PlateHistory />}

        {activeTab === 'gallery' && <GalleryPanel />}

        {activeTab === 'reports' && <ReportPanel />}

        {activeTab === 'penalties' && <PenaltyPanel />}

        {activeTab === 'settings' && (
          <div className="space-y-6">
            <Settings />
            <CameraHealth />
            <WhitelistPanel />
          </div>
        )}

        {activeTab === 'logs' && <LogViewer />}

        {activeTab === 'chat' && <ChatPanel />}
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
