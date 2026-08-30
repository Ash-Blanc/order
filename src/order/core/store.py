"""SQLite async storage for commitments"""
import json
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from sqlalchemy import Column, String, DateTime, Integer, JSON, create_engine, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings
from .models import Commitment, CommitmentStatus, Source

Base = declarative_base()


class CommitmentRow(Base):
    __tablename__ = "commitments"
    
    id = Column(String, primary_key=True)
    source = Column(String, index=True)
    text = Column(String)
    extracted_task = Column(String)
    platform_id = Column(String, index=True)
    platform_url = Column(String)
    deadline = Column(DateTime, nullable=True)
    priority = Column(Integer, default=0)
    status = Column(String, default="pending", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(JSON, nullable=True)


class Store:
    def __init__(self):
        self.db_path = Path(settings.data_dir) / "order.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{self.db_path}",
            echo=False
        )
        self.async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
    
    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def add(self, commitment: Commitment) -> str:
        async with self.async_session() as session:
            row = CommitmentRow(
                id=commitment.id,
                source=commitment.source.value,
                text=commitment.text,
                extracted_task=commitment.extracted_task,
                platform_id=commitment.platform_id,
                platform_url=commitment.platform_url,
                deadline=commitment.deadline,
                priority=commitment.priority,
                status=commitment.status.value,
                created_at=commitment.created_at,
                raw_data=commitment.raw_data
            )
            session.add(row)
            await session.commit()
            return commitment.id
    
    async def add_many(self, commitments: List[Commitment]):
        async with self.async_session() as session:
            # Get existing platform_ids to avoid duplicates
            result = await session.execute(select(CommitmentRow.platform_id))
            existing_ids = {row for row in result.scalars().all()}

            for c in commitments:
                if c.platform_id in existing_ids:
                    continue
                row = CommitmentRow(
                    id=c.id,
                    source=c.source.value,
                    text=c.text,
                    extracted_task=c.extracted_task,
                    platform_id=c.platform_id,
                    platform_url=c.platform_url,
                    deadline=c.deadline,
                    priority=c.priority,
                    status=c.status.value,
                    created_at=c.created_at,
                    raw_data=c.raw_data
                )
                session.add(row)
                existing_ids.add(c.platform_id)
            await session.commit()
    
    async def get_all(self) -> List[Commitment]:
        async with self.async_session() as session:
            result = await session.execute(
                select(CommitmentRow).order_by(CommitmentRow.created_at.desc())
            )
            rows = result.scalars().all()
            return [self._row_to_model(r) for r in rows]
    
    async def get_pending(self) -> List[Commitment]:
        async with self.async_session() as session:
            result = await session.execute(
                select(CommitmentRow)
                .where(CommitmentRow.status == "pending")
                .order_by(CommitmentRow.priority.desc(), CommitmentRow.deadline.asc())
            )
            rows = result.scalars().all()
            return [self._row_to_model(r) for r in rows]
    
    async def update_status(self, commitment_id: str, status: CommitmentStatus):
        async with self.async_session() as session:
            result = await session.execute(
                select(CommitmentRow).where(CommitmentRow.id == commitment_id)
            )
            row = result.scalar_one_or_none()
            if row:
                row.status = status.value
                await session.commit()
    
    async def count_by_status(self) -> dict:
        async with self.async_session() as session:
            result = await session.execute(select(CommitmentRow))
            rows = result.scalars().all()
            counts = {}
            for row in rows:
                counts[row.status] = counts.get(row.status, 0) + 1
            return counts
    
    async def expire_old(self, hours: int = 72) -> int:
        """Mark old pending commitments as expired"""
        from datetime import timedelta
        from sqlalchemy import update
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        async with self.async_session() as session:
            result = await session.execute(
                select(CommitmentRow)
                .where(CommitmentRow.status == "pending")
                .where(CommitmentRow.created_at < cutoff)
            )
            rows = result.scalars().all()
            for row in rows:
                row.status = "expired"
            await session.commit()
            return len(rows)

    def _row_to_model(self, row: CommitmentRow) -> Commitment:
        return Commitment(
            id=row.id,
            source=Source(row.source),
            text=row.text,
            extracted_task=row.extracted_task,
            platform_id=row.platform_id,
            platform_url=row.platform_url,
            deadline=row.deadline,
            priority=row.priority,
            status=CommitmentStatus(row.status),
            created_at=row.created_at,
            raw_data=row.raw_data
        )


store = Store()
