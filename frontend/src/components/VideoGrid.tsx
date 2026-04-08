import VideoPlayer from './VideoPlayer';
import { useStore } from '../store/useStore';
import { useTranslation } from '../i18n/useTranslation';

export default function VideoGrid() {
  const activeCameraId = useStore((s) => s.activeCameraId);
  const setActiveCameraId = useStore((s) => s.setActiveCameraId);
  const stats = useStore((s) => s.stats);
  const { t } = useTranslation();
  const cameraIds = Object.keys(stats?.cameras ?? {})
    .map((id) => Number(id))
    .filter((id) => Number.isFinite(id))
    .sort((a, b) => a - b);
  const visibleCameraIds = cameraIds.length > 0 ? cameraIds : [1];

  if (activeCameraId !== null) {
    return (
      <div className="relative">
        <VideoPlayer
          cameraId={activeCameraId}
          cameraName={t(`camera.${activeCameraId}` as Parameters<typeof t>[0])}
          onFullscreen={() => setActiveCameraId(null)}
        />
        <button
          onClick={() => setActiveCameraId(null)}
          className="absolute top-4 right-4 z-10 bg-black/70 hover:bg-black/90 text-white px-3 py-1 rounded text-sm"
        >
          {t('video.back_to_grid')}
        </button>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
      {visibleCameraIds.map((id) => (
        <VideoPlayer
          key={id}
          cameraId={id}
          cameraName={t(`camera.${id}` as Parameters<typeof t>[0])}
          onFullscreen={() => setActiveCameraId(id)}
        />
      ))}
    </div>
  );
}
