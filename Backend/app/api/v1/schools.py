from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database.connection import get_session
from app.services.school import SchoolService
from app.schemas import PaginatedResponse

router = APIRouter()


@router.get("/schools", response_model=PaginatedResponse)
def read_schools(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    schools, total, total_pages = SchoolService.get_schools(page, page_size, session)
    return PaginatedResponse(
        items=schools,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/schools/count")
def schools_count(session: Session = Depends(get_session)):
    return SchoolService.get_schools_count(session)
