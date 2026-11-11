import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api, OverviewData } from '../services/api';
import { KPICard } from '../components/KPICard';
import { RevenueLineChart, CategoryProfitBarChart } from '../charts/DashboardCharts';
import { Sparkles, ArrowRight, ShieldCheck, Database, Bot } from 'lucide-react';

export const OverviewPage: React.FC = () => {
  const { activeDataset, setActiveTab, filters } = useApp();
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [charts, setCharts] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!activeDataset) return;
    const load = async () => {
      try {
        setIsLoading(true);
        const [ovData, chData] = await Promise.all([
          api.getOverview(activeDataset.id, filters),
          api.getCharts(activeDataset.id, filters),
        ]);
        setOverview(ovData);
        setCharts(chData);
      } catch (err) {
        console.error('Failed to load overview data:', err);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [activeDataset, filters]);

  if (!activeDataset) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh] text-center p-6">
        <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4">
          <Database className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">No Active Dataset</h2>
        <p className="text-sm text-slate-400 max-w-md mb-6">
          Upload a business CSV or XLSX dataset to generate automatic KPIs, EDA insights, and AI analysis.
        </p>
        <button
          onClick={() => setActiveTab('upload')}
          className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition flex items-center gap-2"
        >
          <span>Go to Data Upload</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Executive Welcome Hero Banner */}
      <div className="relative rounded-2xl p-6 bg-gradient-to-r from-indigo-950/70 via-slate-900 to-slate-950 border border-indigo-800/40 shadow-lg overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-full bg-gradient-to-l from-indigo-500/10 to-transparent pointer-events-none" />
        <div className="max-w-3xl relative z-10">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold mb-3">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>Autonomous Intelligence Engine</span>
          </div>
          <h2 className="text-2xl font-black text-white tracking-tight mb-2">
            Welcome to InsightIQ
          </h2>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mb-4">
            {overview?.auto_summary ||
              `Analyzing active dataset "${activeDataset.filename}" across ${activeDataset.row_count.toLocaleString()} business transactions.`}
          </p>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => setActiveTab('dashboard')}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition flex items-center gap-1.5 shadow-sm shadow-indigo-600/30"
            >
              <span>Explore Full Dashboard</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setActiveTab('ai')}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-semibold text-xs transition flex items-center gap-1.5"
            >
              <Bot className="w-3.5 h-3.5 text-indigo-400" />
              <span>Ask AI Analyst</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      {overview && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {overview.kpis.map((kpi) => (
            <KPICard key={kpi.id} kpi={kpi} />
          ))}
        </div>
      )}

      {/* Primary Analytics Visualization Grid */}
      {charts && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <RevenueLineChart data={charts.revenue_over_time} />
          <CategoryProfitBarChart data={charts.profit_by_category} />
        </div>
      )}
    </div>
  );
};
