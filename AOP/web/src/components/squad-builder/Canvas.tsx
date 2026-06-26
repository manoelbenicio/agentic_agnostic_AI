"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  ReactFlow,
  useNodesState,
  useEdgesState,
  addEdge,
  MiniMap,
  Controls,
  Background,
  type Connection,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { api } from "@/lib/api-client";
import type { Agent, Seat } from "@/lib/api-types";
import {
  Download,
  Loader2,
  Plus,
  Save,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";

const SQUAD_ID = "default";

type SaveState = "idle" | "saving" | "saved" | "error";
type SquadNodeData = Record<string, unknown> & {
  label: string;
  role: string;
};
type SquadNode = Node<SquadNodeData>;

export default function Canvas() {
  const [nodes, setNodes, onNodesChange] = useNodesState<SquadNode>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [seats, setSeats] = useState<Seat[]>([]);
  const [loading, setLoading] = useState(true);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [loadError, setLoadError] = useState<string | null>(null);

  // Load topology + agents on mount
  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setLoadError(null);
      try {
        const [topoRes, agentList, seatRes] = await Promise.all([
          api.getTopology(SQUAD_ID).catch(() => null),
          api.listAgents().catch(() => [] as Agent[]),
          api.getSeats().catch(() => ({ seats: [] as Seat[] })),
        ]);

        if (cancelled) return;
        setAgents(agentList);
        setSeats(seatRes.seats);

        // If topology has stored nodes/edges, use them
        const stored = topoRes?.stored as {
          nodes?: Array<Record<string, unknown>>;
          edges?: Array<Record<string, unknown>>;
        } | null;
        if (stored?.nodes && stored.nodes.length > 0) {
          setNodes(normalizeStoredNodes(stored.nodes, agentList));
          setEdges(normalizeStoredEdges(stored.edges ?? []));
        } else {
          // Generate initial canvas from registered agents
          const initialNodes: SquadNode[] = agentList.map((agent, i) => ({
            id: agent.agent_id,
            position: {
              x: 150 + (i % 3) * 250,
              y: 80 + Math.floor(i / 3) * 150,
            },
            data: {
              label: `${agent.label} (${agent.vendor})`,
              role: agent.role,
            },
          }));
          setNodes(initialNodes);
          setEdges([]);
        }
      } catch (err) {
        if (!cancelled)
          setLoadError(
            err instanceof Error ? err.message : "Failed to load topology",
          );
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Connection | Edge) =>
      setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  // Save topology
  const handleSave = useCallback(async () => {
    setSaveState("saving");
    try {
      const nodeData = nodes.map((n) => ({
        id: n.id,
        label: String((n.data as Record<string, unknown>).label ?? n.id),
        role: String((n.data as Record<string, unknown>).role ?? "worker"),
        x: String(n.position.x),
        y: String(n.position.y),
      }));
      const edgeData = edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
      }));
      await api.saveTopology(SQUAD_ID, {
        nodes: nodeData,
        edges: edgeData,
      });
      setSaveState("saved");
      setTimeout(() => setSaveState("idle"), 2000);
    } catch {
      setSaveState("error");
      setTimeout(() => setSaveState("idle"), 3000);
    }
  }, [nodes, edges]);

  // Add agent node that isn't on canvas yet
  const handleAddAgent = useCallback(
    (agent: Agent) => {
      const exists = nodes.some((n) => n.id === agent.agent_id);
      if (exists) return;
      const newNode: SquadNode = {
        id: agent.agent_id,
        position: {
          x: 200 + Math.random() * 200,
          y: 100 + Math.random() * 200,
        },
        data: { label: `${agent.label} (${agent.vendor})`, role: agent.role },
      };
      setNodes((nds) => [...nds, newNode]);
    },
    [nodes, setNodes],
  );

  const unplacedAgents = agents.filter(
    (a) => !nodes.some((n) => n.id === a.agent_id),
  );

  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center rounded-lg border border-border bg-card">
        <div className="flex items-center gap-3 text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
          <span className="text-sm">Loading topology…</span>
        </div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="flex h-[80vh] flex-col items-center justify-center rounded-lg border border-destructive/30 bg-destructive/5">
        <AlertCircle className="mb-3 size-8 text-destructive" />
        <p className="text-sm font-medium text-destructive">
          Failed to load topology
        </p>
        <p className="mt-1 text-xs text-muted-foreground">{loadError}</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-3">
          {/* Toolbar */}
          <div className="flex items-center justify-between rounded-lg border border-border bg-card px-4 py-2">
            <div className="flex items-center gap-2">
              {unplacedAgents.length > 0 && (
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-muted-foreground">
                    Add agent:
                  </span>
                  {unplacedAgents.map((agent) => (
                    <button
                      key={agent.agent_id}
                      onClick={() => handleAddAgent(agent)}
                      className="flex items-center gap-1 rounded-md border border-border bg-background px-2 py-1 text-xs transition-colors hover:bg-accent"
                    >
                      <Plus className="size-3" />
                      {agent.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button
              onClick={handleSave}
              disabled={saveState === "saving"}
              className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-xs font-medium shadow-sm transition-all ${
                saveState === "saved"
                  ? "bg-success/10 text-success border border-success/30"
                  : saveState === "error"
                    ? "bg-destructive/10 text-destructive border border-destructive/30"
                    : "bg-primary text-primary-foreground hover:bg-primary/90"
              }`}
            >
              {saveState === "saving" ? (
                <Loader2 className="size-3.5 animate-spin" />
              ) : saveState === "saved" ? (
                <CheckCircle2 className="size-3.5" />
              ) : saveState === "error" ? (
                <AlertCircle className="size-3.5" />
              ) : (
                <Save className="size-3.5" />
              )}
              {saveState === "saving"
                ? "Saving…"
                : saveState === "saved"
                  ? "Saved!"
                  : saveState === "error"
                    ? "Save failed"
                    : "Save Topology"}
            </button>
          </div>

          {/* Canvas */}
          <div
            style={{ width: "100%", height: "75vh" }}
            className="overflow-hidden rounded-lg border border-border"
          >
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              fitView
            >
              <Controls />
              <MiniMap />
              <Background gap={12} size={1} />
            </ReactFlow>
          </div>
        </div>

        <aside className="space-y-3">
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="text-sm font-semibold">Registry</div>
            <div className="mt-3 space-y-2">
              {agents.length ? agents.map((agent) => (
                <div key={agent.agent_id} className="rounded-md border border-border p-3 text-sm">
                  <div className="font-medium">{agent.label}</div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    {agent.vendor} | {agent.role} | {agent.status}
                  </div>
                </div>
              )) : <div className="text-sm text-muted-foreground">No agents returned.</div>}
            </div>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="text-sm font-semibold">Seats</div>
            <div className="mt-3 space-y-2">
              {seats.length ? seats.map((seat) => (
                <div key={seat.seat_id} className="flex items-center justify-between gap-3 text-sm">
                  <span className="truncate">{seat.seat_id}</span>
                  <span className="text-xs text-muted-foreground">{seat.vendor} / {seat.ref_count}</span>
                </div>
              )) : <div className="text-sm text-muted-foreground">No seats returned.</div>}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

function normalizeStoredNodes(items: Array<Record<string, unknown>>, agents: Agent[]): SquadNode[] {
  const byId = new Map(agents.map((agent) => [agent.agent_id, agent]));
  return items.map((item, index) => {
    const id = String(item.id ?? `node-${index + 1}`);
    const agent = byId.get(id);
    return {
      id,
      position: {
        x: Number(item.x ?? 150 + (index % 3) * 250),
        y: Number(item.y ?? 80 + Math.floor(index / 3) * 150),
      },
      data: {
        label: String(item.label ?? agent?.label ?? id),
        role: String(item.role ?? agent?.role ?? "worker"),
      },
    };
  });
}

function normalizeStoredEdges(items: Array<Record<string, unknown>>): Edge[] {
  return items
    .filter((item) => item.source && item.target)
    .map((item, index) => ({
      id: String(item.id ?? `${item.source}-${item.target}-${index}`),
      source: String(item.source),
      target: String(item.target),
      animated: true,
    }));
}
