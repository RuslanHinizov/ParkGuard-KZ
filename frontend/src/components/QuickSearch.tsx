import { useState, useEffect, useRef, useCallback } from 'react';
import { Search, Camera, Clock } from 'lucide-react';

const API_BASE = '/api';

interface SearchResult {
  id: string;
  plate: string;
  camera_id: number;
  camera_name?: string;
  zone_name?: string;
  created_at: string;
  status: string;
}

interface QuickSearchProps {
  onNavigate: (plate: string) => void;
}

export default function QuickSearch({ onNavigate }: QuickSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Debounced search
  const doSearch = useCallback(async (q: string) => {
    const trimmed = q.trim();
    if (!trimmed) {
      setResults([]);
      setOpen(false);
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(
        `${API_BASE}/alarms?plate=${encodeURIComponent(trimmed)}&limit=5`
      );
      if (res.ok) {
        const data = await res.json();
        const items: SearchResult[] = data.alarms ?? (Array.isArray(data) ? data : []);
        setResults(items);
        setOpen(items.length > 0);
      }
    } catch {
      // network error
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!query.trim()) {
      setResults([]);
      setOpen(false);
      return;
    }
    debounceRef.current = setTimeout(() => doSearch(query), 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, doSearch]);

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSelect = (plate: string) => {
    setOpen(false);
    setQuery('');
    onNavigate(plate);
  };

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return iso;
    }
  };

  return (
    <div ref={wrapperRef} className="relative">
      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value.toUpperCase())}
          onFocus={() => results.length > 0 && setOpen(true)}
          placeholder="Поиск номера..."
          className="w-48 bg-gray-800 text-white placeholder-gray-600 rounded-lg pl-8 pr-3 py-1.5
                     text-xs border border-gray-700 focus:outline-none focus:border-blue-500
                     font-mono tracking-wider transition-all focus:w-64"
        />
        {loading && (
          <div className="absolute right-2.5 top-1/2 -translate-y-1/2">
            <div className="w-3 h-3 border-2 border-gray-600 border-t-blue-400 rounded-full animate-spin" />
          </div>
        )}
      </div>

      {/* Dropdown */}
      {open && results.length > 0 && (
        <div
          className="absolute top-full left-0 mt-1 w-80 bg-gray-900 border border-gray-700
                     rounded-lg shadow-xl z-50 overflow-hidden"
        >
          <div className="px-3 py-2 border-b border-gray-800">
            <p className="text-xs text-gray-500">
              Найдено: {results.length} {results.length >= 5 ? '(макс. 5)' : ''}
            </p>
          </div>
          <div className="max-h-64 overflow-y-auto">
            {results.map((item) => (
              <button
                key={item.id}
                onClick={() => handleSelect(item.plate)}
                className="w-full px-3 py-2.5 flex items-center gap-3 hover:bg-gray-800
                           transition-colors text-left border-b border-gray-800/50 last:border-b-0"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-mono font-semibold text-white">
                    {item.plate}
                  </p>
                  <div className="flex items-center gap-3 mt-0.5">
                    <span className="flex items-center gap-1 text-xs text-gray-500">
                      <Camera className="w-3 h-3" />
                      {item.camera_name ?? `Камера ${item.camera_id}`}
                    </span>
                    <span className="flex items-center gap-1 text-xs text-gray-500">
                      <Clock className="w-3 h-3" />
                      {formatDate(item.created_at)}
                    </span>
                  </div>
                </div>
                <span
                  className={`text-xs px-1.5 py-0.5 rounded flex-shrink-0 ${
                    item.status === 'active'
                      ? 'bg-red-900/50 text-red-400'
                      : 'bg-green-900/50 text-green-400'
                  }`}
                >
                  {item.status === 'active' ? 'Акт.' : 'Реш.'}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
