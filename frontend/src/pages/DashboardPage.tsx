import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api, OverviewData } from '../services/api';
import { KPICard } from '../components/KPICard';
import { FilterBar } from '../components/FilterBar';
import {
  RevenueLineChart,
  CategoryProfitBarChart,
  RegionalSalesChart,
  ProductPerformanceChart,
  RevenueDonutChart,
  ProfitabilityScatterPlot,
  MonthlySalesAreaChart,
} from '../charts/DashboardCharts';
import { RefreshCw } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { activeDataset, filters } = useApp();
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [charts, setCharts] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const loadDashboard = async () => {
    if (!activeDataset) return;
    try {
      setIsLoading(true);
      const [ovData, chData] = await Promise.all([
        api.getOverview(activeDataset.id, filters),
        api.getCharts(activeDataset.id, filters),
      ]);
      setOverview(ovData);
      setCharts(chData);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, [activeDataset, filters]);

  if (!activeDataset) {
    return <div className="text-center p-12 text-slate-400">Please select an active dataset.</div>;
  }

  return (
    <div className="space-y-6">
      {/* Interactive Filter Bar */}
      <FilterBar
        categories={overview?.categories}
        regions={overview?.regions}
        dateRange={overview?.date_range}
        onFilterChange={loadDashboard}
      />

      {/* Dynamic KPI Cards Grid */}
      {overview && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {overview.kpis.map((kpi) => (
            <KPICard key={kpi.id} kpi={kpi} />
          ))}
        </div>
      )}

      {/* Interactive Charts Matrix */}
      {charts && (
        <div className="space-y-6">
          {/* Row 1: Revenue Line & Monthly Area Chart */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <RevenueLineChart data={charts.revenue_over_time} />
            <MonthlySalesAreaChart data={charts.monthly_sales_distribution} />
          </div>

          {/* Row 2: Category Bar & Regional Sales */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <CategoryProfitBarChart data={charts.profit_by_category} />
            <RegionalSalesChart data={charts.sales_by_region} />
          </div>

          {/* Row 3: Product Performance & Category Donut */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ProductPerformanceChart data={charts.product_performance} />
            <RevenueDonutChart data={charts.revenue_contribution} />
          </div>

          {/* Row 4: Profitability Scatter Plot */}
          <div className="w-full">
            <ProfitabilityScatterPlot data={charts.profitability_scatter} />
          </div>
        </div>
      )}
    </div>
  );
};
