"""Shared subscription quota and burn-rate forecasting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True, slots=True)
class QuotaSnapshot:
    """Current shared quota position for one vendor."""

    vendor: str
    five_hour_cap_seconds: int = 5 * 60 * 60
    weekly_cap_seconds: int = 5 * 60 * 60
    used_five_hour_seconds: int = 0
    used_weekly_seconds: int = 0
    measured_at: datetime | None = None

    @property
    def five_hour_remaining_seconds(self) -> int:
        """Remaining burn in the rolling five-hour window."""
        return max(0, self.five_hour_cap_seconds - self.used_five_hour_seconds)

    @property
    def weekly_remaining_seconds(self) -> int:
        """Remaining burn in the weekly shared subscription cap."""
        return max(0, self.weekly_cap_seconds - self.used_weekly_seconds)

    @property
    def effective_remaining_seconds(self) -> int:
        """Dispatchable burn constrained by the tightest cap."""
        return min(self.five_hour_remaining_seconds, self.weekly_remaining_seconds)


@dataclass(frozen=True, slots=True)
class BurnForecast:
    """Forecast of when a vendor quota will be exhausted."""

    vendor: str
    burn_rate_seconds_per_hour: float
    hours_until_exhaustion: float | None
    will_exhaust_within_24h: bool


class QuotaLedger:
    """In-memory quota ledger for shared vendor subscription burn."""

    def __init__(self, snapshots: dict[str, QuotaSnapshot] | None = None) -> None:
        """Create a ledger keyed by vendor."""
        self._snapshots = dict(snapshots or {})

    def set_snapshot(self, snapshot: QuotaSnapshot) -> None:
        """Replace the tracked quota snapshot for a vendor."""
        self._snapshots[snapshot.vendor] = snapshot

    def snapshot(self, vendor: str) -> QuotaSnapshot:
        """Return a vendor snapshot, defaulting to an unused 5-hour cap."""
        return self._snapshots.get(vendor, QuotaSnapshot(vendor=vendor))

    def has_headroom(self, vendor: str, estimated_seconds: int) -> bool:
        """Return True when the shared cap can admit the estimated burn."""
        return self.snapshot(vendor).effective_remaining_seconds >= max(0, estimated_seconds)

    def reserve(self, vendor: str, estimated_seconds: int) -> QuotaSnapshot:
        """Reserve estimated burn against both five-hour and weekly windows."""
        current = self.snapshot(vendor)
        burn = max(0, estimated_seconds)
        updated = QuotaSnapshot(
            vendor=vendor,
            five_hour_cap_seconds=current.five_hour_cap_seconds,
            weekly_cap_seconds=current.weekly_cap_seconds,
            used_five_hour_seconds=current.used_five_hour_seconds + burn,
            used_weekly_seconds=current.used_weekly_seconds + burn,
            measured_at=datetime.now(timezone.utc),
        )
        self.set_snapshot(updated)
        return updated

    def forecast(
        self,
        vendor: str,
        *,
        observed_burn_seconds: int,
        observed_window: timedelta,
    ) -> BurnForecast:
        """Forecast quota exhaustion from observed burn over a time window."""
        hours = max(observed_window.total_seconds() / 3600.0, 0.001)
        burn_rate = max(0, observed_burn_seconds) / hours
        remaining = self.snapshot(vendor).weekly_remaining_seconds
        hours_until = None if burn_rate == 0 else remaining / burn_rate
        return BurnForecast(
            vendor=vendor,
            burn_rate_seconds_per_hour=burn_rate,
            hours_until_exhaustion=hours_until,
            will_exhaust_within_24h=hours_until is not None and hours_until <= 24,
        )

