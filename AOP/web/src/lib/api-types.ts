// ---------------------------------------------------------------------------
// AOP Control-Plane – API Type Contracts
// ---------------------------------------------------------------------------

// Health -------------------------------------------------------------------

export interface HealthResponse {
  status: string;
}

export interface ReadyResponse {
  status: string;
  checks: {
    postgres: boolean;
    redis: boolean;
  };
}

// Agent --------------------------------------------------------------------

export interface Agent {
  agent_id: string;
  tenant_id: string;
  label: string;
  vendor: string;
  role: string;
  status: string;
  workspace_id: string | null;
  pane_id: string | null;
  stable_key: string | null;
  metadata: Record<string, unknown>;
}

export interface AgentCreateRequest {
  tenant_id: string;
  label: string;
  vendor: string;
  role: string;
  workspace_id?: string | null;
  pane_id?: string | null;
  stable_key?: string | null;
  metadata?: Record<string, unknown>;
}

// Seat ---------------------------------------------------------------------

export interface Seat {
  seat_id: string;
  tenant_id: string;
  vendor: string;
  leased: boolean;
  ref_count: number;
}

export interface SeatsResponse {
  seats: Seat[];
}

// Topology -----------------------------------------------------------------

export interface TopologyNode {
  [key: string]: string;
}

export interface TopologyEdge {
  [key: string]: string;
}

export interface TopologySaveRequest {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
}

export interface AclRole {
  name: string;
  agents: string[];
  can_send_to: string[];
  can_receive_from: string[];
  can_dispatch_tasks: boolean;
  can_reassign_tasks: boolean;
}

export interface TopologySaveResponse {
  squad_id: string;
  effective_topology: {
    default_policy: string;
    roles: AclRole[];
  };
}

export interface TopologyGetResponse {
  squad_id: string;
  stored: unknown;
}

// FinOps -------------------------------------------------------------------

export interface ProjectRollup {
  tenant_id: string;
  project_id: string;
  total_cost_usd: string;
  token_cost_usd: string;
  seat_cost_usd: string;
  record_count: number;
}

// Tracing ------------------------------------------------------------------

export interface TraceEvent {
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
}

// Task ---------------------------------------------------------------------

export interface TaskCreateRequest {
  task_id: string;
  tenant_id: string;
  project_id: string;
  issue_id?: string;
  assignee_runtime: string;
  prompt: string;
  credential_ref?: string;
  operation_mode: 'terminal' | 'socket';
  seat_seconds?: number;
}

export interface TaskDispatchResponse {
  task_id: string;
  operation_mode: 'terminal' | 'socket';
  events: Record<string, unknown>[];
}
