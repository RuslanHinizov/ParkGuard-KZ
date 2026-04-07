import { create } from 'zustand';
import type { Alarm, Zone, SystemStats, TodayStats, WSStatus } from '../types';
import type { Lang } from '../i18n/translations';

// Dil tercihini localStorage'dan oku (varsayılan: Rusça)
function getSavedLang(): Lang {
  try {
    const saved = localStorage.getItem('korgen_lang');
    if (saved === 'ru' || saved === 'kk' || saved === 'en') return saved;
  } catch {
    // localStorage erişim hatası
  }
  return 'ru';
}

interface AppState {
  // Alarmlar
  alarms: Alarm[];
  addAlarm: (alarm: Alarm) => void;
  setAlarms: (alarms: Alarm[]) => void;
  resolveAlarm: (id: string) => void;
  removeAlarm: (id: string) => void;

  // Zoneler
  zones: Zone[];
  setZones: (zones: Zone[]) => void;
  addZone: (zone: Zone) => void;
  removeZone: (id: string) => void;
  updateZone: (id: string, updates: Partial<Zone>) => void;

  // Sistem
  stats: SystemStats | null;
  setStats: (stats: SystemStats) => void;

  todayStats: TodayStats | null;
  setTodayStats: (stats: TodayStats) => void;

  // WebSocket durumları
  streamStatus: Record<number, WSStatus>;
  setStreamStatus: (camId: number, status: WSStatus) => void;
  alarmWsStatus: WSStatus;
  setAlarmWsStatus: (status: WSStatus) => void;

  // Aktif kamera (tam ekran)
  activeCameraId: number | null;
  setActiveCameraId: (id: number | null) => void;

  // Ses
  soundEnabled: boolean;
  toggleSound: () => void;

  // Seçili sekme
  activeTab: 'live' | 'alarms' | 'zones' | 'stats' | 'settings' | 'logs' | 'chat' | 'plates' | 'gallery' | 'reports' | 'penalties';
  setActiveTab: (tab: 'live' | 'alarms' | 'zones' | 'stats' | 'settings' | 'logs' | 'chat' | 'plates' | 'gallery' | 'reports' | 'penalties') => void;
  selectedPlateQuery: string;
  setSelectedPlateQuery: (plate: string) => void;

  // Dil
  language: Lang;
  setLanguage: (lang: Lang) => void;
}

export const useStore = create<AppState>((set) => ({
  // Alarmlar
  alarms: [],
  addAlarm: (alarm) =>
    set((state) => ({
      alarms: [alarm, ...state.alarms].slice(0, 200),
    })),
  setAlarms: (alarms) => set({ alarms }),
  resolveAlarm: (id) =>
    set((state) => ({
      alarms: state.alarms.map((a) =>
        a.id === id ? { ...a, status: 'resolved' as const, resolved_at: new Date().toISOString() } : a
      ),
    })),
  removeAlarm: (id) =>
    set((state) => ({
      alarms: state.alarms.filter((a) => a.id !== id),
    })),

  // Zoneler
  zones: [],
  setZones: (zones) => set({ zones }),
  addZone: (zone) => set((state) => ({ zones: [...state.zones, zone] })),
  removeZone: (id) =>
    set((state) => ({ zones: state.zones.filter((z) => z.id !== id) })),
  updateZone: (id, updates) =>
    set((state) => ({
      zones: state.zones.map((z) => (z.id === id ? { ...z, ...updates } : z)),
    })),

  // Sistem
  stats: null,
  setStats: (stats) => set({ stats }),

  todayStats: null,
  setTodayStats: (stats) => set({ todayStats: stats }),

  // WebSocket
  streamStatus: {},
  setStreamStatus: (camId, status) =>
    set((state) => ({
      streamStatus: { ...state.streamStatus, [camId]: status },
    })),
  alarmWsStatus: 'disconnected',
  setAlarmWsStatus: (status) => set({ alarmWsStatus: status }),

  // Aktif kamera
  activeCameraId: null,
  setActiveCameraId: (id) => set({ activeCameraId: id }),

  // Ses
  soundEnabled: true,
  toggleSound: () => set((state) => ({ soundEnabled: !state.soundEnabled })),

  // Tab
  activeTab: 'live',
  setActiveTab: (tab) => set({ activeTab: tab }),
  selectedPlateQuery: '',
  setSelectedPlateQuery: (plate) => set({ selectedPlateQuery: plate }),

  // Dil — localStorage'dan yükle, değişince kaydet
  language: getSavedLang(),
  setLanguage: (lang) => {
    try {
      localStorage.setItem('korgen_lang', lang);
    } catch {
      // localStorage erişim hatası
    }
    set({ language: lang });
  },
}));
