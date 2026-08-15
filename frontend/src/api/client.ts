/**
 * Centralized, typed API client for Enterprise AI Investigation backend.
 */

import type {
  BackendHealthResponse,
  FullInvestigationResponse,
  InvestigationRequestPayload,
  ScenarioItem,
} from './types';

// Default to backend on 8000 during local dev, or proxy/env override
const DEFAULT_API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  (typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : '/api');

export class ApiError extends Error {
  status: number;
  data?: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  timeoutMs = 45000
): Promise<T> {
  const url = `${DEFAULT_API_BASE.replace(/\/$/, '')}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        ...(options.headers || {}),
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
      let errorData: unknown;
      try {
        errorData = await response.json();
        if (errorData && typeof errorData === 'object' && 'detail' in errorData) {
          errorMessage = String((errorData as { detail: unknown }).detail);
        }
      } catch {
        // use fallback text
      }
      throw new ApiError(errorMessage, response.status, errorData);
    }

    const json = (await response.json()) as T;
    return json;
  } catch (err: unknown) {
    clearTimeout(timeoutId);
    if (err instanceof ApiError) {
      throw err;
    }
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError(`Request timed out after ${timeoutMs / 1000}s`, 408);
    }
    const message = err instanceof Error ? err.message : 'Unknown network connection failure';
    throw new ApiError(`Failed to connect to backend server: ${message}`, 0, err);
  }
}

export const apiClient = {
  /**
   * Check backend service status.
   */
  async checkHealth(): Promise<BackendHealthResponse> {
    return request<BackendHealthResponse>('/health', { method: 'GET' }, 5000);
  },

  /**
   * Fetch predefined investigation benchmark scenarios.
   */
  async fetchScenarios(): Promise<ScenarioItem[]> {
    return request<ScenarioItem[]>('/investigations/scenarios', { method: 'GET' }, 10000);
  },

  /**
   * Run an end-to-end investigation with planning, tool dispatch, evidence collection, and grounded synthesis.
   */
  async runInvestigation(payload: InvestigationRequestPayload): Promise<FullInvestigationResponse> {
    return request<FullInvestigationResponse>(
      '/investigations/investigate',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      60000
    );
  },

  /**
   * Fetch latest evaluation benchmark report.
   */
  async fetchLatestEvaluation(): Promise<Record<string, unknown>> {
    return request<Record<string, unknown>>('/investigations/evaluation/latest', { method: 'GET' }, 10000);
  },
};
