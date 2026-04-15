from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database.connection import get_session
from app.services.statistics import StatisticsService
from app.api.deps import check_login, check_role

router = APIRouter()


@router.get("/statistics/leaves")
def get_leave_statistics(
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    session: Session = Depends(get_session),
):
    """获取请假统计数据 - 仅管理员和审核员可访问"""
    return StatisticsService.get_leave_statistics(current_user, session)


@router.get("/statistics/leaves/trend")
def get_leave_trend(
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    days: int = Query(30, ge=1, le=365),
    session: Session = Depends(get_session),
):
    """获取请假趋势数据 - 仅管理员和审核员可访问"""
    return StatisticsService.get_leave_trend(current_user, days, session)


@router.get("/statistics/courses/enrollment")
def get_course_enrollment_statistics(
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    session: Session = Depends(get_session),
):
    """获取课程选课统计数据 - 仅管理员和审核员可访问"""
    return StatisticsService.get_course_enrollment_statistics(current_user, session)


@router.get("/statistics/users")
def get_user_statistics(
    current_user: dict = Depends(check_role(["admin"])),
    session: Session = Depends(get_session),
):
    """获取用户统计数据 - 仅管理员可访问"""
    return StatisticsService.get_user_statistics(session)


@router.get("/statistics/reviewers/performance")
def get_reviewer_performance(
    current_user: dict = Depends(check_role(["admin"])),
    session: Session = Depends(get_session),
):
    """获取审核员绩效统计 - 仅管理员可访问"""
    return StatisticsService.get_reviewer_performance(current_user, session)


@router.get("/statistics/reviewers/students")
def get_reviewer_students_statistics(
    current_user: dict = Depends(check_role(["reviewer"])),
    session: Session = Depends(get_session),
):
    """获取审核员管理的学生统计情况 - 仅审核员可访问"""
    return StatisticsService.get_reviewer_students_statistics(current_user, session)
