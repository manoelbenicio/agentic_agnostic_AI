"use client";

import { useAgents } from "@/lib/hooks";
import { LiveTracePanel } from "@/components/live/LiveTracePanel";
import { Brain, Radio, Loader2 } from "lucide-react";
import { useState } from "react";

export default function LivePage() {
  const { agents, loading, error } = useAgents();
  const [selectedAgentIds, setSelectedAgentIds] = useState<string[]>([]);

  function toggleAgent(agentId: string) {
    setSelectedAgentIds((prev) =>
      prev.includes(agentId)
        ? prev.filter((id) => id !== agentId)
        : [...prev, agentId],
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="mb-1 inline-flex items-center gap-2 rounded-md border border-border bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
          <Radio className="size-3.5 animate-pulse text-success" />
          Live Tracing
        </div>
        <h1 className="text-2xl font-semibold tracking-normal text-foreground">
          Agent Live Panel
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
          Real-time chain-of-thought, state transitions, and individual token
          burn streamed via WebSocket. Select agents to observe.
        </p>
      </div>

      {/* Agent selector */}
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Select Agents to Monitor
        </div>
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading agents…
          </div>
        ) : error ? (
          <p className="text-sm text-destructive">{error}</p>
        ) : agents.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No agents registered. Start the control-plane and register agents to
            begin monitoring.
          </p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {agents.map((agent) => {
              const active = selectedAgentIds.includes(agent.agent_id);
              return (
                <button
                  key={agent.agent_id}
                  onClick={() => toggleAgent(agent.agent_id)}
                  className={`flex items-center gap-2 rounded-md border px-3 py-2 text-sm transition-all ${
                    active
                      ? "border-primary bg-primary/10 text-primary shadow-sm"
                      : "border-border bg-background text-muted-foreground hover:border-primary/40 hover:bg-primary/5"
                  }`}
                >
                  <Brain className="size-3.5" />
                  <span className="font-medium">{agent.label}</span>
                  <span className="text-[10px] opacity-60">
                    ({agent.vendor})
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Live panels */}
      {selectedAgentIds.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border bg-card/50 p-12 text-center">
          <Radio className="mx-auto mb-3 size-10 text-muted-foreground/30" />
          <p className="text-sm text-muted-foreground">
            Select one or more agents above to start streaming their trace
            events.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {selectedAgentIds.map((agentId) => {
            const agent = agents.find((a) => a.agent_id === agentId);
            return (
              <LiveTracePanel
                key={agentId}
                agentId={agentId}
                agentLabel={agent?.label}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
