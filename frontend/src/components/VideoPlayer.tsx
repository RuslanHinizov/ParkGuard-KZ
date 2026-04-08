import { useMemo } from 'react';
import { useStream } from '../hooks/useStream';
import { useMetadata } from '../hooks/useMetadata';
import { useStore } from '../store/useStore';
import { useTranslation } from '../i18n/useTranslation';

interface VideoPlayerProps {
  cameraId: number;
  cameraName: string;
  onFullscreen?: () => void;
}

function hexToRgba(hex: string, alpha: number) {
  const value = hex.replace('#', '');
  const r = parseInt(value.slice(0, 2), 16);
  const g = parseInt(value.slice(2, 4), 16);
  const b = parseInt(value.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export default function VideoPlayer({ cameraId, cameraName, onFullscreen }: VideoPlayerProps) {
  const { status, source, videoRef } = useStream(cameraId);
  const { metadata } = useMetadata(cameraId);
  const stats = useStore((s) => s.stats);
  const fps = stats?.fps?.[cameraId] ?? 0;
  const { t } = useTranslation();

  const viewBox = useMemo(() => {
    const width = metadata?.frame_width ?? 1920;
    const height = metadata?.frame_height ?? 1080;
    return `0 0 ${width} ${height}`;
  }, [metadata?.frame_height, metadata?.frame_width]);

  return (
    <div
      className="relative bg-gray-950 rounded-lg overflow-hidden cursor-pointer group aspect-video"
      onClick={onFullscreen}
    >
      <video
        ref={videoRef}
        className="w-full h-full object-contain bg-black"
        muted
        autoPlay
        playsInline
        preload="auto"
      />

      {metadata && (
        <svg
          viewBox={viewBox}
          preserveAspectRatio="xMidYMid meet"
          className="absolute inset-0 w-full h-full pointer-events-none"
        >
          {metadata.zones.map((zone) => (
            <g key={zone.id}>
              <polygon
                points={zone.polygon.map((point) => point.join(',')).join(' ')}
                fill={hexToRgba(zone.color, 0.20)}
                stroke={zone.color}
                strokeWidth={3}
              />
              <text
                x={zone.polygon.reduce((sum, point) => sum + point[0], 0) / zone.polygon.length}
                y={zone.polygon.reduce((sum, point) => sum + point[1], 0) / zone.polygon.length}
                fill="#ffffff"
                fontSize="24"
                textAnchor="middle"
              >
                {zone.name}
              </text>
            </g>
          ))}

          {metadata.detections.map((det, index) => {
            const [x1, y1, x2, y2] = det.bbox;
            const plateConfidence =
              det.plate && det.plate_conf != null ? ` ${Math.round(det.plate_conf * 100)}%` : '';
            const label = `ID:${det.track_id ?? '?'} ${det.class_name}${det.plate ? ` | ${det.plate}${plateConfidence}` : ''}`;
            const color = det.in_violation ? '#ef4444' : '#22c55e';
            const labelWidth = Math.max(180, label.length * 11);
            const labelY = Math.max(28, y1 - 10);

            return (
              <g key={`${det.track_id ?? 'na'}-${index}`}>
                <rect
                  x={x1}
                  y={y1}
                  width={Math.max(0, x2 - x1)}
                  height={Math.max(0, y2 - y1)}
                  fill="none"
                  stroke={color}
                  strokeWidth={4}
                />
                <rect
                  x={x1}
                  y={labelY - 28}
                  width={labelWidth}
                  height={28}
                  rx={4}
                  fill={color}
                />
                <text
                  x={x1 + 8}
                  y={labelY - 8}
                  fill="#ffffff"
                  fontSize="18"
                  fontFamily="monospace"
                >
                  {label}
                </text>
              </g>
            );
          })}
        </svg>
      )}

      {status !== 'connected' && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900/75">
          <div className="text-center text-gray-300">
            <div className="text-4xl mb-2">{status === 'connecting' ? '...' : '✕'}</div>
            <p className="text-sm">
              {status === 'connecting' ? t('video.connecting') : t('video.no_signal')}
            </p>
          </div>
        </div>
      )}

      <div className="absolute top-2 left-2 bg-black/60 px-2 py-1 rounded text-xs font-medium">
        {cameraName}
      </div>

      <div className="absolute top-2 right-2 flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${status === 'connected' ? 'bg-green-500' : 'bg-red-500'}`} />
        <span className="bg-black/60 px-2 py-1 rounded text-xs font-mono">
          {fps.toFixed(1)} FPS
        </span>
        {source?.mode && (
          <span className="bg-black/60 px-2 py-1 rounded text-[10px] font-mono uppercase">
            {source.mode}
          </span>
        )}
      </div>

      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/15 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
        <span className="text-white text-2xl">&#x26F6;</span>
      </div>
    </div>
  );
}
