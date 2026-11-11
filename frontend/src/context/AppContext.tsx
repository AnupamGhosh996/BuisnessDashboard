import React, { createContext, useContext, useState, useEffect } from 'react';
import { api, Dataset, FilterParams } from '../services/api';

interface AppContextType {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  datasets: Dataset[];
  activeDataset: Dataset | null;
  setActiveDataset: (dataset: Dataset) => void;
  filters: FilterParams;
  setFilters: React.Dispatch<React.SetStateAction<FilterParams>>;
  theme: 'dark' | 'light';
  toggleTheme: () => void;
  isLoadingDatasets: boolean;
  refreshDatasets: () => Promise<void>;
  selectDatasetById: (id: number) => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [activeDataset, setActiveDataset] = useState<Dataset | null>(null);
  const [filters, setFilters] = useState<FilterParams>({});
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [isLoadingDatasets, setIsLoadingDatasets] = useState<boolean>(true);

  const refreshDatasets = async () => {
    try {
      setIsLoadingDatasets(true);
      const list = await api.getDatasets();
      setDatasets(list);
      const active = list.find((d) => d.is_active) || list[0] || null;
      setActiveDataset(active);
    } catch (err) {
      console.error('Failed to load datasets:', err);
    } finally {
      setIsLoadingDatasets(false);
    }
  };

  const selectDatasetById = async (id: number) => {
    try {
      await api.selectDataset(id);
      await refreshDatasets();
    } catch (err) {
      console.error('Failed to switch dataset:', err);
    }
  };

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  useEffect(() => {
    refreshDatasets();
  }, []);

  return (
    <AppContext.Provider
      value={{
        activeTab,
        setActiveTab,
        datasets,
        activeDataset,
        setActiveDataset,
        filters,
        setFilters,
        theme,
        toggleTheme,
        isLoadingDatasets,
        refreshDatasets,
        selectDatasetById,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within an AppProvider');
  return context;
};
