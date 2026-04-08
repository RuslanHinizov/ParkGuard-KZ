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
  plate_screenshot?: string | null;
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
  track_id: number | null;
  plate: string | null;
  plate_conf?: number | null;
  in_violation: boolean;
}

export type VideoSourceMode = 'file' | 'webrtc' | 'hls';

export interface CameraStreamSource {
  camera_id: number;
  mode: VideoSourceMode;
  fallback_mode: VideoSourceMode | null;
  label: string;
  file_url: string | null;
  hls_url: string | null;
  whep_url: string | null;
  rtsp_url: string | null;
  metadata_ws_url: string;
}

export interface StreamMetadata {
  camera_id: number;
  frame_width: number;
  frame_height: number;
  timestamp_ms: number;
  detections: Detection[];
  zones: Zone[];
}

// === SİSTEM İSTATİSTİKLERİ ===
export interface SystemStats {
  fps: Record<number, number>;
  cpu: number;
  ram: number;
  gpu?: number;
  gpu_memory?: number;
  gpu_name?: string;
  vram_used?: number;
  vram_total?: number;
  cameras: Record<number, CameraStatus>;
}

export interface CameraStatus {
  name: string;
  connected: boolean;
  fps: number;
}

// === SYSTEM HEALTH ===
export interface SystemHealth {
  cpu_percent: number;
  gpu_percent?: number;
  gpu_memory_percent?: number;
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
