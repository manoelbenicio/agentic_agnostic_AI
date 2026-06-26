"""Prometheus text export for FinOps metrics."""

from __future__ import annotations

from .repository import FinOpsRepository


class FinOpsMetricsExporter:
    """Expose FinOps metrics for the existing Prometheus stack to scrape."""

    def __init__(self, repository: FinOpsRepository) -> None:
        self.repository = repository

    def project_metrics(self, *, tenant_id: str, project_id: str) -> str:
        """Return Prometheus text for one tenant/project rollup."""
        rollup = self.repository.rollup_project(tenant_id, project_id)
        labels = f'tenant_id="{tenant_id}",project_id="{project_id}"'
        lines = [
            "# HELP aop_finops_project_cost_usd Project cost by engine",
            "# TYPE aop_finops_project_cost_usd gauge",
            f'aop_finops_project_cost_usd{{{labels},engine="total"}} {rollup.total_cost_usd}',
            f'aop_finops_project_cost_usd{{{labels},engine="token"}} {rollup.token_cost_usd}',
            f'aop_finops_project_cost_usd{{{labels},engine="seat"}} {rollup.seat_cost_usd}',
            "# HELP aop_finops_project_cost_records Cost record count",
            "# TYPE aop_finops_project_cost_records gauge",
            f"aop_finops_project_cost_records{{{labels}}} {rollup.record_count}",
        ]
        return "\n".join(lines) + "\n"
