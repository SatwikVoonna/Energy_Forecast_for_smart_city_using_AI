import axios from 'axios';
import type { ForecastResponse, RenewableResponse, AnomalyResponse, MetricsResponse } from '../types/api';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const fetchForecast = async (horizon: number = 24, model: string = 'ensemble'): Promise<ForecastResponse> => {
  const response = await api.get<ForecastResponse>(`/forecast?horizon=${horizon}&model=${model}`);
  return response.data;
};

export const fetchAnomalies = async (): Promise<AnomalyResponse[]> => {
  const response = await api.get<AnomalyResponse[]>('/anomalies');
  return response.data;
};

export const fetchRenewables = async (): Promise<RenewableResponse> => {
  const response = await api.get<RenewableResponse>('/renewables/netload');
  return response.data;
};

export const fetchMetrics = async (): Promise<MetricsResponse> => {
  const response = await api.get<MetricsResponse>('/metrics');
  return response.data;
};
