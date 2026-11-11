import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import {
  FileText,
  Download,
  FileSpreadsheet,
  FileCode,
  Sparkles,
  Calendar,
  CheckCircle2,
  Clock,
  Printer,
} from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const { activeDataset } = useApp();
  const [reportType, setReportType] = useState<string>('executive_summary');
  const [format, setFormat] = useState<string>('pdf');
  const [reportTitle, setReportTitle] = useState<string>('');
  const [reportsList, setReportsList] = useState<any[]>([]);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [latestReport, setLatestReport] = useState<any>(null);

  const loadReports = async () => {
    try {
      const list = await api.getReports();
      setReportsList(list);
    } catch (err) {
      console.error('Failed to load reports:', err);
    }
  };

  useEffect(() => {
    loadReports();
  }, [activeDataset]);

  const handleGenerate = async () => {
    if (!activeDataset) return;
    try {
      setIsGenerating(true);
      const res = await api.generateReport(
        activeDataset.id,
        reportType,
        format,
        reportTitle.trim() || undefined
      );
      setLatestReport(res);
      await loadReports();
    } catch (err) {
      console.error('Failed to generate report:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const reportTypes = [
    { id: 'executive_summary', label: 'Executive Summary', desc: 'Holistic C-level commercial and strategic overview' },
    { id: 'monthly_sales', label: 'Monthly Sales Report', desc: 'MoM sales volume, revenue velocities, and seasonality' },
    { id: 'profitability', label: 'Profitability Analysis', desc: 'Unit margins, cost dynamics, and profit contribution' },
    { id: 'revenue', label: 'Revenue Analysis', desc: 'Gross revenue drivers and category distribution' },
    { id: 'weekly', label: 'Weekly Performance Report', desc: 'Short-term tactical order velocities and KPIs' },
  ];

  if (!activeDataset) {
    return <div className="text-center p-12 text-slate-400">Please select an active dataset.</div>;
  }

  return (
    <div className="space-y-6">
      {/* Report Generator Studio Card */}
      <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm space-y-5">
        <div>
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-400" />
            <span>Automated AI Business Report Generator</span>
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Produce publication-ready analytical reports backed by verified computations for '{activeDataset.filename}'.
          </p>
        </div>

        {/* Report Type Selector */}
        <div>
          <label className="text-xs font-semibold text-slate-300 mb-2 block">Select Report Template:</label>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {reportTypes.map((rt) => (
              <div
                key={rt.id}
                onClick={() => setReportType(rt.id)}
                className={`p-3.5 rounded-xl border cursor-pointer transition ${
                  reportType === rt.id
                    ? 'bg-indigo-950/40 border-indigo-500 shadow-xs'
                    : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-xs text-white">{rt.label}</span>
                  {reportType === rt.id && <CheckCircle2 className="w-4 h-4 text-indigo-400" />}
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">{rt.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Custom Title & Export Format */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
          <div>
            <label className="text-xs font-semibold text-slate-300 mb-1.5 block">Custom Report Title (Optional):</label>
            <input
              type="text"
              value={reportTitle}
              onChange={(e) => setReportTitle(e.target.value)}
              placeholder="e.g. Q4 2024 Commercial Executive Briefing"
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 transition"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 mb-1.5 block">Export Format:</label>
            <div className="flex items-center gap-3">
              {[
                { id: 'pdf', label: 'PDF Document', icon: FileText },
                { id: 'xlsx', label: 'Excel (XLSX)', icon: FileSpreadsheet },
                { id: 'csv', label: 'CSV Spreadsheet', icon: FileCode },
              ].map((fmt) => {
                const Icon = fmt.icon;
                return (
                  <button
                    key={fmt.id}
                    type="button"
                    onClick={() => setFormat(fmt.id)}
                    className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg border text-xs font-semibold transition ${
                      format === fmt.id
                        ? 'bg-indigo-600 border-indigo-500 text-white shadow-xs'
                        : 'bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span>{fmt.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="pt-2">
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full sm:w-auto px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-xs transition flex items-center justify-center gap-2 shadow-sm"
          >
            <Sparkles className="w-4 h-4 text-cyan-300" />
            <span>{isGenerating ? 'Compiling Report...' : 'Generate Analytical Report'}</span>
          </button>
        </div>
      </div>

      {/* Generated Report Live Executive Preview */}
      {latestReport && (
        <div className="bg-slate-900/90 border border-indigo-800/40 rounded-xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <span className="text-[10px] bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded font-bold uppercase tracking-wider">
                Report Generated
              </span>
              <h3 className="text-base font-bold text-white mt-1">{latestReport.title}</h3>
              <p className="text-xs text-slate-400">
                Format: <span className="uppercase font-semibold">{latestReport.file_format}</span>
              </p>
            </div>

            <a
              href={latestReport.download_url}
              download
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition shadow-sm"
            >
              <Download className="w-4 h-4" />
              <span>Download File</span>
            </a>
          </div>

          <div className="text-xs leading-relaxed text-slate-300 bg-slate-950/60 p-4 rounded-xl border border-slate-800">
            <h4 className="font-bold text-white mb-1">Executive Summary:</h4>
            <p>{latestReport.summary_text}</p>
          </div>
        </div>
      )}

      {/* Report Archive List */}
      <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm space-y-3">
        <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
          <Clock className="w-4 h-4 text-cyan-400" />
          <span>Report Archive & Export History ({reportsList.length})</span>
        </h3>

        <div className="divide-y divide-slate-800">
          {reportsList.map((r) => (
            <div key={r.id} className="py-3 flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-indigo-400">
                  <FileText className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="font-bold text-white">{r.title}</h4>
                  <p className="text-[11px] text-slate-400">
                    Template: <span className="capitalize">{r.report_type.replace('_', ' ')}</span> • Format: <span className="uppercase">{r.file_format}</span> • {r.created_at.slice(0, 16)}
                  </p>
                </div>
              </div>

              <a
                href={r.download_url}
                download
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white transition font-medium"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download</span>
              </a>
            </div>
          ))}
          {reportsList.length === 0 && (
            <div className="py-8 text-center text-slate-400 text-xs">
              No reports generated yet. Click "Generate Analytical Report" above to build your first report.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
