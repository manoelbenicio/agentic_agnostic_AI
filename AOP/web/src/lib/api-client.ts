// ---------------------------------------------------------------------------
// AOP Control-Plane – Typed Fetch API Client
// ---------------------------------------------------------------------------

import type {
  HealthResponse,
  ReadyResponse,
  Agent,
  AgentCreateRequest,
  SeatsResponse,
  TopologySaveRequest,
  TopologySaveResponse,
  TopologyGetResponse,
  ProjectRollup,
  TraceEvent,
  TaskCreateRequest,
  TaskDispatchResponse,
} from './api-types';

// ---------------------------------------------------------------------------
// Custom Error
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  public readonly status: number;
  public readonly statusText: string;
  public readonly body: unknown;

  constructor(status: number, statusText: string, body: unknown) {
    const message =
      typeof body === 'object' && body !== null && 'detail' in body
        ? String((body as Record<string, unknown>).detail)
        : `API error ${status}: ${statusText}`;
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.statusText = statusText;
    this.body = body;
  }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

export class ApiClient {
  private readonly baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl =
      baseUrl ??
      (typeof process !== 'undefined'
        ? process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8090'
        : 'http://127.0.0.1:8090');
  }

  // ---- internal helpers ---------------------------------------------------

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;

    const headers: Record<string, string> = {
      Accept: 'application/json',
    };

    if (body !== undefined) {
      headers['Content-Type'] = 'application/json';
    }

    const res = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    // For 204 No Content (e.g. DELETE), return an empty object.
    if (res.status === 204) {
      return {} as T;
    }

    let parsed: unknown;
    const contentType = res.headers.get('content-type') ?? '';
    if (contentType.includes('application/json')) {
      parsed = await res.json();
    } else {
      parsed = await res.text();
    }

    if (!res.ok) {
      throw new ApiError(res.status, res.statusText, parsed);
    }

    return parsed as T;
  }

  private get<T>(path: string): Promise<T> {
    return this.request<T>('GET', path);
  }

  private post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>('POST', path, body);
  }

  private del<T>(path: string): Promise<T> {
    return this.request<T>('DELETE', path);
  }

  // ---- Health -------------------------------------------------------------

  async health(): Promise<HealthResponse> {
    return this.get<HealthResponse>('/health');
  }

  async ready(): Promise<ReadyResponse> {
    return this.get<ReadyResponse>('/health/ready');
  }

  // ---- Agents -------------------------------------------------------------

  async listAgents(): Promise<Agent[]> {
    return this.get<Agent[]>('/agents');
  }

  async createAgent(req: AgentCreateRequest): Promise<Agent> {
    return this.post<Agent>('/agents', req);
  }

  async deleteAgent(agentId: string): Promise<void> {
    await this.del<void>(`/agents/${encodeURIComponent(agentId)}`);
  }

  // ---- Seats --------------------------------------------------------------

  async getSeats(): Promise<SeatsResponse> {
    return this.get<SeatsResponse>('/seats');
  }

  // ---- Topology -----------------------------------------------------------

  async saveTopology(
    squadId: string,
    req: TopologySaveRequest,
  ): Promise<TopologySaveResponse> {
    return this.post<TopologySaveResponse>(
      `/squads/${encodeURIComponent(squadId)}/topology`,
      req,
    );
  }

  async getTopology(squadId: string): Promise<TopologyGetResponse> {
    return this.get<TopologyGetResponse>(
      `/squads/${encodeURIComponent(squadId)}/topology`,
    );
  }

  // ---- FinOps -------------------------------------------------------------

  async projectRollup(
    tenantId: string,
    projectId: string,
  ): Promise<ProjectRollup> {
    return this.get<ProjectRollup>(
      `/finops/projects/${encodeURIComponent(tenantId)}/${encodeURIComponent(projectId)}/rollup`,
    );
  }

  // ---- Tracing ------------------------------------------------------------

  async traceAgent(agentId: string): Promise<TraceEvent[]> {
    return this.get<TraceEvent[]>(
      `/tracing/agents/${encodeURIComponent(agentId)}`,
    );
  }

  async traceRuntime(runtimeId: string): Promise<TraceEvent[]> {
    return this.get<TraceEvent[]>(
      `/tracing/runtimes/${encodeURIComponent(runtimeId)}`,
    );
  }

  // ---- Tasks --------------------------------------------------------------

  async createTask(req: TaskCreateRequest): Promise<TaskDispatchResponse> {
    return this.post<TaskDispatchResponse>('/tasks', req);
  }
}

// ---------------------------------------------------------------------------
// Singleton
// ---------------------------------------------------------------------------

export const api = new ApiClient();
