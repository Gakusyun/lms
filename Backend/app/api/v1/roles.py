from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database.connection import get_session
from app.services.role import RoleService
from app.schemas import PaginatedResponse

router = APIRouter()


@router.get("/roles", response_model=PaginatedResponse)
def read_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    roles, total, total_pages = RoleService.get_roles(page, page_size, session)
    return PaginatedResponse(
        items=roles,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/roles/count")
def roles_count(session: Session = Depends(get_session)):
    return RoleService.get_roles_count(session)
