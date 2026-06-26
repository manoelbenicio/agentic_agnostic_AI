import asyncio
import time
from typing import Dict, Tuple

class Seat:
    """
    Represents an authenticated seat for a specific tenant and vendor.
    Provides credential isolation via a dedicated home_dir.
    """
    def __init__(self, seat_id: str, tenant_id: str, vendor: str, home_dir: str, token_lifetime: float = 3600.0):
        self.seat_id = seat_id
        self.tenant_id = tenant_id
        self.vendor = vendor
        self.home_dir = home_dir
        self.ref_count = 0
        self.token_lifetime = token_lifetime
        self.lease_expiry = 0.0
        self.token = None

    def get_env(self) -> Dict[str, str]:
        """
        Returns isolated environment variables for the process using this seat.
        """
        return {
            "HOME": self.home_dir,
            "SEAT_ID": self.seat_id,
            "VENDOR": self.vendor,
            "TENANT_ID": self.tenant_id,
            "SEAT_TOKEN": self.token or ""
        }

    def refresh_token(self):
        """
        Refreshes the seat's auth token and extends the lease expiry.
        """
        # In a real implementation, this would interact with an Auth provider (OAuth/device-auth).
        self.lease_expiry = time.time() + self.token_lifetime
        self.token = f"token-{self.seat_id}-{time.time()}"

    def release(self):
        """
        Releases one reference. Returns True if fully released (ref_count == 0).
        """
        if self.ref_count > 0:
            self.ref_count -= 1
        return self.ref_count == 0

class SeatPool:
    """
    Manages a pool of seats grouped by tenant and vendor.
    """
    def __init__(self):
        self.pools: Dict[Tuple[str, str], asyncio.Queue] = {}
        self.all_seats: Dict[str, Seat] = {}

    def register_seat(self, seat: Seat):
        """
        Adds a new seat to the pool.
        """
        key = (seat.tenant_id, seat.vendor)
        if key not in self.pools:
            self.pools[key] = asyncio.Queue()
        self.pools[key].put_nowait(seat)
        self.all_seats[seat.seat_id] = seat

    async def acquire(self, tenant_id: str, vendor: str) -> Seat:
        """
        Acquires a seat for a parent agent.
        Queues the task if no seats are currently available.
        """
        key = (tenant_id, vendor)
        if key not in self.pools:
            self.pools[key] = asyncio.Queue()
        
        # Blocks until a seat is available
        seat = await self.pools[key].get()
        seat.ref_count += 1
        
        # Lease affinity and refresh hook logic
        if time.time() >= seat.lease_expiry:
            seat.refresh_token()
            
        return seat

    def acquire_subagent(self, parent_seat: Seat) -> Seat:
        """
        Acquires the same seat for a subagent spawned by the parent.
        Does not consume an extra seat from the pool, just increments ref_count.
        """
        if parent_seat.ref_count <= 0:
            raise RuntimeError(f"Cannot acquire subagent seat for {parent_seat.seat_id}: Parent seat is not actively leased.")
        parent_seat.ref_count += 1
        return parent_seat

    def release(self, seat: Seat):
        """
        Releases a seat. If ref_count reaches 0, it's returned to the available pool.
        """
        fully_released = seat.release()
        if fully_released:
            key = (seat.tenant_id, seat.vendor)
            self.pools[key].put_nowait(seat)
