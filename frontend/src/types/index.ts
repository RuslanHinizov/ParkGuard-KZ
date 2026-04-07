// === KAMERA ===
export interface Camera {
  id: number;
  name: string;
  connected: boolean;
  fps: number;
}

// === ALARM ===
export interface Alarm {
  id: string;
  camera_id: number;
  track_id: number;
  plate: string | null;
  plate_conf: number | null;
  vehicle_class: string;
  zone_id: string;
  zone_name: string;
  duration_sec: number;
  status: 'active' | 'resolved';
  screenshot: string;
  created_at: string;
  resolved_at: string | null;
}

// === ZONE (Yasak Park Bölgesi) ===
export interface Zone {
  id: string;
  camera_id: number;
  name: string;
  polygon: number[][];
  color: string;
  active: boolean;
}

export interface ZoneCreate {
  camera_id: number;
  name: string;
  polygon: number[][];
  color: string;
}

// === DETECTION ===
export interface Detection {
  camera_id: number;
  bbox: number[];
  confidence: number;
  class_id: number;
  class_name: string;
  track_id: number;
  plate: string | null;
  in_violation: boolean;
}

// === SİSTEM İSTATİSTİKLERİ ===
export interface SystemStats {
  fps: Record<number, number>;
  cpu: number;
  ram: number;
  gpu?: number;
  vram?: number;
  cameras: Record<number, CameraStatus>;
}

export interface CameraStatus {
  name: string;
  connected: boolean;
  fps: number;
}

// === BUGÜN İSTATİSTİKLERİ ===
export interface TodayStats {
  total_alarms: number;
  active: number;
  resolved: number;
  by_camera: Record<number, number>;
}

// === SAATLİK İSTATİSTİK ===
export interface HourlyStat {
  hour: number;
  count: number;
}

// === KAMERA İSTATİSTİĞİ ===
export interface CameraStat {
  camera_id: number;
  name: string;
  alarm_count: number;
  last_alarm: string;
}

// === SYSTEM HEALTH ===
export interface SystemHealth {
  cpu_percent: number;
  ram_used_gb: number;
  ram_total_gb: number;
  ram_percent: number;
  gpu_name?: string;
  vram_used_gb?: number;
  vram_total_gb?: number;
  gpu_available: boolean;
  cameras: Record<number, CameraStatus>;
}

// === CEZA (PENALTY) ===
export interface Penalty {
  id: string;
  alarm_id: string;
  plate: string;
  camera_id: number | null;
  zone_name: string;
  duration_sec: number;
  screenshot: string;
  status: 'pending' | 'sent' | 'cancelled';
  fine_amount: number;
  created_at: string;
  sent_at: string | null;
  notes: string;
}

export interface PenaltyStats {
  pending:   { count: number; total_amount: number };
  sent:      { count: number; total_amount: number };
  cancelled: { count: number; total_amount: number };
}

// === WS Bağlantı Durumu ===
export type WSStatus = 'connecting' | 'connected' | 'disconnected';
