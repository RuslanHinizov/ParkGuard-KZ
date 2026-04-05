import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from '../i18n/useTranslation';
import PlateCard from './PlateCard';
import type { Alarm } from '../types';

const API_BASE = '/api';
const PAGE_SIZE = 20;

interface Filters {
  plate: string;
  camera_id: string;   // '' | '1' | '2' | '3'
  status: string;      // '' | 'active' | 'resolved'
  date_from: string;
  date_to: string;
}

const EMPTY_FILTERS: Filters = {
  plate: '', camera_id: '', status: '', date_from: '', date_to: '',
};

export default function AlarmSearch() {
  const { t } = useTranslation();

  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [applied, setApplied] = useState<Filters>(EMPTY_FILTERS);
  const [alarms, setAlarms] = useState<Alarm[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(false);

  const fetchAlarms = useCallback(async (f: Filters, pg: number) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('limit', String(PAGE_SIZE));
      params.set('offset', String(pg * PAGE_SIZE));
      if (f.plate)     params.set('plate', f.plate.trim());
      if (f.camera_id) params.set('camera_id', f.camera_id);
      if (f.status)    params.set('status', f.status);
      if (f.date_from) params.set('date_from', f.date_from);
      if (f.date_to)   params.set('date_to', f.date_to + 'T23:59:59');

      const res = await fetch(`${API_BASE}/alarms?${params}`);
      const data = await res.json();
      setAlarms(data.alarms ?? []);
      setTotal(data.total ?? 0);
    } catch {
      setAlarms([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, []);

  // İlk yükleme ve sayfa değişimi
  useEffect(() => {
    fetchAlarms(applied, page);
  }, [applied, page, fetchAlarms]);

  const handleSearch = () => {
    setPage(0);
    setApplied({ ...filters });
  };

  const handleReset = () => {
    setFilters(EMPTY_FILTERS);
    setPage(0);
    setApplied(EMPTY_FILTERS);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch();
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const from = total === 0 ? 0 : page * PAGE_SIZE + 1;
  const to = Math.min((page + 1) * PAGE_SIZE, total);

  return (
    <div className="space-y-4">
      {/* Filtre satırı */}
      <div className="bg-gray-900 rounded-lg p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Plaka arama */}
          <input
            type="text"
            placeholder={t('filter.plate')}
            value={filters.plate}
            onChange={(e) => setFilters((f) => ({ ...f, plate: e.target.value.toUpperCase() }))}
            onKeyDown={handleKeyDown}
            className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500 font-mono"
          />

          {/* Kamera filtresi */}
          <select
            value={filters.camera_id}
            onChange={(e) => setFilters((f) => ({ ...f, camera_id: e.target.value }))}
            className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
          >
            <option value="">{t('filter.all_cameras')}</option>
            <option value="1">{t('camera.1')}</option>
            <option value="2">{t('camera.2')}</option>
            <option value="3">{t('camera.3')}</option>
          </select>

          {/* Durum filtresi */}
          <select
            value={filters.status}
            onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
            className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
          >
            <option value="">{t('filter.all_status')}</option>
            <option value="active">{t('filter.status_active')}</option>
            <option value="resolved">{t('filter.status_resolved')}</option>
          </select>

          {/* Tarih aralığı */}
          <div className="flex gap-2">
            <div className="flex-1">
              <label className="block text-xs text-gray-500 mb-1">{t('filter.date_from')}</label>
              <input
                type="date"
                value={filters.date_from}
                onChange={(e) => setFilters((f) => ({ ...f, date_from: e.target.value }))}
                className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <div className="flex-1">
              <label className="block text-xs text-gray-500 mb-1">{t('filter.date_to')}</label>
              <input
                type="date"
                value={filters.date_to}
                onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value }))}
                className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          {/* Butonlar */}
          <div className="flex gap-2 items-end">
            <button
              onClick={handleSearch}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm font-medium transition-all"
            >
              {t('filter.search')}
            </button>
            <button
              onClick={handleReset}
              className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded text-sm transition-all"
              title={t('filter.reset')}
            >
              ✕
            </button>
          </div>
        </div>
      </div>

      {/* Sonuç sayısı + sayfalama */}
      <div className="flex items-center justify-between text-sm text-gray-400 px-1">
        <span>
          {total > 0
            ? `${t('filter.showing')} ${from}–${to} / ${t('filter.total')}: ${total}`
            : loading ? '...' : t('filter.no_results')
          }
        </span>

        {totalPages > 1 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded disabled:opacity-40 disabled:cursor-not-allowed text-xs"
            >
              ← {t('filter.prev')}
            </button>
            <span className="text-xs font-mono">{page + 1} / {totalPages}</span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded disabled:opacity-40 disabled:cursor-not-allowed text-xs"
            >
              {t('filter.next')} →
            </button>
          </div>
        )}
      </div>

      {/* Alarm listesi */}
      {loading ? (
        <div className="flex justify-center py-12 text-gray-500">{t('stats.loading')}</div>
      ) : alarms.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-4xl mb-3">🔍</p>
          <p>{t('filter.no_results')}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {alarms.map((alarm) => (
            <PlateCard key={alarm.id} alarm={alarm} />
          ))}
        </div>
      )}

      {/* Alt sayfalama */}
      {totalPages > 1 && !loading && (
        <div className="flex items-center justify-center gap-2 pt-2">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded disabled:opacity-40 disabled:cursor-not-allowed text-sm"
          >
            ← {t('filter.prev')}
          </button>
          <span className="text-sm text-gray-400 font-mono">{page + 1} / {totalPages}</span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded disabled:opacity-40 disabled:cursor-not-allowed text-sm"
          >
            {t('filter.next')} →
          </button>
        </div>
      )}
    </div>
  );
}
