/**
 * NIFTY API client — thin fetch wrapper over the Phase 1–3 backend.
 * Same base-URL resolution as src/api/client.ts; no logic, no LLM, no computation.
 */

import type {
  NiftyExperimentIntent,
  NiftyExplainRequest,
  NiftyExplainResponse,
  NiftyInterpretResponse,
  NiftyRunResponse,
} from './types';

const NIFTY_API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  (typeof window !== 'undefined' && (window.location.port === '5173' || window.location.port === '3000')
    ? 'http://localhost:8000'
    : '');

export class NiftyApiError extends Error {
  status: number;
  data?: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = 'NiftyApiError';
    this.status = status;
    this.data = data;
  }
}

async function niftyRequest<T>(endpoint: string, body: unknown, timeoutMs = 45000): Promise<T> {
  const url = `${NIFTY_API_BASE.replace(/\/$/, '')}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      method: 'POST',
      signal: controller.signal,
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(body),
    });
    clearTimeout(timeoutId);
    if (!response.ok) {
      let message = `HTTP Error ${response.status}: ${response.statusText}`;
      let data: unknown;
      try {
        data = await response.json();
        if (data && typeof data === 'object' && 'detail' in data) {
          const detail = (data as { detail: unknown }).detail;
          message = typeof detail === 'string' ? detail : JSON.stringify(detail);
        }
      } catch {
        // keep fallback message
      }
      throw new NiftyApiError(message, response.status, data);
    }
    return (await response.json()) as T;
  } catch (err: unknown) {
    clearTimeout(timeoutId);
    if (err instanceof NiftyApiError) throw err;
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new NiftyApiError(`Request timed out after ${timeoutMs / 1000}s`, 408);
    }
    const message = err instanceof Error ? err.message : 'Unknown network failure';
    throw new NiftyApiError(`Failed to reach NIFTY backend: ${message}`, 0, err);
  }
}

export const niftyApi = {
  interpret(question: string): Promise<NiftyInterpretResponse> {
    return niftyRequest<NiftyInterpretResponse>('/api/interpret', { question }, 15000);
  },
  validateExperiment(intent: NiftyExperimentIntent): Promise<NiftyExperimentIntent> {
    return niftyRequest<NiftyExperimentIntent>('/api/experiment', intent, 15000);
  },
  run(intent: NiftyExperimentIntent): Promise<NiftyRunResponse> {
    return niftyRequest<NiftyRunResponse>('/api/run', intent, 60000);
  },
  explain(facts: NiftyExplainRequest): Promise<NiftyExplainResponse> {
    return niftyRequest<NiftyExplainResponse>('/api/explain', facts, 15000);
  },
};
