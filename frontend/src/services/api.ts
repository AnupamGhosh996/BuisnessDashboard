const API_BASE = '/api';

export interface Dataset {
  id: number;
  filename: str;
  row_count: number;
  column_count: number;
  file_size_bytes: number;
  is_active: boolean;
  is_cleaned: boolean;
  parent_id?: number;
  uploaded_at: string;
  column_names: string[];
  detected_mappings: Record<string, string>;
}

export interface KPICardData {
  id: string;
  label: string;
  value: number;
  formatted_value: string;
  change_pct?: number;
  subtext?: string;
  icon?: string;
}

export interface OverviewData {
  dataset_id: number;
  filename: string;
  row_count: number;
  column_count: number;
  kpis: KPICardData[];
  date_range?: { start: string; end: string };
  categories: string[];
  regions: string[];
  products_count: number;
  customers_count: number;
  auto_summary: string;
}

export interface FilterParams {
  start_date?: string;
  end_date?: string;
  category?: string[];
  region?: string[];
  product?: string[];
}

export const api = {
  // Datasets
  async getDatasets(): Promise<Dataset[]> {
    const res = await fetch(`${API_BASE}/datasets`);
    if (!res.ok) throw new Error('Failed to fetch datasets');
    return res.json();
  },

  async uploadDataset(file: File): Promise<Dataset> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/datasets/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async selectDataset(id: number): Promise<void> {
    const res = await fetch(`${API_BASE}/datasets/${id}/select`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to set active dataset');
  },

  async deleteDataset(id: number): Promise<void> {
    const res = await fetch(`${API_BASE}/datasets/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete dataset');
  },

  async getPreview(id: number, page = 1, pageSize = 25, search = '', sortBy = '', sortOrder = 'asc'): Promise<any> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      sort_order: sortOrder,
    });
    if (search) params.append('search', search);
    if (sortBy) params.append('sort_by', sortBy);
    const res = await fetch(`${API_BASE}/datasets/${id}?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch preview');
    return res.json();
  },

  // Analysis
  async getOverview(id: number, filters?: FilterParams): Promise<OverviewData> {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    filters?.category?.forEach((c) => params.append('category', c));
    filters?.region?.forEach((r) => params.append('region', r));
    const res = await fetch(`${API_BASE}/analysis/${id}/overview?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch overview');
    return res.json();
  },

  async getStatistics(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/analysis/${id}/statistics`);
    if (!res.ok) throw new Error('Failed to fetch statistics');
    return res.json();
  },

  async getCorrelations(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/analysis/${id}/correlations`);
    if (!res.ok) throw new Error('Failed to fetch correlations');
    return res.json();
  },

  async getCharts(id: number, filters?: FilterParams): Promise<any> {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    filters?.category?.forEach((c) => params.append('category', c));
    filters?.region?.forEach((r) => params.append('region', r));
    const res = await fetch(`${API_BASE}/analysis/${id}/charts?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch charts');
    return res.json();
  },

  // Cleaning
  async previewCleaning(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/cleaning/${id}/preview`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to preview cleaning');
    return res.json();
  },

  async applyCleaning(id: number, payload: any): Promise<any> {
    const res = await fetch(`${API_BASE}/cleaning/${id}/apply`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to apply cleaning');
    return res.json();
  },

  // AI Analyst
  async sendChatMessage(datasetId: number, message: string, conversationId?: number): Promise<any> {
    const res = await fetch(`${API_BASE}/ai/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dataset_id: datasetId, message, conversation_id: conversationId }),
    });
    if (!res.ok) throw new Error('Failed to communicate with AI analyst');
    return res.json();
  },

  async getSuggestions(datasetId: number): Promise<string[]> {
    const res = await fetch(`${API_BASE}/ai/suggestions/${datasetId}`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.suggestions || [];
  },

  async getChatHistory(conversationId: number): Promise<any> {
    const res = await fetch(`${API_BASE}/ai/history/${conversationId}`);
    if (!res.ok) throw new Error('Failed to load history');
    return res.json();
  },

  // Anomaly Detection
  async detectAnomalies(datasetId: number, method = 'isolation_forest', metricColumn?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/anomaly/${datasetId}/detect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ method, metric_column: metricColumn }),
    });
    if (!res.ok) throw new Error('Failed to detect anomalies');
    return res.json();
  },

  // Forecasting
  async getForecast(datasetId: number, horizonDays = 30, method = 'linear', metricColumn?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/forecast/${datasetId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ horizon_days: horizonDays, method, metric_column: metricColumn }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Forecast failed' }));
      throw new Error(err.detail || 'Forecast calculation failed');
    }
    return res.json();
  },

  // Reports
  async generateReport(datasetId: number, reportType: string, format = 'pdf', title?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/reports/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dataset_id: datasetId, report_type: reportType, format, title }),
    });
    if (!res.ok) throw new Error('Failed to generate report');
    return res.json();
  },

  async getReports(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/reports`);
    if (!res.ok) return [];
    return res.json();
  },

  // Health
  async getHealth(): Promise<any> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },
};
