import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { Sidebar } from './layouts/Sidebar';
import { Header } from './layouts/Header';

import { OverviewPage } from './pages/OverviewPage';
import { UploadPage } from './pages/UploadPage';
import { DataExplorerPage } from './pages/DataExplorerPage';
import { CleaningPage } from './pages/CleaningPage';
import { EDAPage } from './pages/EDAPage';
import { DashboardPage } from './pages/DashboardPage';
import { AIAnalystPage } from './pages/AIAnalystPage';
import { AnomalyPage } from './pages/AnomalyPage';
import { ForecastingPage } from './pages/ForecastingPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';

const pageMeta: Record<string, { title: string; subtitle: string }> = {
  overview: {
    title: 'Executive Overview',
    subtitle: 'High-level business performance metrics and real-time operational status',
  },
  upload: {
    title: 'Data Upload & Management',
    subtitle: 'Upload CSV and Excel datasets with automated schema extraction',
  },
  explorer: {
    title: 'Data Explorer',
    subtitle: 'Interactive dataset inspector, column filter, and sorting grid',
  },
  cleaning: {
    title: 'Automated Data Cleaning',
    subtitle: 'Deduplication, missing value imputation, and non-destructive dataset cloning',
  },
  eda: {
    title: 'Exploratory Data Analysis (EDA)',
    subtitle: 'Statistical distributions, Pearson correlation matrices, and automated findings',
  },
  dashboard: {
    title: 'Interactive BI Dashboard',
    subtitle: 'Dynamic KPI metrics, time-series trends, and multi-dimensional segment filters',
  },
  ai: {
    title: 'AI Data Analyst',
    subtitle: 'Ask natural language analytical questions verified by deterministic calculations',
  },
  anomaly: {
    title: 'Anomaly Detection',
    subtitle: 'Multivariate statistical & Isolation Forest outlier detection',
  },
  forecasting: {
    title: 'Business & Sales Forecasting',
    subtitle: 'Predictive time-series regression and exponential smoothing with confidence intervals',
  },
  reports: {
    title: 'AI Business Reports',
    subtitle: 'Generate C-suite analytical summaries and export to PDF, Excel, or CSV',
  },
  settings: {
    title: 'Platform Settings',
    subtitle: 'Anthropic Claude API credentials, database settings, and system health',
  },
};

const DashboardContent: React.FC = () => {
  const { activeTab, theme } = useApp();
  const currentMeta = pageMeta[activeTab] || pageMeta.overview;

  const renderActivePage = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewPage />;
      case 'upload':
        return <UploadPage />;
      case 'explorer':
        return <DataExplorerPage />;
      case 'cleaning':
        return <CleaningPage />;
      case 'eda':
        return <EDAPage />;
      case 'dashboard':
        return <DashboardPage />;
      case 'ai':
        return <AIAnalystPage />;
      case 'anomaly':
        return <AnomalyPage />;
      case 'forecasting':
        return <ForecastingPage />;
      case 'reports':
        return <ReportsPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <OverviewPage />;
    }
  };

  return (
    <div className={`flex h-screen overflow-hidden ${theme === 'dark' ? 'dark bg-[#090d16]' : 'bg-slate-50'}`}>
      <Sidebar />
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        <Header title={currentMeta.title} subtitle={currentMeta.subtitle} />
        <main className="flex-1 overflow-y-auto p-8">
          {renderActivePage()}
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AppProvider>
      <DashboardContent />
    </AppProvider>
  );
};

export default App;
