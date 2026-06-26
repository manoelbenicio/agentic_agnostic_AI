"use client";

export const API_URL = (
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8090"
).replace(/\/$/, "");

export const WS_URL = API_URL.replace(/^http/, "ws");

export type HealthResponse = { status: string };

export type Agent = {
  agent_id: string;
  tenant_id: string;
  label: string;
  vendor: string;
  role: string;
  status: string;
  workspace_id?: string | null;
  pane_id?: string | null;
  stable_key?: string | null;
  metadata?: Record<string, unknown>;
};

export type Seat = {
  seat_id: string;
  tenant_id: string;
  vendor: string;
  leased: boolean;
  ref_count: number;
};

export type FinOpsRollup = {
  tenant_id: string;
  project_id: string;
  total_cost_usd: string;
  token_cost_usd: string;
  seat_cost_usd: string;
  record_count: number;
};

export type TraceEvent = {
  event_id: string;
  trace_id: string;
  layer: string;
  signal_type: string;
  tenant_id: string;
  project_id: string;
  issue_id: string;
  agent_id: string;
  runtime_id: string;
  message: string;
  token_burn: number;
  seat_seconds: number;
  details: Record<string, unknown>;
};

export type TopologyNode = {
  id: string;
  role: string;
  label?: string;
};

export type TopologyEdge = {
  source: string;
  target: string;
};

export type StoredTopology = {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
};

export type TopologyResponse = {
  squad_id: string;
  stored?: StoredTopology | null;
  effective_topology?: {
    default_policy: string;
    roles: Array<{
      name: string;
      agents: string[];
      can_send_to: string[];
      can_receive_from: string[];
      can_dispatch_tasks: boolean;
      can_reassign_tasks: boolean;
    }>;
  };
};

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`${response.status} ${response.statusText}${text ? `: ${text}` : ""}`);
  }

  return (await response.json()) as T;
}

export const api = {
  health: () => apiFetch<HealthResponse>("/health"),
  agents: () => apiFetch<Agent[]>("/agents"),
  seats: async () => (await apiFetch<{ seats: Seat[] }>("/seats")).seats,
  topology: (squadId: string) =>
    apiFetch<TopologyResponse>(`/squads/${encodeURIComponent(squadId)}/topology`),
  saveTopology: (squadId: string, nodes: TopologyNode[], edges: TopologyEdge[]) =>
    apiFetch<TopologyResponse>(`/squads/${encodeURIComponent(squadId)}/topology`, {
      method: "POST",
      body: JSON.stringify({ nodes, edges }),
    }),
  finopsRollup: (tenantId = "tenant-a", projectId = "project-a") =>
    apiFetch<FinOpsRollup>(
      `/finops/projects/${encodeURIComponent(tenantId)}/${encodeURIComponent(projectId)}/rollup`,
    ),
  traceAgent: (agentId: string) =>
    apiFetch<TraceEvent[]>(`/tracing/agents/${encodeURIComponent(agentId)}`),
};

export function traceAgentWebSocketUrl(agentId: string) {
  return `${WS_URL}/ws/tracing/agents/${encodeURIComponent(agentId)}`;
}
