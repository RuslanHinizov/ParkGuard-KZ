/**
 * PenaltyPanel.tsx — Fine Queue Panel
 * Full i18n: ru / kk / en
 */

import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from '../i18n/useTranslation';
import type { Penalty, PenaltyStats } from '../types';

const API = '/api';

// ─── Stat card ───────────────────────────────────────────────────────────────
function StatCard({ label, count, amount, color }: {
  label: string; count: number; amount: number; color: string;
}) {
  return (
    <div className={`rounded-lg p-4 border ${color}`}>
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className="text-2xl font-bold">{count}</p>
      <p className="text-sm text-gray-400 mt-1 font-mono">
        {amount.toLocaleString('ru-RU')} ₸
      </p>
    </div>
  );
}

function duration(sec: number): string {
  if (sec < 60)   return `${sec}s`;
  if (sec < 3600) return `${Math.floor(sec / 60)}m`;
  return `${Math.floor(sec / 3600)}h ${Math.floor((sec % 3600) / 60)}m`;
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function PenaltyPanel() {
  const { t } = useTranslation();

  const [penalties, setPenalties] = useState<Penalty[]>([]);
  const [stats, setStats]         = useState<PenaltyStats | null>(null);
  const [total, setTotal]         = useState(0);
  const [page, setPage]           = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [plateFilter, setPlateFilter]   = useState('');
  const [loading, setLoading]     = useState(false);
  const [sendingId, setSendingId] = useState<string | null>(null);
  const [sendingAll, setSendingAll] = useState(false);

  const PER_PAGE = 20;

  // i18n status labels
  const STATUS_STYLE: Record<string, string> = {
    pending:   'bg-yellow-900/50 text-yellow-300 border border-yellow-700',
    sent:      'bg-green-900/50  text-green-300  border border-green-700',
    cancelled: 'bg-gray-700/50  text-gray-400   border border-gray-600',
  };
  const statusLabel = (s: string) => {
    if (s === 'pending')   return t('penalty.status_pending');
    if (s === 'sent')      return t('penalty.status_sent');
    if (s === 'cancelled') return t('penalty.status_cancelled');
    return s;
  };

  const fetchStats = useCallback(() => {
    fetch(`${API}/penalties/stats`)
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {});
  }, []);

  const fetchPenalties = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams({ limit: String(PER_PAGE), offset: String(page * PER_PAGE) });
    if (statusFilter) params.set('status', statusFilter);
    if (plateFilter)  params.set('plate',  plateFilter);

    fetch(`${API}/penalties?${params}`)
      .then((r) => r.json())
      .then((data) => { setPenalties(data.penalties ?? []); setTotal(data.total ?? 0); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [page, statusFilter, plateFilter]);

  useEffect(() => { fetchStats();     }, [fetchStats]);
  useEffect(() => { fetchPenalties(); }, [fetchPenalties]);

  const sendOne = async (id: string) => {
    setSendingId(id);
    try {
      const res = await fetch(`${API}/penalties/${id}/send`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setPenalties((p) =>
          p.map((x) => x.id === id ? { ...x, status: 'sent', sent_at: data.sent_at ?? x.sent_at } : x)
        );
        fetchStats();
      }
    } catch { /* */ }
    setSendingId(null);
  };

  const cancelOne = async (id: string) => {
    try {
      const res = await fetch(`${API}/penalties/${id}/cancel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'operator' }),
      });
      if (res.ok) { setPenalties((p) => p.map((x) => x.id === id ? { ...x, status: 'cancelled' } : x)); fetchStats(); }
    } catch { /* */ }
  };

  const sendAll = async () => {
    setSendingAll(true);
    try {
      const res = await fetch(`${API}/penalties/send-all`, { method: 'POST' });
      if (res.ok) { fetchPenalties(); fetchStats(); }
    } catch { /* */ }
    setSendingAll(false);
  };

  const pendingCount = stats?.pending?.count ?? 0;
  const totalPages   = Math.ceil(total / PER_PAGE);

  const FILTERS = [
    { v: '',           l: t('penalty.filter_all')       },
    { v: 'pending',    l: t('penalty.filter_pending')   },
    { v: 'sent',       l: t('penalty.filter_sent')      },
    { v: 'cancelled',  l: t('penalty.filter_cancelled') },
  ];

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">💸 {t('penalty.title')}</h2>
          <p className="text-sm text-gray-400 mt-0.5">{t('penalty.subtitle')}</p>
        </div>
        {pendingCount > 0 && (
          <button
            onClick={sendAll}
            disabled={sendingAll}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-orange-600 hover:bg-orange-500
                       text-white font-medium text-sm disabled:opacity-50 transition-all"
          >
            {sendingAll ? <span className="animate-spin">↻</span> : '🚀'}
            {sendingAll ? t('penalty.sending_all') : `${t('penalty.send_all')} (${pendingCount})`}
          </button>
        )}
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard
          label={t('penalty.card_pending')}
          count={stats?.pending?.count   ?? 0}
          amount={stats?.pending?.total_amount ?? 0}
          color="bg-yellow-950/40 border-yellow-800"
        />
        <StatCard
          label={t('penalty.card_sent')}
          count={stats?.sent?.count     ?? 0}
          amount={stats?.sent?.total_amount    ?? 0}
          color="bg-green-950/40 border-green-800"
        />
        <StatCard
          label={t('penalty.card_cancelled')}
          count={stats?.cancelled?.count ?? 0}
          amount={stats?.cancelled?.total_amount ?? 0}
          color="bg-gray-800/40 border-gray-700"
        />
      </div>

      {/* Filters */}
      <div className="flex gap-3 items-center flex-wrap">
        <div className="flex gap-1">
          {FILTERS.map(({ v, l }) => (
            <button
              key={v}
              onClick={() => { setStatusFilter(v); setPage(0); }}
              className={`text-xs px-3 py-1.5 rounded-lg transition-all ${
                statusFilter === v
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              {l}
            </button>
          ))}
        </div>

        <input
          type="text"
          placeholder={t('penalty.search_placeholder')}
          value={plateFilter}
          onChange={(e) => { setPlateFilter(e.target.value); setPage(0); }}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm
                     text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 w-44"
        />

        <button
          onClick={() => { fetchPenalties(); fetchStats(); }}
          className="text-xs px-3 py-1.5 rounded-lg bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700"
        >
          ↻ {t('penalty.refresh')}
        </button>

        <span className="text-xs text-gray-500 ml-auto">
          {t('penalty.total')}: {total} {t('penalty.records')}
        </span>
      </div>

      {/* Table */}
      <div className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
        {loading ? (
          <div className="text-center py-12 text-gray-500">
            <div className="text-2xl animate-spin inline-block mb-2">↻</div>
            <p>{t('penalty.loading')}</p>
          </div>
        ) : penalties.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-4xl mb-3">💸</p>
            <p className="text-sm">{t('penalty.empty')}</p>
            <p className="text-xs text-gray-600 mt-1">{t('penalty.empty_sub')}</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400 text-xs">
                <th className="px-4 py-3 text-left">{t('penalty.col_plate')}</th>
                <th className="px-4 py-3 text-left">{t('penalty.col_camera')}</th>
                <th className="px-4 py-3 text-left">{t('penalty.col_duration')}</th>
                <th className="px-4 py-3 text-right">{t('penalty.col_amount')}</th>
                <th className="px-4 py-3 text-left">{t('penalty.col_status')}</th>
                <th className="px-4 py-3 text-left">{t('penalty.col_date')}</th>
                <th className="px-4 py-3 text-center">{t('penalty.col_action')}</th>
              </tr>
            </thead>
            <tbody>
              {penalties.map((p) => (
                <tr key={p.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                  <td className="px-4 py-3">
                    <span className="font-mono font-bold text-white tracking-wider">{p.plate}</span>
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    <div>{t('penalty.camera')} {p.camera_id}</div>
                    <div className="text-xs text-gray-500">{p.zone_name}</div>
                  </td>
                  <td className="px-4 py-3 text-gray-300">{duration(p.duration_sec)}</td>
                  <td className="px-4 py-3 text-right font-mono font-bold text-orange-400">
                    {p.fine_amount.toLocaleString('ru-RU')}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_STYLE[p.status] ?? ''}`}>
                      {statusLabel(p.status)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {new Date(p.created_at).toLocaleString('ru-RU', {
                      day: '2-digit', month: '2-digit',
                      hour: '2-digit', minute: '2-digit',
                    })}
                    {p.sent_at && (
                      <div className="text-green-600">
                        ✓ {new Date(p.sent_at).toLocaleString('ru-RU', {
                          day: '2-digit', month: '2-digit',
                          hour: '2-digit', minute: '2-digit',
                        })}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1 justify-center">
                      {p.status === 'pending' ? (
                        <>
                          <button
                            onClick={() => sendOne(p.id)}
                            disabled={sendingId === p.id}
                            className="text-xs px-2 py-1 rounded bg-orange-700 hover:bg-orange-600 text-white disabled:opacity-50"
                          >
                            {sendingId === p.id ? '...' : t('penalty.btn_send')}
                          </button>
                          <button
                            onClick={() => cancelOne(p.id)}
                            className="text-xs px-2 py-1 rounded bg-gray-700 hover:bg-red-800 text-gray-400 hover:text-white"
                          >
                            {t('penalty.btn_cancel')}
                          </button>
                        </>
                      ) : (
                        <span className="text-gray-600 text-xs">—</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-3 py-1 rounded bg-gray-800 text-gray-400 hover:text-white disabled:opacity-30 text-sm"
          >
            {t('penalty.prev')}
          </button>
          <span className="text-sm text-gray-400">{page + 1} / {totalPages}</span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="px-3 py-1 rounded bg-gray-800 text-gray-400 hover:text-white disabled:opacity-30 text-sm"
          >
            {t('penalty.next')}
          </button>
        </div>
      )}

      {/* Info note */}
      <div className="bg-blue-950/30 border border-blue-900/50 rounded-lg p-4 text-xs text-blue-300">
        <p className="font-medium mb-1">ℹ️ {t('penalty.info_title')}</p>
        <p className="text-blue-400">
          &lt; 10 min: 5 МРП (18,460 ₸) &nbsp;|&nbsp;
          &lt; 30 min: 10 МРП (36,920 ₸) &nbsp;|&nbsp;
          ≥ 30 min: 15 МРП (55,380 ₸)
        </p>
        <p className="text-blue-500 mt-1">{t('penalty.info_mock')}</p>
      </div>
    </div>
  );
}
