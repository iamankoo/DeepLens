import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ResearchStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchRun(Base):
    __tablename__ = "research_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    query: Mapped[str] = mapped_column(Text, nullable=False)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ResearchStatus] = mapped_column(
        Enum(ResearchStatus, values_callable=lambda e: [m.value for m in e], length=20),
        default=ResearchStatus.PENDING, server_default=ResearchStatus.PENDING.value,
        nullable=False, index=True,
    )

    report: Mapped[str | None] = mapped_column(LONGTEXT, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    iteration: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Name of the LangGraph node most recently completed (e.g. "planner",
    # "search", "writer") — lets the frontend show real staged progress
    # instead of a generic spinner. Set via WorkflowManager's on_step
    # callback while streaming the graph; not meaningful once the run is
    # completed/failed (report/error are the source of truth then).
    current_step: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    # Set when the RQ worker actually begins executing this run (mark_running),
    # distinct from created_at (when it was enqueued) — a run can legitimately
    # sit queued for a while behind an earlier job on a single worker before
    # its own execution ever starts. Staleness reconciliation
    # (research_run_repository._reconcile_if_stale) needs this distinction:
    # RQ's own per-job timeout is scoped to execution time, not queue wait,
    # so measuring a RUNNING row's staleness from created_at instead of
    # started_at could mark a row FAILED before the worker even got to start
    # it — reproduced live against this project's own single-worker setup
    # when an earlier job was still processing ahead of it in the queue.
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
