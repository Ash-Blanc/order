"""Unit tests for the Store layer"""
import pytest
from datetime import datetime, timedelta

from order.core.models import Commitment, CommitmentStatus, Source
from order.core.store import store


pytestmark = pytest.mark.asyncio


def _make_commitment(platform_id: str = "p1", priority: int = 1) -> Commitment:
    return Commitment(
        source=Source.GITHUB,
        text="Review the PR",
        extracted_task="Review PR #123",
        platform_id=platform_id,
        platform_url="https://github.com/org/repo/pull/123",
        priority=priority,
    )


class TestAdd:
    async def test_add_and_retrieve(self):
        c = _make_commitment()
        await store.add(c)
        all_items = await store.get_all()
        assert len(all_items) == 1
        assert all_items[0].id == c.id

    async def test_add_many_deduplicates_by_platform_id(self):
        c1 = _make_commitment("same-id")
        c2 = _make_commitment("same-id")
        await store.add_many([c1, c2])
        all_items = await store.get_all()
        assert len(all_items) == 1


class TestGetPending:
    async def test_pending_ordered_by_priority(self):
        low = _make_commitment("low", priority=0)
        high = _make_commitment("high", priority=3)
        await store.add_many([low, high])
        pending = await store.get_pending()
        assert pending[0].priority >= pending[-1].priority

    async def test_done_not_in_pending(self):
        c = _make_commitment()
        await store.add(c)
        await store.update_status(c.id, CommitmentStatus.DONE)
        pending = await store.get_pending()
        assert all(p.id != c.id for p in pending)


class TestExpireOld:
    async def test_expire_old_marks_as_expired(self):
        c = _make_commitment()
        await store.add(c)

        # Artificially age the row
        from sqlalchemy import update
        from order.core.store import CommitmentRow
        async with store.async_session() as session:
            await session.execute(
                update(CommitmentRow)
                .where(CommitmentRow.id == c.id)
                .values(created_at=datetime.utcnow() - timedelta(hours=73))
            )
            await session.commit()

        expired_count = await store.expire_old(hours=72)
        assert expired_count == 1
        pending = await store.get_pending()
        assert all(p.id != c.id for p in pending)

    async def test_recent_items_not_expired(self):
        c = _make_commitment()
        await store.add(c)
        expired_count = await store.expire_old(hours=72)
        assert expired_count == 0


class TestCountByStatus:
    async def test_counts_are_accurate(self):
        c1 = _make_commitment("id1")
        c2 = _make_commitment("id2")
        await store.add_many([c1, c2])
        await store.update_status(c1.id, CommitmentStatus.DONE)
        counts = await store.count_by_status()
        assert counts["pending"] == 1
        assert counts["done"] == 1
