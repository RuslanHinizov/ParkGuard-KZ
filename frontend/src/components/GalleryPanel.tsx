import { useState, useEffect } from 'react';
import {
  Image as ImageIcon,
  X,
  ChevronLeft,
  ChevronRight,
  Camera,
  Clock,
  Search,
  Filter,
} from 'lucide-react';

const API_BASE = '/api';
const PER_PAGE = 20;

interface GalleryItem {
  id: string;
  plate: string;
  camera_id: number;
  camera_name: string;
  zone_name: string;
  screenshot_url: string;
  created_at: string;
  duration_sec: number;
  status: string;
}

const CAMERA_OPTIONS = [
  { value: '', label: 'Все камеры' },
  { value: '1', label: 'Камера 1' },
  { value: '2', label: 'Камера 2' },
  { value: '3', label: 'Камера 3' },
];

export default function GalleryPanel() {
  const [items, setItems] = useState<GalleryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Filters
  const [filterCamera, setFilterCamera] = useState('');
  const [filterDate, setFilterDate] = useState('');
  const [filterPlate, setFilterPlate] = useState('');

  // Lightbox
  const [lightboxItem, setLightboxItem] = useState<GalleryItem | null>(null);

  const fetchGallery = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('page', String(page));
      params.set('per_page', String(PER_PAGE));
      if (filterCamera) params.set('camera_id', filterCamera);
      if (filterDate) params.set('date', filterDate);
      if (filterPlate.trim()) params.set('plate', filterPlate.trim());

      const res = await fetch(`${API_BASE}/gallery?${params}`);
      if (res.ok) {
        const data = await res.json();
        const list: GalleryItem[] = data.items ?? data.gallery ?? (Array.isArray(data) ? data : []);
        setItems(list);
        setTotalPages(data.total_pages ?? Math.max(1, Math.ceil((data.total ?? list.length) / PER_PAGE)));
      }
    } catch {
      // network error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGallery();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, filterCamera, filterDate, filterPlate]);

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return iso;
    }
  };

  const formatDuration = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.round(secs % 60);
    if (m === 0) return `${s} сек`;
    return `${m} мин ${s} сек`;
  };

  // Navigate lightbox
  const navigateLightbox = (dir: -1 | 1) => {
    if (!lightboxItem) return;
    const idx = items.findIndex((i) => i.id === lightboxItem.id);
    const next = idx + dir;
    if (next >= 0 && next < items.length) {
      setLightboxItem(items[next]);
    }
  };

  // Keyboard nav for lightbox
  useEffect(() => {
    if (!lightboxItem) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setLightboxItem(null);
      if (e.key === 'ArrowLeft') navigateLightbox(-1);
      if (e.key === 'ArrowRight') navigateLightbox(1);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lightboxItem, items]);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <ImageIcon className="w-6 h-6 text-blue-400" />
        <h2 className="text-xl font-bold">Галерея</h2>
      </div>

      {/* Filter bar */}
      <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
        <div className="flex flex-wrap items-center gap-3">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            value={filterCamera}
            onChange={(e) => { setFilterCamera(e.target.value); setPage(1); }}
            className="bg-gray-800 text-white rounded-lg px-3 py-1.5 text-sm
                       border border-gray-700 focus:outline-none focus:border-blue-500"
          >
            {CAMERA_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <input
            type="date"
            value={filterDate}
            onChange={(e) => { setFilterDate(e.target.value); setPage(1); }}
            className="bg-gray-800 text-white rounded-lg px-3 py-1.5 text-sm
                       border border-gray-700 focus:outline-none focus:border-blue-500
                       [color-scheme:dark]"
          />
          <div className="relative flex-1 min-w-[150px] max-w-[250px]">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500" />
            <input
              type="text"
              value={filterPlate}
              onChange={(e) => { setFilterPlate(e.target.value.toUpperCase()); setPage(1); }}
              placeholder="Номер..."
              className="w-full bg-gray-800 text-white placeholder-gray-600 rounded-lg pl-8 pr-3 py-1.5
                         text-sm border border-gray-700 focus:outline-none focus:border-blue-500
                         font-mono"
            />
          </div>
          {(filterCamera || filterDate || filterPlate) && (
            <button
              onClick={() => {
                setFilterCamera('');
                setFilterDate('');
                setFilterPlate('');
                setPage(1);
              }}
              className="text-xs text-gray-400 hover:text-white transition-colors"
            >
              Сбросить
            </button>
          )}
        </div>
      </div>

      {/* Gallery grid */}
      {loading ? (
        <div className="flex items-center justify-center py-16 text-gray-500 text-sm">
          Загрузка...
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <ImageIcon className="w-12 h-12 mx-auto mb-3 text-gray-700" />
          <p className="text-sm">Скриншоты не найдены</p>
          <p className="text-xs text-gray-600 mt-1">Попробуйте изменить фильтры</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {items.map((item) => (
            <div
              key={item.id}
              className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden
                         hover:border-gray-700 transition-colors group cursor-pointer"
              onClick={() => setLightboxItem(item)}
            >
              {/* Thumbnail */}
              <div className="relative aspect-video bg-gray-800 overflow-hidden">
                <img
                  src={item.screenshot_url || `${API_BASE}/alarms/${item.id}/screenshot`}
                  alt={item.plate}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  loading="lazy"
                />
                <div className="absolute top-2 right-2">
                  <span
                    className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                      item.status === 'active'
                        ? 'bg-red-600/90 text-white'
                        : 'bg-green-600/90 text-white'
                    }`}
                  >
                    {item.status === 'active' ? 'Акт.' : 'Реш.'}
                  </span>
                </div>
              </div>
              {/* Info */}
              <div className="p-3">
                <p className="text-sm font-mono font-semibold text-white mb-1">
                  {item.plate || '---'}
                </p>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Camera className="w-3 h-3" />
                  <span>{item.camera_name}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500 mt-0.5">
                  <Clock className="w-3 h-3" />
                  <span>{formatDate(item.created_at)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 py-4">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="px-3 py-1.5 rounded-lg text-sm bg-gray-800 text-gray-300
                       hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed
                       transition-colors border border-gray-700"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-sm text-gray-400 px-3">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="px-3 py-1.5 rounded-lg text-sm bg-gray-800 text-gray-300
                       hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed
                       transition-colors border border-gray-700"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Lightbox */}
      {lightboxItem && (
        <div
          className="fixed inset-0 z-50 bg-black/85 flex items-center justify-center p-4"
          onClick={() => setLightboxItem(null)}
        >
          <div
            className="relative max-w-5xl w-full bg-gray-900 rounded-xl border border-gray-700
                       overflow-hidden shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={() => setLightboxItem(null)}
              className="absolute top-3 right-3 bg-gray-800/80 text-white rounded-full p-1.5
                         hover:bg-gray-700 transition-colors z-10"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Navigation arrows */}
            <button
              onClick={() => navigateLightbox(-1)}
              className="absolute left-3 top-1/2 -translate-y-1/2 bg-gray-800/80 text-white
                         rounded-full p-2 hover:bg-gray-700 transition-colors z-10"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button
              onClick={() => navigateLightbox(1)}
              className="absolute right-3 top-1/2 -translate-y-1/2 bg-gray-800/80 text-white
                         rounded-full p-2 hover:bg-gray-700 transition-colors z-10"
            >
              <ChevronRight className="w-5 h-5" />
            </button>

            {/* Image */}
            <div className="bg-black flex items-center justify-center">
              <img
                src={
                  lightboxItem.screenshot_url ||
                  `${API_BASE}/alarms/${lightboxItem.id}/screenshot`
                }
                alt={lightboxItem.plate}
                className="max-w-full max-h-[70vh] object-contain"
              />
            </div>

            {/* Details bar */}
            <div className="px-5 py-4 flex items-center gap-6 border-t border-gray-800">
              <div>
                <p className="text-lg font-mono font-bold text-white">
                  {lightboxItem.plate || '---'}
                </p>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <Camera className="w-4 h-4" />
                <span>{lightboxItem.camera_name}</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <Clock className="w-4 h-4" />
                <span>{formatDate(lightboxItem.created_at)}</span>
              </div>
              <div className="text-sm text-yellow-400">
                {formatDuration(lightboxItem.duration_sec)}
              </div>
              <span
                className={`text-xs px-2 py-0.5 rounded font-medium ml-auto ${
                  lightboxItem.status === 'active'
                    ? 'bg-red-900/50 text-red-400'
                    : 'bg-green-900/50 text-green-400'
                }`}
              >
                {lightboxItem.status === 'active' ? 'Активно' : 'Решено'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
