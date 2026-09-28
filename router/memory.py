"""Shared conversation memory: one transcript per user across all devices and assistants.

A session is a user plus a rolling window (`session_minutes`); "new conversation" ends it
early. Turns produced by a `private: true` assistant are flagged and never replayed to cloud
assistants or folded into summaries.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import event
from sqlmodel import Field, SQLModel, create_engine, select
from sqlmodel import Session as DbSession

from router.registry import Assistant
from router.settings import MemoryConfig

log = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(UTC)


class ConversationSession(SQLModel, table=True):
    __tablename__ = "sessions"

    id: str = Field(primary_key=True)
    user_id: str = Field(index=True)
    started_at: datetime
    last_active_at: datetime
    ended_at: datetime | None = None
    summary: str | None = None
    last_assistant: str | None = None
    last_assistant_at: datetime | None = None


class Turn(SQLModel, table=True):
    __tablename__ = "turns"

    id: int | None = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    user_id: str = Field(index=True)
    role: str  # "user" | "assistant"
    assistant_key: str | None = None  # who spoke (assistant) or who was addressed (user)
    assistant_name: str | None = None
    content: str
    private: bool = False
    summarized: bool = False
    device_id: str | None = None
    created_at: datetime


class Memory:
    def __init__(
        self,
        config: MemoryConfig | None = None,
        *,
        db_url: str | None = None,
        now: Callable[[], datetime] = utcnow,
    ) -> None:
        self.config = config or MemoryConfig()
        self.now = now
        if db_url is None:
            path = Path(self.config.db_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            db_url = f"sqlite:///{path}"
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        if db_url.startswith("sqlite"):

            @event.listens_for(self.engine, "connect")
            def _pragmas(dbapi_conn, _record):  # type: ignore[no-untyped-def]
                cur = dbapi_conn.cursor()
                cur.execute("PRAGMA journal_mode=WAL")
                cur.execute("PRAGMA foreign_keys=ON")
                cur.close()

        SQLModel.metadata.create_all(self.engine)

    # -- sessions --------------------------------------------------------------------------
    def current_session(self, user_id: str) -> ConversationSession | None:
        cutoff = self.now() - timedelta(minutes=self.config.session_minutes)
        with DbSession(self.engine) as db:
            stmt = (
                select(ConversationSession)
                .where(ConversationSession.user_id == user_id)
                .where(ConversationSession.ended_at.is_(None))  # type: ignore[union-attr]
                .where(ConversationSession.last_active_at >= cutoff)
                .order_by(ConversationSession.last_active_at.desc())  # type: ignore[union-attr]
            )
            return db.exec(stmt).first()

    def get_or_create_session(self, user_id: str) -> ConversationSession:
        existing = self.current_session(user_id)
        if existing is not None:
            return existing
        now = self.now()
        session = ConversationSession(
            id=uuid.uuid4().hex[:12], user_id=user_id, started_at=now, last_active_at=now
        )
        with DbSession(self.engine) as db:
            db.add(session)
            db.commit()
            db.refresh(session)
        return session

    def end_session(self, user_id: str) -> ConversationSession | None:
        """'new conversation': close the active session so the next request starts fresh."""
        session = self.current_session(user_id)
        if session is None:
            return None
        with DbSession(self.engine) as db:
            row = db.get(ConversationSession, session.id)
            assert row is not None
            row.ended_at = self.now()
            db.add(row)
            db.commit()
            db.refresh(row)
            return row

    def get_session(self, session_id: str) -> ConversationSession | None:
        with DbSession(self.engine) as db:
            return db.get(ConversationSession, session_id)

    def sticky_assistant(self, session: ConversationSession, sticky_minutes: int) -> str | None:
        if session.last_assistant is None or session.last_assistant_at is None:
            return None
        if self.now() - session.last_assistant_at > timedelta(minutes=sticky_minutes):
            return None
        return session.last_assistant

    # -- turns -----------------------------------------------------------------------------
    def record_exchange(
        self,
        session: ConversationSession,
        *,
        user_text: str,
        reply: str,
        assistant: Assistant,
        device_id: str | None = None,
    ) -> ConversationSession:
        now = self.now()
        with DbSession(self.engine) as db:
            row = db.get(ConversationSession, session.id)
            assert row is not None
            common = dict(
                session_id=row.id,
                user_id=row.user_id,
                private=assistant.private,
                device_id=device_id,
                created_at=now,
                assistant_key=assistant.key,
                assistant_name=assistant.display_name,
            )
            db.add(Turn(role="user", content=user_text, **common))
            db.add(Turn(role="assistant", content=reply, **common))
            row.last_active_at = now
            row.last_assistant = assistant.key
            row.last_assistant_at = now
            db.add(row)
            db.commit()
            db.refresh(row)
            return row

    def touch(self, session: ConversationSession) -> None:
        with DbSession(self.engine) as db:
            row = db.get(ConversationSession, session.id)
            if row is not None:
                row.last_active_at = self.now()
                db.add(row)
                db.commit()

    def history(
        self,
        session: ConversationSession,
        *,
        include_private: bool,
        limit: int | None = None,
    ) -> list[Turn]:
        """Most recent un-summarized turns, oldest first."""
        limit = self.config.replay_turns if limit is None else limit
        with DbSession(self.engine) as db:
            stmt = (
                select(Turn)
                .where(Turn.session_id == session.id)
                .where(Turn.summarized == False)  # noqa: E712
                .order_by(Turn.created_at.desc(), Turn.id.desc())  # type: ignore[union-attr]
            )
            if not include_private:
                stmt = stmt.where(Turn.private == False)  # noqa: E712
            rows = db.exec(stmt.limit(limit)).all()
        return list(reversed(rows))

    def all_turns(self, session: ConversationSession) -> list[Turn]:
        with DbSession(self.engine) as db:
            stmt = (
                select(Turn).where(Turn.session_id == session.id).order_by(Turn.created_at, Turn.id)  # type: ignore[arg-type]
            )
            return list(db.exec(stmt).all())

    # -- summaries -------------------------------------------------------------------------
    def turns_to_summarize(self, session: ConversationSession) -> list[Turn]:
        """Non-private, un-summarized turns older than the replay window, once the session
        has more un-summarized turns than `summarize_after_turns`. Empty when nothing to do."""
        with DbSession(self.engine) as db:
            stmt = (
                select(Turn)
                .where(Turn.session_id == session.id)
                .where(Turn.summarized == False)  # noqa: E712
                .order_by(Turn.created_at, Turn.id)  # type: ignore[arg-type]
            )
            rows = list(db.exec(stmt).all())
        if len(rows) <= self.config.summarize_after_turns:
            return []
        older = rows[: len(rows) - self.config.replay_turns]
        return [t for t in older if not t.private]

    def apply_summary(
        self, session: ConversationSession, summary: str, turns: list[Turn]
    ) -> ConversationSession:
        ids = {t.id for t in turns}
        with DbSession(self.engine) as db:
            row = db.get(ConversationSession, session.id)
            assert row is not None
            row.summary = summary.strip()
            for t in db.exec(select(Turn).where(Turn.id.in_(ids))).all():  # type: ignore[union-attr]
                t.summarized = True
                db.add(t)
            db.add(row)
            db.commit()
            db.refresh(row)
            return row
