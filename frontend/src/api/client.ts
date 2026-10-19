import {
  CreateSessionResponse,
  JobAcceptedResponse,
  JobStatusResponse,
  MediaIngestResponse,
  SessionDetailResponse,
  StepResult,
  ApiError,
} from '../types/api';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export class ApiClientError extends Error {
  code: string;
  retryable: boolean;
  details?: any;

  constructor(message: string, code = 'UNKNOWN_ERROR', retryable = false, details?: any) {
    super(message);
    this.name = 'ApiClientError';
    this.code = code;
    this.retryable = retryable;
    this.details = details;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorData: ApiError | null = null;
    try {
      errorData = await res.json();
    } catch {
      // not JSON
    }
    if (errorData && errorData.error) {
      throw new ApiClientError(
        errorData.error.message || `HTTP ${res.status}`,
        errorData.error.code || 'HTTP_ERROR',
        errorData.error.retryable ?? false,
        errorData.error.details
      );
    }
    throw new ApiClientError(`Request failed with status ${res.status}`);
  }
  return res.json();
}

export const api = {
  async getHealth(): Promise<{ status: string; app: string }> {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse(res);
  },

  async getReady(): Promise<{ status: string; storage: boolean; stt_provider: string }> {
    const res = await fetch(`${API_BASE}/ready`);
    return handleResponse(res);
  },

  async uploadMedia(file: File): Promise<MediaIngestResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/api/v1/media/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<MediaIngestResponse>(res);
  },

  async ingestMediaUrl(url: string): Promise<MediaIngestResponse> {
    const res = await fetch(`${API_BASE}/api/v1/media/ingest-url`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    return handleResponse<MediaIngestResponse>(res);
  },

  async createSession(videoUri: string, idempotencyKey?: string): Promise<CreateSessionResponse> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (idempotencyKey) {
      headers['Idempotency-Key'] = idempotencyKey;
    }

    const res = await fetch(`${API_BASE}/api/v1/sessions`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ video_uri: videoUri }),
    });
    return handleResponse<CreateSessionResponse>(res);
  },

  async getSession(sessionId: string): Promise<SessionDetailResponse> {
    const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}`);
    return handleResponse<SessionDetailResponse>(res);
  },

  async executeStep(
    sessionId: string,
    say: string,
    answer?: string,
    idempotencyKey?: string
  ): Promise<StepResult | JobAcceptedResponse> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (idempotencyKey) {
      headers['Idempotency-Key'] = idempotencyKey;
    }

    const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/steps`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ say, answer }),
    });

    return handleResponse<StepResult | JobAcceptedResponse>(res);
  },

  async triggerRender(sessionId: string, idempotencyKey?: string): Promise<JobAcceptedResponse> {
    const headers: Record<string, string> = {};
    if (idempotencyKey) {
      headers['Idempotency-Key'] = idempotencyKey;
    }

    const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/render`, {
      method: 'POST',
      headers,
    });
    return handleResponse<JobAcceptedResponse>(res);
  },

  async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    const res = await fetch(`${API_BASE}/api/v1/jobs/${jobId}`);
    return handleResponse<JobStatusResponse>(res);
  },

  async exportOTIO(sessionId: string): Promise<{ status: string; file_path: string; filename: string }> {
    const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/export-otio`);
    return handleResponse(res);
  },
};
