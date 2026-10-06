"""Auth dependencies for FastAPI route protection."""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import and_, false, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.models.entities import Assignment, AssignmentStatus
from app.models.incident import Incident

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate JWT, return current user."""
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    try:
        user_id = uuid.UUID(payload.get("sub", ""))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload") from None

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True, User.is_deleted == False))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def require_role(*roles: UserRole):
    """Dependency factory: require the user to have one of the specified roles."""

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not authorized. Required: {[r.value for r in roles]}",
            )
        return current_user

    return role_checker


def responder_assignment_scope(user: User, include_unassigned: bool = True):
    """Responders may see their work and claim newly dispatched, unassigned work."""
    owned = Assignment.responder_id == user.id
    if include_unassigned:
        return or_(owned, and_(Assignment.responder_id.is_(None), Assignment.status == AssignmentStatus.ASSIGNED))
    return owned


def incident_scope(user: User, include_unassigned: bool = True):
    """Apply the same object policy to list, detail, and evidence queries."""
    if user.role in (UserRole.ADMIN, UserRole.DISPATCHER):
        return true()
    if user.role == UserRole.CITIZEN:
        return Incident.reporter_id == user.id
    if user.role == UserRole.RESPONDER:
        assigned = select(Assignment.incident_id).where(
            Assignment.is_deleted == False,
            responder_assignment_scope(user, include_unassigned),
        )
        return or_(Incident.reporter_id == user.id, Incident.id.in_(assigned))
    return false()


async def require_incident_access(db: AsyncSession, incident_id: uuid.UUID, user: User, *, write: bool = False):
    result = await db.execute(select(Incident).where(
        Incident.id == incident_id, Incident.is_deleted == False,
        incident_scope(user, include_unassigned=not write),
    ))
    incident = result.scalar_one_or_none()
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
