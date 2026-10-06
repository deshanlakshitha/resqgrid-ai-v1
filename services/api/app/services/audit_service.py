"""Audit trail helper: records significant actions to the immutable audit log."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AuditLog, AuditAction


async def log_action(
    db: AsyncSession,
    action: AuditAction,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    details: dict | None = None,
    old_values: dict | None = None,
    new_values: dict | None = None,
    request_id: str | None = None,
) -> AuditLog:
    """Append an entry to the audit trail. Caller commits the session."""
    entry = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        details=details,
        old_values=old_values,
        new_values=new_values,
        request_id=request_id,
    )
    db.add(entry)
    await db.flush()
    return entry
