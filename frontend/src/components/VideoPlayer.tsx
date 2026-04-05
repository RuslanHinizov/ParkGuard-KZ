import { useStream } from '../hooks/useStream';
import { useStore } from '../store/useStore';
import { useTranslation } from '../i18n/useTranslation';

interface VideoPlayerProps {
  cameraId: number;
  cameraName: string;
  onFullscreen?: () => void;
}

export default function VideoPlayer({ cameraId, cameraName, onFullscreen }: VideoPlayerProps) {
  const { status, frameUrl } = useStream(cameraId);
  const stats = useStore((s) => s.stats);
  const fps = stats?.fps?.[cameraId] ?? 0;
  const { t } = useTranslation();

  return (
    <div
      className="relative bg-gray-900 rounded-lg overflow-hidden cursor-pointer group"
      onClick={onFullscreen}
    >
      {frameUrl ? (
        <img
          src={frameUrl}
          alt={cameraName}
          className="w-full h-full object-cover"
          draggable={false}
        />
      ) : (
        <div className="w-full aspect-video flex items-center justify-center bg-gray-800">
          <div className="text-center text-gray-400">
            <div className="text-4xl mb-2">
              {status === 'connecting' ? '...' : '✕'}
            </div>
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
        <span
          className={`w-2 h-2 rounded-full ${
            status === 'connected' ? 'bg-green-500' : 'bg-red-500'
          }`}
        />
        <span className="bg-black/60 px-2 py-1 rounded text-xs font-mono">
          {fps.toFixed(1)} FPS
        </span>
      </div>

      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
        <span className="text-white text-2xl">&#x26F6;</span>
      </div>
    </div>
  );
}
