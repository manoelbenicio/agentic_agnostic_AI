import asyncio
import pytest
from ..pool import Seat, SeatPool

@pytest.fixture
def seat_pool():
    return SeatPool()

@pytest.mark.asyncio
async def test_acquire_and_release(seat_pool):
    seat = Seat("s1", "tenant_a", "vendor_x", "/tmp/home_s1")
    seat_pool.register_seat(seat)
    
    acquired_seat = await asyncio.wait_for(seat_pool.acquire("tenant_a", "vendor_x"), timeout=1.0)
    assert acquired_seat.seat_id == "s1"
    assert acquired_seat.ref_count == 1
    assert "token-" in acquired_seat.token  # Token should have been refreshed on first acquire
    
    seat_pool.release(acquired_seat)
    assert acquired_seat.ref_count == 0
    
    # Should be able to acquire again
    acquired_seat_2 = await asyncio.wait_for(seat_pool.acquire("tenant_a", "vendor_x"), timeout=1.0)
    assert acquired_seat_2.seat_id == "s1"

@pytest.mark.asyncio
async def test_queueing_when_no_seats_available(seat_pool):
    seat = Seat("s1", "tenant_a", "vendor_x", "/tmp/home_s1")
    seat_pool.register_seat(seat)
    
    # Acquire the only seat
    seat1 = await seat_pool.acquire("tenant_a", "vendor_x")
    
    # Try to acquire another, should block
    acquire_task = asyncio.create_task(seat_pool.acquire("tenant_a", "vendor_x"))
    
    done, pending = await asyncio.wait([acquire_task], timeout=0.1)
    assert not done  # It is blocked
    
    # Release the seat
    seat_pool.release(seat1)
    
    # Now it should unblock
    seat2 = await asyncio.wait_for(acquire_task, timeout=1.0)
    assert seat2.seat_id == "s1"

@pytest.mark.asyncio
async def test_subagent_inherits_seat(seat_pool):
    seat = Seat("s1", "tenant_a", "vendor_x", "/tmp/home_s1")
    seat_pool.register_seat(seat)
    
    parent_seat = await seat_pool.acquire("tenant_a", "vendor_x")
    assert parent_seat.ref_count == 1
    
    subagent_seat = seat_pool.acquire_subagent(parent_seat)
    assert subagent_seat.seat_id == "s1"
    assert subagent_seat.ref_count == 2
    
    # Releasing parent shouldn't make seat available yet
    seat_pool.release(parent_seat)
    assert subagent_seat.ref_count == 1
    
    # Releasing subagent makes it available
    seat_pool.release(subagent_seat)
    assert subagent_seat.ref_count == 0
    
    # Can acquire again
    new_seat = await asyncio.wait_for(seat_pool.acquire("tenant_a", "vendor_x"), timeout=1.0)
    assert new_seat.seat_id == "s1"

def test_credential_isolation_env():
    seat1 = Seat("s1", "tenant_a", "vendor_x", "/tmp/home_s1")
    seat2 = Seat("s2", "tenant_a", "vendor_x", "/tmp/home_s2")
    
    env1 = seat1.get_env()
    env2 = seat2.get_env()
    
    assert env1["HOME"] == "/tmp/home_s1"
    assert env2["HOME"] == "/tmp/home_s2"
    assert env1["SEAT_ID"] == "s1"
    assert env2["SEAT_ID"] == "s2"
    assert env1["HOME"] != env2["HOME"]

@pytest.mark.asyncio
async def test_lease_affinity_and_refresh(seat_pool):
    seat = Seat("s1", "tenant_a", "vendor_x", "/tmp/home_s1", token_lifetime=0.1)
    seat_pool.register_seat(seat)
    
    acquired_seat = await seat_pool.acquire("tenant_a", "vendor_x")
    first_token = acquired_seat.token
    
    # Wait for token to expire
    await asyncio.sleep(0.15)
    
    # It still has the same seat, but if we release and acquire, it will refresh
    seat_pool.release(acquired_seat)
    re_acquired_seat = await seat_pool.acquire("tenant_a", "vendor_x")
    
    assert re_acquired_seat.seat_id == "s1"  # Lease affinity (got the same seat)
    assert re_acquired_seat.token != first_token  # Token was refreshed due to expiry
