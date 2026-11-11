import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import {
  AlertTriangle,
  Activity,
  Sliders,
  CheckCircle,
  AlertOctagon,
  RefreshCw,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';

export const AnomalyPage: React.FC = () => {
  const { activeDataset } = useApp();
  const [data, setData] = useState<any>(null);
  const [method, setMethod] = useState<string>('isolation_forest');
  const [metricColumn, setMetricColumn] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const runDetection = async () => {
    if (!activeDataset) return;
    try {
      setIsLoading(true);
      const res = await api.detectAnomalies(activeDataset.id, method, metricColumn || undefined);
      setData(res);
    } catch (err) {
      console.error('Failed to detect anomalies:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    runDetection();
  }, [activeDataset, method, metricColumn]);

  if (!activeDataset) {
    return <div className="text-center p-12 text-slate-400">Please select an active dataset.</div>;
  }

  return (
    <div className="space-y-6">
      {/* Control & Method Switcher Header */}
      <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <span>Statistical & ML Anomaly Detection Engine</span>
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Uncovers spikes, negative margins, and abnormal transactional deviations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Method Selector */}
          <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 rounded-lg p-1 text-xs">
            {[
              { id: 'isolation_forest', label: 'Isolation Forest' },
              { id: 'zscore', label: 'Z-Score (2.5σ)' },
              { id: 'iqr', label: 'IQR Outliers' },
            ].map((m) => (
              <button
                key={m.id}
                onClick={() => setMethod(m.id)}
                className={`px-3 py-1.5 rounded-md font-medium transition ${
                  method === m.id
                    ? 'bg-indigo-600 text-white font-semibold shadow-xs'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>

          <button
            onClick={runDetection}
            disabled={isLoading}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Summary KPI Badges */}
      {data && (
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-4">
            <span className="text-xs text-slate-400 font-medium">Metric Analyzed</span>
            <p className="text-lg font-bold text-white mt-1">{data.metric_analyzed}</p>
          </div>
          <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-4">
            <span className="text-xs text-slate-400 font-medium">Flagged Anomalies</span>
            <p className="text-lg font-bold text-amber-400 mt-1">
              {data.anomalies_detected_count}{' '}
              <span className="text-xs font-normal text-slate-400">records</span>
            </p>
          </div>
          <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-4">
            <span className="text-xs text-slate-400 font-medium">Anomaly Rate</span>
            <p className="text-lg font-bold text-white mt-1">{data.anomaly_rate_pct}%</p>
          </div>
          <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-4">
            <span className="text-xs text-slate-400 font-medium">Detection Method</span>
            <p className="text-lg font-bold text-indigo-400 mt-1 capitalize">
              {data.method_used.replace('_', ' ')}
            </p>
          </div>
        </div>
      )}

      {/* Anomaly Plot with Expected Range */}
      {data?.time_series_plot?.length > 0 && (
        <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm space-y-2">
          <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            <span>Distribution Trajectory & Expected Bounds</span>
          </h4>
          <p className="text-xs text-slate-400">
            Yellow bounds represent normal operating tolerance; points outside trigger anomaly alerts.
          </p>

          <div className="h-64 w-full pt-3">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.time_series_plot}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" fontSize={10} tickFormatter={(v) => `$${v}`} />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={1.5} dot={false} />
                <Line type="monotone" dataKey="upper_bound" stroke="#f59e0b" strokeDasharray="4 4" dot={false} />
                <Line type="monotone" dataKey="lower_bound" stroke="#f59e0b" strokeDasharray="4 4" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Anomalies Item Grid */}
      <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm space-y-3">
        <h4 className="text-sm font-bold text-slate-100">
          Detected Outlier Records ({data?.anomalies?.length || 0})
        </h4>

        <div className="space-y-2.5">
          {data?.anomalies?.map((an: any, idx: number) => {
            const isCrit = an.severity === 'Critical';
            return (
              <div
                key={idx}
                className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs"
              >
                <div className="space-y-1 max-w-lg">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white text-xs">{an.record_id}</span>
                    {an.date && <span className="text-slate-400">({an.date})</span>}
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                        isCrit
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      }`}
                    >
                      {an.severity}
                    </span>
                    {an.is_confirmed_issue && (
                      <span className="text-[10px] bg-red-950 text-red-300 px-2 py-0.5 rounded font-medium">
                        Margin Loss
                      </span>
                    )}
                  </div>
                  <p className="text-slate-300">{an.reason}</p>
                </div>

                <div className="flex items-center gap-6 text-right">
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase">Actual</span>
                    <p className="font-bold text-white text-sm">
                      ${an.actual_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase">Baseline / Expected</span>
                    <p className="font-medium text-slate-400 text-xs">
                      ${an.expected_baseline.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase">Deviation</span>
                    <p className={`font-bold text-xs ${an.deviation_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {an.deviation_pct > 0 ? '+' : ''}
                      {an.deviation_pct}%
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
