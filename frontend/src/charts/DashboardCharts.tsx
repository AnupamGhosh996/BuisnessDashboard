import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

const COLORS = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#3b82f6'];

// Custom Dark Tooltip
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#0f172a] border border-slate-700/80 p-3 rounded-lg shadow-xl text-xs">
        <p className="font-semibold text-slate-200 mb-1.5">{label}</p>
        {payload.map((entry: any, index: number) => (
          <div key={`item-${index}`} className="flex items-center justify-between gap-4 py-0.5">
            <span className="flex items-center gap-1.5 text-slate-400">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
              {entry.name}:
            </span>
            <span className="font-bold text-white">
              {typeof entry.value === 'number' && entry.name.toLowerCase().includes('profit') || entry.name.toLowerCase().includes('revenue') || entry.name.toLowerCase().includes('value')
                ? `$${entry.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                : entry.value.toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

// 1. Revenue & Profit Over Time (Line Chart)
export const RevenueLineChart: React.FC<{ data: any[] }> = ({ data }) => {
  return (
    <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-100">Revenue & Profit Trajectory</h3>
          <p className="text-xs text-slate-400">Monthly revenue trends vs net generated profit</p>
        </div>
      </div>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="period" stroke="#64748b" fontSize={11} tickLine={false} />
            <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `$${v / 1000}k`} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
            <Line type="monotone" dataKey="revenue" name="Revenue" stroke="#6366f1" strokeWidth={2.5} dot={{ r: 3, fill: '#6366f1' }} activeDot={{ r: 6 }} />
            <Line type="monotone" dataKey="profit" name="Profit" stroke="#10b981" strokeWidth={2.5} dot={{ r: 3, fill: '#10b981' }} activeDot={{ r: 6 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// 2. Profit by Category (Bar Chart)
export const CategoryProfitBarChart: React.FC<{ data: any[] }> = ({ data }) => {
  return (
    <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-100">Profit & Revenue by Category</h3>
          <p className="text-xs text-slate-400">Comparison of performance across segments</p>
        </div>
      </div>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="category" stroke="#64748b" fontSize={11} tickLine={false} />
            <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `$${v / 1000}k`} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
            <Bar dataKey="revenue" name="Revenue" fill="#6366f1" radius={[4, 4, 0, 0]} />
            <Bar dataKey="profit" name="Profit" fill="#06b6d4" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// 3. Sales by Region (Bar Chart)
export const RegionalSalesChart: React.FC<{ data: any[] }> = ({ data }) => {
  return (
    <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-100">Regional Performance</h3>
          <p className="text-xs text-slate-400">Territory breakdown by total gross revenue</p>
        </div>
      </div>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 10, right: 20, left: 30, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis type="number" stroke="#64748b" fontSize={11} tickFormatter={(v) => `$${v / 1000}k`} />
            <YAxis type="category" dataKey="region" stroke="#64748b" fontSize={11} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="revenue" name="Revenue" fill="#06b6d4" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// 4. Product Performance (Horizontal Bar Chart)
export const ProductPerformanceChart: React.FC<{ data: any[] }> = ({ data }) => {
  return (
    <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-100">Top 10 Products by Revenue</h3>
          <p className="text-xs text-slate-400">Commercial ranking of high-performing inventory</p>
        </div>
      </div>
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 5, right: 20, left: 70, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis type="number" stroke="#64748b" fontSize={11} tickFormatter={(v) => `$${v / 1000}k`} />
            <YAxis type="category" dataKey="product" stroke="#94a3b8" fontSize={10} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="revenue" name="Revenue" fill="#6366f1" radius={[0, 4, 4, 0]} />
            <Bar dataKey="profit" name="Profit" fill="#10b981" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// 5. Revenue Contribution (Donut Chart)
export const RevenueDonutChart: React.FC<{ data: any[] }> = ({ data }) => {
  return (
    <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-100">Category Contribution</h3>
          <p className="text-xs text-slate-400">Percentage share of total gross revenue</p>
        </div>
      </div>
      <div className="h-72 w-full flex items-center justify-center">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={4}
              label={({ name, percentage }) => `${name}: ${percentage}%`}
              labelLine={false}
            >
              {data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// 6. Profitability Scatter Plot
export const ProfitabilityScatterPlot: React.FC<{ data: any[] }> = ({ data }) => {
  return (
    <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-100">Profitability Scatter (Revenue vs Profit)</h3>
          <p className="text-xs text-slate-400">Order-level correlation between revenue volume and net profit</p>
        </div>
      </div>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="revenue" name="Revenue" stroke="#64748b" fontSize={11} tickFormatter={(v) => `$${v}`} />
            <YAxis dataKey="profit" name="Profit" stroke="#64748b" fontSize={11} tickFormatter={(v) => `$${v}`} />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} content={<CustomTooltip />} />
            <Scatter name="Transactions" data={data} fill="#818cf8" fillOpacity={0.7} />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// 7. Monthly Sales Distribution (Area Chart)
export const MonthlySalesAreaChart: React.FC<{ data: any[] }> = ({ data }) => {
  return (
    <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-100">Cumulative Sales Volume</h3>
          <p className="text-xs text-slate-400">Distribution of monthly sales over time</p>
        </div>
      </div>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
            <YAxis stroke="#64748b" fontSize={11} tickFormatter={(v) => `$${v / 1000}k`} />
            <Tooltip content={<CustomTooltip />} />
            <Area type="monotone" dataKey="revenue" stroke="#6366f1" fillOpacity={1} fill="url(#colorRev)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// 8. Correlation Heatmap Component
export const CorrelationHeatmap: React.FC<{ columns: string[]; matrix: number[][] }> = ({ columns, matrix }) => {
  const getColor = (val: number) => {
    if (val >= 0.7) return 'bg-indigo-600 text-white font-bold';
    if (val >= 0.3) return 'bg-indigo-900/80 text-indigo-200';
    if (val >= -0.3) return 'bg-slate-800/60 text-slate-400';
    if (val >= -0.7) return 'bg-rose-900/60 text-rose-200';
    return 'bg-rose-600 text-white font-bold';
  };

  return (
    <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm overflow-x-auto">
      <div className="mb-4">
        <h3 className="text-sm font-bold text-slate-100">Pearson Correlation Heatmap</h3>
        <p className="text-xs text-slate-400">Statistical relationships between numerical attributes</p>
      </div>
      <table className="w-full text-xs text-center border-collapse">
        <thead>
          <tr>
            <th className="p-2 text-left font-semibold text-slate-400"></th>
            {columns.map((c) => (
              <th key={c} className="p-2 font-semibold text-slate-300 truncate max-w-[100px]">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={columns[i]}>
              <td className="p-2 text-left font-semibold text-slate-300 truncate max-w-[120px]">
                {columns[i]}
              </td>
              {row.map((val, j) => (
                <td key={j} className="p-1">
                  <div className={`p-2 rounded font-mono text-xs ${getColor(val)}`}>
                    {val.toFixed(2)}
                  </div>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
