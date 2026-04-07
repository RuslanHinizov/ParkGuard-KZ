import { useState, useEffect } from 'react';
import { Trash2, Plus, ShieldCheck } from 'lucide-react';
import { useTranslation } from '../i18n/useTranslation';

const API_BASE = '/api';

interface WhitelistEntry {
  plate: string;
  reason: string;
  created_at: string;
}

export default function WhitelistPanel() {
  const { t } = useTranslation();

  // Reason options are translated keys
  const REASON_KEYS = [
    'wl.reason_staff',
    'wl.reason_disabled',
    'wl.reason_vip',
    'wl.reason_special',
    'wl.reason_other',
  ] as const;

  const [entries, setEntries] = useState<WhitelistEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [plate, setPlate]     = useState('');
  const [reasonKey, setReasonKey] = useState<typeof REASON_KEYS[number]>(REASON_KEYS[0]);
  const [adding, setAdding]   = useState(false);
  const [error, setError]     = useState<string | null>(null);

  const fetchWhitelist = async () => {
    try {
      const res = await fetch(`${API_BASE}/whitelist`);
      if (res.ok) {
        const data = await res.json();
        setEntries(Array.isArray(data) ? data : data.items ?? data.entries ?? []);
      }
    } catch { /* network error */ }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchWhitelist(); }, []);

  const handleAdd = async () => {
    const trimmed = plate.trim().toUpperCase();
    if (!trimmed) { setError(t('wl.enter_plate')); return; }
    setAdding(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/whitelist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plate: trimmed, reason: t(reasonKey) }),
      });
      if (res.ok) {
        setPlate('');
        setReasonKey(REASON_KEYS[0]);
        await fetchWhitelist();
      } else {
        const data = await res.json().catch(() => null);
        setError(data?.detail ?? 'Error');
      }
    } catch { setError('Network error'); }
    finally { setAdding(false); }
  };

  const handleDelete = async (plateNum: string) => {
    try {
      const res = await fetch(`${API_BASE}/whitelist/${encodeURIComponent(plateNum)}`, { method: 'DELETE' });
      if (res.ok) setEntries((prev) => prev.filter((e) => e.plate !== plateNum));
    } catch { /* network error */ }
  };

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString('ru-RU', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
    } catch { return iso; }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-48 text-gray-500">{t('wl.loading')}</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <ShieldCheck className="w-6 h-6 text-blue-400" />
        <h2 className="text-xl font-bold">{t('wl.title')}</h2>
        <span className="text-sm text-gray-500">({entries.length} {t('wl.entries_count')})</span>
      </div>

      {/* Add form */}
      <div className="bg-gray-900 rounded-lg p-5 border border-gray-800">
        <h3 className="text-sm font-semibold text-gray-400 mb-4">{t('wl.add_title')}</h3>
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs text-gray-500 mb-1">{t('wl.plate_label')}</label>
            <input
              type="text"
              value={plate}
              onChange={(e) => setPlate(e.target.value.toUpperCase())}
              placeholder="A123BC 77"
              className="w-full bg-gray-800 text-white placeholder-gray-600 rounded-lg px-3 py-2
                         text-sm border border-gray-700 focus:outline-none focus:border-blue-500
                         font-mono tracking-wider"
            />
          </div>
          <div className="min-w-[180px]">
            <label className="block text-xs text-gray-500 mb-1">{t('wl.reason_label')}</label>
            <select
              value={reasonKey}
              onChange={(e) => setReasonKey(e.target.value as typeof REASON_KEYS[number])}
              className="w-full bg-gray-800 text-white rounded-lg px-3 py-2 text-sm
                         border border-gray-700 focus:outline-none focus:border-blue-500"
            >
              {REASON_KEYS.map((k) => (
                <option key={k} value={k}>{t(k)}</option>
              ))}
            </select>
          </div>
          <button
            onClick={handleAdd}
            disabled={adding}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50
                       disabled:cursor-not-allowed text-white text-sm font-medium px-5 py-2
                       rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            {adding ? t('wl.adding') : t('wl.add_btn')}
          </button>
        </div>
        {error && <p className="text-red-400 text-xs mt-2">{error}</p>}
      </div>

      {/* Table */}
      <div className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
        {entries.length === 0 ? (
          <div className="text-center text-gray-500 py-12">
            <ShieldCheck className="w-10 h-10 mx-auto mb-3 text-gray-700" />
            <p className="text-sm">{t('wl.empty')}</p>
            <p className="text-xs text-gray-600 mt-1">{t('wl.empty_sub')}</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400 text-xs uppercase tracking-wider">
                <th className="text-left px-4 py-3">{t('wl.col_plate')}</th>
                <th className="text-left px-4 py-3">{t('wl.col_reason')}</th>
                <th className="text-left px-4 py-3">{t('wl.col_date')}</th>
                <th className="text-right px-4 py-3">{t('wl.col_action')}</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr
                  key={entry.plate}
                  className="border-b border-gray-800/50 hover:bg-gray-800/50 transition-colors"
                >
                  <td className="px-4 py-3 font-mono font-semibold text-white tracking-wider">
                    {entry.plate}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                      entry.reason === 'VIP'
                        ? 'bg-yellow-900/50 text-yellow-400 border border-yellow-800'
                        : 'bg-gray-800 text-gray-400 border border-gray-700'
                    }`}>
                      {entry.reason}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400">{formatDate(entry.created_at)}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDelete(entry.plate)}
                      className="text-gray-500 hover:text-red-400 transition-colors p-1 rounded hover:bg-red-900/20"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
