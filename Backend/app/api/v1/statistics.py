from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database.connection import get_session
from app.services.statistics import StatisticsService

router = APIRouter()


@router.get("/statistics/leaves")
def get_leave_statistics(
    token: str,
    session: Session = Depends(get_session),
):
    """获取请假统计数据"""
    return StatisticsService.get_leave_statistics(token, session)


@router.get("/statistics/leaves/trend")
def get_leave_trend(
    token: str,
    days: int = Query(30, ge=1, le=365),
    session: Session = Depends(get_session),
):
    """获取请假趋势数据"""
    return StatisticsService.get_leave_trend(token, days, session)


@router.get("/statistics/courses/enrollment")
def get_course_enrollment_statistics(
    token: str,
    session: Session = Depends(get_session),
):
    """获取课程选课统计数据"""
    return StatisticsService.get_course_enrollment_statistics(token, session)


@router.get("/statistics/users")
def get_user_statistics(
    session: Session = Depends(get_session),
):
    """获取用户统计数据"""
    return StatisticsService.get_user_statistics(session)


@router.get("/statistics/reviewers/performance")
def get_reviewer_performance(
    token: str,
    session: Session = Depends(get_session),
):
    """获取审核员绩效统计"""
    return StatisticsService.get_reviewer_performance(token, session)
