import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import { CorrelationHeatmap } from '../charts/DashboardCharts';
import { LineChart, Sparkles, BarChart3, Binary, Table } from 'lucide-react';

export const EDAPage: React.FC = () => {
  const { activeDataset } = useApp();
  const [stats, setStats] = useState<any>(null);
  const [correlations, setCorrelations] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'numerical' | 'categorical' | 'correlations'>('numerical');

  useEffect(() => {
    if (!activeDataset) return;
    const load = async () => {
      try {
        setIsLoading(true);
        const [st, corr] = await Promise.all([
          api.getStatistics(activeDataset.id),
          api.getCorrelations(activeDataset.id),
        ]);
        setStats(st);
        setCorrelations(corr);
      } catch (err) {
        console.error('Failed to load EDA data:', err);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [activeDataset]);

  if (!activeDataset) {
    return <div className="text-center p-12 text-slate-400">Please select an active dataset.</div>;
  }

  return (
    <div className="space-y-6">
      {/* Auto-Generated EDA Narrative Summary */}
      {stats?.auto_eda_narrative && (
        <div className="bg-gradient-to-r from-indigo-950/60 to-slate-900 border border-indigo-800/40 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 text-indigo-400 text-xs font-bold uppercase tracking-wider mb-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span>Automated Exploratory Data Analysis Executive Insights</span>
          </div>
          <p className="text-xs sm:text-sm text-slate-200 leading-relaxed">
            {stats.auto_eda_narrative}
          </p>
        </div>
      )}

      {/* EDA Section Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-xs font-semibold">
        <button
          onClick={() => setActiveTab('numerical')}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-lg transition ${
            activeTab === 'numerical'
              ? 'bg-indigo-600 text-white'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <Binary className="w-3.5 h-3.5" />
          <span>Numerical Statistics ({stats?.numerical_stats?.length || 0})</span>
        </button>

        <button
          onClick={() => setActiveTab('categorical')}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-lg transition ${
            activeTab === 'categorical'
              ? 'bg-indigo-600 text-white'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5" />
          <span>Categorical Distributions ({stats?.categorical_stats?.length || 0})</span>
        </button>

        <button
          onClick={() => setActiveTab('correlations')}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-lg transition ${
            activeTab === 'correlations'
              ? 'bg-indigo-600 text-white'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <LineChart className="w-3.5 h-3.5" />
          <span>Correlation Matrix</span>
        </button>
      </div>

      {/* Tab 1: Numerical Statistics Table */}
      {activeTab === 'numerical' && stats && (
        <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead className="bg-slate-900 text-slate-300 uppercase tracking-wider font-semibold border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Metric Column</th>
                  <th className="px-3 py-3 text-right">Count</th>
                  <th className="px-3 py-3 text-right">Mean</th>
                  <th className="px-3 py-3 text-right">Median</th>
                  <th className="px-3 py-3 text-right">Std Dev</th>
                  <th className="px-3 py-3 text-right">Min</th>
                  <th className="px-3 py-3 text-right">25% (Q1)</th>
                  <th className="px-3 py-3 text-right">75% (Q3)</th>
                  <th className="px-3 py-3 text-right">Max</th>
                  <th className="px-3 py-3 text-right">IQR</th>
                  <th className="px-3 py-3 text-right">Skewness</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300">
                {stats.numerical_stats.map((ns: any) => (
                  <tr key={ns.column} className="hover:bg-slate-800/50">
                    <td className="px-4 py-3 font-bold text-white whitespace-nowrap">{ns.column}</td>
                    <td className="px-3 py-3 text-right font-mono">{ns.count.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right font-mono font-semibold text-indigo-400">${ns.mean.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right font-mono">${ns.median.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right font-mono text-slate-400">{ns.std.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right font-mono">${ns.min.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right font-mono">${ns.q25.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right font-mono">${ns.q75.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right font-mono font-semibold text-emerald-400">${ns.max.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right font-mono">{ns.iqr.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right font-mono text-slate-400">{ns.skewness ?? 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Categorical Distributions */}
      {activeTab === 'categorical' && stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {stats.categorical_stats.map((cs: any) => (
            <div
              key={cs.column}
              className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm space-y-3"
            >
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <div>
                  <h4 className="text-sm font-bold text-slate-100">{cs.column}</h4>
                  <p className="text-xs text-slate-400">
                    {cs.unique_count} unique categories across {cs.total_count} records
                  </p>
                </div>
                <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">
                  Top: {cs.top_value}
                </span>
              </div>

              <div className="space-y-2 pt-1">
                {cs.frequencies.map((freq: any) => (
                  <div key={freq.category} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-300 truncate max-w-[180px]">
                        {freq.category}
                      </span>
                      <span className="text-slate-400">
                        {freq.count} ({freq.percentage}%)
                      </span>
                    </div>
                    {/* Progress Bar */}
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-indigo-500 h-1.5 rounded-full"
                        style={{ width: `${freq.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 3: Correlation Heatmap */}
      {activeTab === 'correlations' && correlations && (
        <CorrelationHeatmap
          columns={correlations.columns}
          matrix={correlations.matrix}
        />
      )}
    </div>
  );
};
