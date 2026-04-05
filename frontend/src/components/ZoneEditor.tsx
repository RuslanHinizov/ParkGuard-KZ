import { useState, useRef, useEffect, useCallback } from 'react';
import { useStore } from '../store/useStore';
import { useTranslation } from '../i18n/useTranslation';
import type { Zone, ZoneCreate } from '../types';

const API_BASE = '/api';

const COLORS = [
  '#FF0000', '#FF6600', '#FFCC00', '#00CC00',
  '#0066FF', '#9900CC', '#FF0099', '#00CCCC',
];

const CAMERA_IDS = [1, 2, 3];

export default function ZoneEditor() {
  const zones = useStore((s) => s.zones);
  const setZones = useStore((s) => s.setZones);
  const addZone = useStore((s) => s.addZone);
  const removeZone = useStore((s) => s.removeZone);
  const { t } = useTranslation();

  const [selectedCamera, setSelectedCamera] = useState(1);
  const [points, setPoints] = useState<number[][]>([]);
  const [zoneName, setZoneName] = useState('');
  const [zoneColor, setZoneColor] = useState(COLORS[0]);
  const [snapshotUrl, setSnapshotUrl] = useState<string>('');
  const [drawing, setDrawing] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imgRef = useRef<HTMLImageElement | null>(null);

  // Başlangıçta zoneleri yükle
  useEffect(() => {
    fetch(`${API_BASE}/zones`)
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) setZones(data);
      })
      .catch(() => {});
  }, [setZones]);

  // Kamera snapshot yükle
  useEffect(() => {
    setSnapshotUrl(`${API_BASE}/system/snapshot/${selectedCamera}?t=${Date.now()}`);
  }, [selectedCamera]);

  // Canvas çizimi
  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const img = imgRef.current;
    if (!canvas || !img) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = img.naturalWidth || 960;
    canvas.height = img.naturalHeight || 540;

    // Yüklenmemiş veya hatalı image çizmeye çalışınca Chrome exception fırlatır
    if (img.complete && img.naturalWidth > 0) {
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    }

    // Mevcut zoneleri çiz
    const camZones = zones.filter((z) => z.camera_id === selectedCamera);
    for (const zone of camZones) {
      if (zone.polygon.length < 3) continue;

      const hex = zone.color || '#FF0000';
      const r = parseInt(hex.slice(1, 3), 16);
      const g = parseInt(hex.slice(3, 5), 16);
      const b = parseInt(hex.slice(5, 7), 16);

      ctx.beginPath();
      ctx.moveTo(zone.polygon[0][0], zone.polygon[0][1]);
      for (let i = 1; i < zone.polygon.length; i++) {
        ctx.lineTo(zone.polygon[i][0], zone.polygon[i][1]);
      }
      ctx.closePath();
      ctx.fillStyle = `rgba(${r},${g},${b},0.25)`;
      ctx.fill();
      ctx.strokeStyle = hex;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Zone adı
      const cx = zone.polygon.reduce((s, p) => s + p[0], 0) / zone.polygon.length;
      const cy = zone.polygon.reduce((s, p) => s + p[1], 0) / zone.polygon.length;
      ctx.fillStyle = '#fff';
      ctx.font = '14px sans-serif';
      ctx.fillText(zone.name, cx - 20, cy);
    }

    // Çizim sırasındaki noktalar
    if (points.length > 0) {
      ctx.beginPath();
      ctx.moveTo(points[0][0], points[0][1]);
      for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i][0], points[i][1]);
      }
      ctx.strokeStyle = zoneColor;
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.stroke();
      ctx.setLineDash([]);

      // Noktalar
      for (const pt of points) {
        ctx.beginPath();
        ctx.arc(pt[0], pt[1], 5, 0, Math.PI * 2);
        ctx.fillStyle = zoneColor;
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    }
  }, [zones, selectedCamera, points, zoneColor]);

  useEffect(() => {
    drawCanvas();
  }, [drawCanvas]);

  // Canvas tıklama → nokta ekle
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);

    setPoints((prev) => [...prev, [x, y]]);
    setDrawing(true);
  };

  // Sağ tık → son noktayı geri al
  const handleRightClick = (e: React.MouseEvent) => {
    e.preventDefault();
    setPoints((prev) => prev.slice(0, -1));
    if (points.length <= 1) setDrawing(false);
  };

  // Çift tıklama → polygon kapat
  const handleDoubleClick = () => {
    if (points.length >= 3) {
      // Kaydedilecek
    }
  };

  // Kaydet
  const handleSave = async () => {
    if (points.length < 3 || !zoneName.trim()) return;

    const body: ZoneCreate = {
      camera_id: selectedCamera,
      name: zoneName.trim(),
      polygon: points,
      color: zoneColor,
    };

    try {
      const res = await fetch(`${API_BASE}/zones`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        const zone: Zone = await res.json();
        addZone(zone);
        setPoints([]);
        setZoneName('');
        setDrawing(false);
      }
    } catch {
      // hata
    }
  };

  // Zone sil
  const handleDelete = async (zoneId: string) => {
    try {
      const res = await fetch(`${API_BASE}/zones/${zoneId}`, { method: 'DELETE' });
      if (res.ok) {
        removeZone(zoneId);
      }
    } catch {
      // hata
    }
  };

  // Temizle
  const handleClear = () => {
    setPoints([]);
    setDrawing(false);
  };

  const cameraZones = zones.filter((z) => z.camera_id === selectedCamera);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* Canvas (sol 2/3) */}
      <div className="lg:col-span-2">
        <div className="bg-gray-900 rounded-lg p-4">
          {/* Kamera seçimi */}
          <div className="flex items-center gap-2 mb-3">
            {CAMERA_IDS.map((id) => (
              <button
                key={id}
                onClick={() => {
                  setSelectedCamera(id);
                  handleClear();
                }}
                className={`px-3 py-1.5 rounded text-sm ${
                  selectedCamera === id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {t(`camera.${id}` as Parameters<typeof t>[0])}
              </button>
            ))}
          </div>

          {/* Canvas */}
          <div className="relative">
            <img
              ref={imgRef}
              src={snapshotUrl}
              alt="Kamera snapshot"
              className="hidden"
              crossOrigin="anonymous"
              onLoad={drawCanvas}
              onError={() => {}}
            />
            <canvas
              ref={canvasRef}
              onClick={handleCanvasClick}
              onContextMenu={handleRightClick}
              onDoubleClick={handleDoubleClick}
              className="w-full rounded cursor-crosshair border border-gray-700"
              style={{ aspectRatio: '16/9', background: '#1f2937' }}
            />
          </div>

          {/* Çizim kontrolleri */}
          <div className="flex items-center gap-3 mt-3">
            <input
              type="text"
              placeholder={t('zone.name_placeholder')}
              value={zoneName}
              onChange={(e) => setZoneName(e.target.value)}
              className="bg-gray-800 border border-gray-600 rounded px-3 py-1.5 text-sm flex-1 focus:outline-none focus:border-blue-500"
            />

            {/* Renk seçimi */}
            <div className="flex gap-1">
              {COLORS.map((c) => (
                <button
                  key={c}
                  onClick={() => setZoneColor(c)}
                  className={`w-6 h-6 rounded border-2 ${
                    zoneColor === c ? 'border-white' : 'border-transparent'
                  }`}
                  style={{ backgroundColor: c }}
                />
              ))}
            </div>

            <button
              onClick={handleSave}
              disabled={points.length < 3 || !zoneName.trim()}
              className="px-4 py-1.5 bg-green-600 hover:bg-green-500 text-white rounded text-sm disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {t('zone.save')}
            </button>

            <button
              onClick={handleClear}
              className="px-4 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded text-sm"
            >
              {t('zone.clear')}
            </button>
          </div>

          {drawing && (
            <p className="text-xs text-gray-400 mt-2">
              {t('zone.drawing_hint')} ({points.length})
            </p>
          )}
        </div>
      </div>

      {/* Zone listesi (sağ 1/3) */}
      <div className="bg-gray-900 rounded-lg p-4">
        <h3 className="text-sm font-bold mb-3">
          {t('zone.title')} ({cameraZones.length})
        </h3>

        <div className="space-y-2">
          {cameraZones.length === 0 ? (
            <p className="text-sm text-gray-500">{t('zone.empty')}</p>
          ) : (
            cameraZones.map((zone) => (
              <div
                key={zone.id}
                className="flex items-center justify-between bg-gray-800 rounded p-2"
              >
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded" style={{ backgroundColor: zone.color }} />
                  <span className="text-sm">{zone.name}</span>
                </div>
                <div className="flex gap-1">
                  <span
                    className={`text-xs px-1.5 py-0.5 rounded ${
                      zone.active ? 'bg-green-800 text-green-300' : 'bg-gray-700 text-gray-400'
                    }`}
                  >
                    {zone.active ? t('zone.active') : t('zone.inactive')}
                  </span>
                  <button
                    onClick={() => handleDelete(zone.id)}
                    className="text-xs px-1.5 py-0.5 rounded bg-gray-700 hover:bg-red-700 text-gray-400 hover:text-white"
                  >
                    {t('zone.delete')}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
