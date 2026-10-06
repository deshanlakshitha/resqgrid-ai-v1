"""AI Command Assistant routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.models.user import User, UserRole
from app.schemas.schemas import AssistantQuery, AssistantResponse

router = APIRouter()


@router.post("/query", response_model=AssistantResponse)
async def query_assistant(
    data: AssistantQuery,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DISPATCHER, UserRole.ADMIN)),
):
    """Query the AI command assistant for situational awareness."""
    from app.services.assistant_service import process_assistant_query
    return await process_assistant_query(db, data, current_user)
