import { useState, useEffect } from 'react';
import { FileText, Download, ChevronDown, ChevronUp, Calendar, RefreshCw } from 'lucide-react';

const API_BASE = '/api';

interface Report {
  id: string;
  title: string;
  type: string;
  created_at: string;
  content: string;
  download_url: string;
  camera_id?: number;
  date_from?: string;
  date_to?: string;
}

function normalizeReport(item: any): Report {
  return {
    id: String(item?.id ?? crypto.randomUUID()),
    title: item?.title ?? 'PDF Report',
    type: item?.type ?? item?.report_type ?? 'custom',
    created_at: item?.created_at ?? new Date().toISOString(),
    content:
      item?.content ??
      `PDF report available for ${item?.date_from ?? 'N/A'} - ${item?.date_to ?? 'N/A'}`,
    download_url: `${API_BASE}/reports/${item?.id}/download`,
    camera_id: item?.camera_id,
    date_from: item?.date_from,
    date_to: item?.date_to,
  };
}

const CAMERA_OPTIONS = [
  { value: '', label: 'Все камеры' },
  { value: '1', label: 'Камера 1' },
  { value: '2', label: 'Камера 2' },
  { value: '3', label: 'Камера 3' },
];

export default function ReportPanel() {
  // Custom report state
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [cameraId, setCameraId] = useState('');
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);

  // Auto reports state
  const [reports, setReports] = useState<Report[]>([]);
  const [loadingReports, setLoadingReports] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Set default dates
  useEffect(() => {
    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    setDateFrom(weekAgo.toISOString().slice(0, 10));
    setDateTo(now.toISOString().slice(0, 10));
  }, []);

  const fetchReports = async () => {
    setLoadingReports(true);
    try {
      const res = await fetch(`${API_BASE}/reports`);
      if (res.ok) {
        const data = await res.json();
        const rawList = Array.isArray(data) ? data : data.items ?? data.reports ?? [];
        setReports(rawList.map(normalizeReport));
      }
    } catch {
      // network error
    } finally {
      setLoadingReports(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleGeneratePDF = async () => {
    if (!dateFrom || !dateTo) {
      setGenError('Укажите даты');
      return;
    }
    setGenerating(true);
    setGenError(null);
    try {
      const body: Record<string, string> = {
        date_from: dateFrom,
        date_to: dateTo,
      };
      if (cameraId) body.camera_id = cameraId;

      const res = await fetch(`${API_BASE}/reports/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(errData?.detail ?? `Ошибка ${res.status}`);
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${dateFrom}_${dateTo}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      // Refresh report list
      await fetchReports();
    } catch (err) {
      setGenError(err instanceof Error ? err.message : 'Ошибка генерации');
    } finally {
      setGenerating(false);
    }
  };

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

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3">
        <FileText className="w-6 h-6 text-blue-400" />
        <h2 className="text-xl font-bold">Отчёты</h2>
      </div>

      {/* Custom report section */}
      <div className="bg-gray-900 rounded-lg p-5 border border-gray-800">
        <h3 className="text-base font-semibold mb-4 flex items-center gap-2">
          <Calendar className="w-4 h-4 text-blue-400" />
          Пользовательский отчёт
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Дата начала</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full bg-gray-800 text-white rounded-lg px-3 py-2 text-sm
                         border border-gray-700 focus:outline-none focus:border-blue-500
                         [color-scheme:dark]"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Дата окончания</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-full bg-gray-800 text-white rounded-lg px-3 py-2 text-sm
                         border border-gray-700 focus:outline-none focus:border-blue-500
                         [color-scheme:dark]"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Камера</label>
            <select
              value={cameraId}
              onChange={(e) => setCameraId(e.target.value)}
              className="w-full bg-gray-800 text-white rounded-lg px-3 py-2 text-sm
                         border border-gray-700 focus:outline-none focus:border-blue-500"
            >
              {CAMERA_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleGeneratePDF}
            disabled={generating}
            className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500
                       disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm
                       font-medium px-5 py-2 rounded-lg transition-colors h-[38px]"
          >
            {generating ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            {generating ? 'Генерация...' : 'Скачать PDF'}
          </button>
        </div>

        {genError && (
          <p className="text-red-400 text-xs mt-3">{genError}</p>
        )}
      </div>

      {/* Auto reports section */}
      <div className="bg-gray-900 rounded-lg border border-gray-800">
        <div className="px-5 py-4 border-b border-gray-800 flex items-center justify-between">
          <h3 className="text-base font-semibold flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-400" />
            Автоматические отчёты
          </h3>
          <button
            onClick={fetchReports}
            className="text-gray-400 hover:text-white transition-colors p-1 rounded hover:bg-gray-800"
            title="Обновить"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {loadingReports ? (
          <div className="flex items-center justify-center py-12 text-gray-500 text-sm">
            Загрузка отчётов...
          </div>
        ) : reports.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <FileText className="w-10 h-10 mx-auto mb-3 text-gray-700" />
            <p className="text-sm">Отчётов пока нет</p>
            <p className="text-xs text-gray-600 mt-1">
              Автоматические отчёты генерируются системой
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-800">
            {reports.map((report) => (
              <div key={report.id}>
                <button
                  onClick={() =>
                    setExpandedId(expandedId === report.id ? null : report.id)
                  }
                  className="w-full px-5 py-3 flex items-center justify-between hover:bg-gray-800/50
                             transition-colors text-left"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <FileText className="w-4 h-4 text-gray-500 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-white truncate">
                        {report.title}
                      </p>
                      <p className="text-xs text-gray-500">
                        {report.type} &middot; {formatDate(report.created_at)}
                      </p>
                    </div>
                  </div>
                  {expandedId === report.id ? (
                    <ChevronUp className="w-4 h-4 text-gray-500 flex-shrink-0" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-gray-500 flex-shrink-0" />
                  )}
                </button>
                {expandedId === report.id && (
                  <div className="px-5 pb-4">
                    <div className="flex justify-end mb-3">
                      <a
                        href={report.download_url}
                        className="inline-flex items-center gap-2 text-xs bg-gray-800 hover:bg-gray-700 text-white px-3 py-2 rounded-lg transition-colors"
                      >
                        <Download className="w-3.5 h-3.5" />
                        РЎРєР°С‡Р°С‚СЊ PDF
                      </a>
                    </div>
                    <div className="bg-gray-800/50 rounded-lg p-4 text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                      {report.content}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
