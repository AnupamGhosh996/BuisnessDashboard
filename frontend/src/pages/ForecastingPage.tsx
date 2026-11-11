import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import {
  TrendingUp,
  Calendar,
  AlertCircle,
  HelpCircle,
  ArrowUpRight,
  ArrowDownRight,
  BarChart,
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
  Legend,
} from 'recharts';

export const ForecastingPage: React.FC = () => {
  const { activeDataset } = useApp();
  const [forecastData, setForecastData] = useState<any>(null);
  const [horizonDays, setHorizonDays] = useState<number>(30);
  const [method, setMethod] = useState<string>('linear');
  const [metricColumn, setMetricColumn] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const runForecast = async () => {
    if (!activeDataset) return;
    try {
      setIsLoading(true);
      setErrorMsg(null);
      const res = await api.getForecast(
        activeDataset.id,
        horizonDays,
        method,
        metricColumn || undefined
      );
      setForecastData(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Forecasting failed');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    runForecast();
  }, [activeDataset, horizonDays, method, metricColumn]);

  if (!activeDataset) {
    return <div className="text-center p-12 text-slate-400">Please select an active dataset.</div>;
  }

  return (
    <div className="space-y-6">
      {/* Forecasting Studio Controls */}
      <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-indigo-400" />
              <span>Time-Series Predictive Forecasting Studio</span>
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Select horizon and statistical predictive algorithm to project commercial trajectory.
            </p>
          </div>

          <button
            onClick={runForecast}
            disabled={isLoading}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Configuration Row */}
        <div className="flex flex-wrap items-center gap-4 text-xs pt-2">
          {/* Horizon Selection */}
          <div className="flex items-center gap-2">
            <span className="text-slate-400 font-medium">Horizon:</span>
            {[
              { days: 7, label: '7 Days' },
              { days: 30, label: '30 Days' },
              { days: 90, label: '3 Months' },
              { days: 180, label: '6 Months' },
            ].map((h) => (
              <button
                key={h.days}
                onClick={() => setHorizonDays(h.days)}
                className={`px-3 py-1.5 rounded-lg font-medium transition ${
                  horizonDays === h.days
                    ? 'bg-indigo-600 text-white font-semibold'
                    : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                {h.label}
              </button>
            ))}
          </div>

          {/* Algorithm Selection */}
          <div className="flex items-center gap-2">
            <span className="text-slate-400 font-medium">Model:</span>
            {[
              { id: 'linear', label: 'Linear Regression' },
              { id: 'exponential_smoothing', label: 'Exponential Smoothing' },
              { id: 'moving_average', label: 'Moving Average' },
            ].map((m) => (
              <button
                key={m.id}
                onClick={() => setMethod(m.id)}
                className={`px-3 py-1.5 rounded-lg font-medium transition ${
                  method === m.id
                    ? 'bg-cyan-600 text-white font-semibold'
                    : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>

        {errorMsg && (
          <div className="flex items-center gap-2 text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 p-3 rounded-lg">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}
      </div>

      {/* Forecast Accuracy & Direction Badges */}
      {forecastData && (
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-4">
            <span className="text-xs text-slate-400 font-medium">Trajectory Trend</span>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-lg font-bold text-white">{forecastData.trend_direction}</span>
              {forecastData.trend_direction.includes('Up') ? (
                <ArrowUpRight className="w-5 h-5 text-emerald-400" />
              ) : (
                <ArrowDownRight className="w-5 h-5 text-rose-400" />
              )}
            </div>
          </div>

          <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-4">
            <span className="text-xs text-slate-400 font-medium">Forecast Accuracy (MAPE)</span>
            <p className="text-lg font-bold text-cyan-400 mt-1">
              {forecastData.accuracy.mape}%
              <span className="text-xs font-normal text-slate-400 ml-1.5">error rate</span>
            </p>
          </div>

          <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-4">
            <span className="text-xs text-slate-400 font-medium">Mean Absolute Error (MAE)</span>
            <p className="text-lg font-bold text-white mt-1">
              ${forecastData.accuracy.mae.toLocaleString()}
            </p>
          </div>

          <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-4">
            <span className="text-xs text-slate-400 font-medium">Target Metric</span>
            <p className="text-lg font-bold text-indigo-400 mt-1">{forecastData.metric}</p>
          </div>
        </div>
      )}

      {/* Historical vs Forecast Chart with Upper/Lower Bounds */}
      {forecastData?.points?.length > 0 && (
        <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <BarChart className="w-4 h-4 text-cyan-400" />
              <span>Historical Reality vs Model Projection (95% Confidence Interval)</span>
            </h4>
            <span className="text-xs text-slate-400 font-mono">
              {forecastData.horizon_days}-Day Outlook
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Solid line shows observed data; dashed line represents forecast with upper and lower probability boundaries.
          </p>

          <div className="h-80 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={forecastData.points}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" fontSize={10} tickFormatter={(v) => `$${v / 1000}k`} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Line
                  type="monotone"
                  dataKey="historical_value"
                  name="Historical Actual"
                  stroke="#6366f1"
                  strokeWidth={2}
                  dot={{ r: 2 }}
                />
                <Line
                  type="monotone"
                  dataKey="forecast_value"
                  name="Forecast Projection"
                  stroke="#10b981"
                  strokeWidth={2.5}
                  strokeDasharray="4 4"
                  dot={{ r: 3, fill: '#10b981' }}
                />
                <Line
                  type="monotone"
                  dataKey="upper_bound"
                  name="Upper 95% Bound"
                  stroke="#94a3b8"
                  strokeWidth={1}
                  strokeDasharray="2 2"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="lower_bound"
                  name="Lower 95% Bound"
                  stroke="#94a3b8"
                  strokeWidth={1}
                  strokeDasharray="2 2"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Domain Disclaimer */}
      {forecastData?.disclaimer && (
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-400 flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-indigo-400 shrink-0" />
          <span>{forecastData.disclaimer}</span>
        </div>
      )}
    </div>
  );
};
