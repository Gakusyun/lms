from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from datetime import datetime
import json

from app.database.connection import get_session
from app.models import Leave, Student, Teacher, Course, School
from app.api.deps import check_login, check_role
from app.services.audit_log import AuditLogService, AuditAction

router = APIRouter()


@router.get("/export/leaves/json")
def export_leaves_json(
    current_user: dict = Depends(check_role(["admin"])),
    session: Session = Depends(get_session),
):
    """导出请假数据为JSON"""
    leaves = session.exec(select(Leave)).all()

    result = []
    for leave in leaves:
        # 关联学生信息
        student = session.exec(
            select(Student).where(Student.student_id == leave.student_id)
        ).first()
        student_name = student.student_name if student else None

        # 关联审核员信息
        reviewer_name = None
        if leave.reviewer_id:
            from app.models import Reviewer
            reviewer = session.exec(
                select(Reviewer).where(Reviewer.reviewer_id == leave.reviewer_id)
            ).first()
            reviewer_name = reviewer.reviewer_name if reviewer else None

        # 关联教师信息
        teacher_name = None
        if leave.teacher_id:
            teacher = session.exec(
                select(Teacher).where(Teacher.teacher_id == leave.teacher_id)
            ).first()
            teacher_name = teacher.teacher_name if teacher else None

        # 关联课程信息
        course_name = None
        if leave.course_id:
            course = session.exec(
                select(Course).where(Course.course_id == leave.course_id)
            ).first()
            course_name = course.course_name if course else None

        # 关联学校信息
        school_name = None
        if student and student.school_id:
            school = session.exec(
                select(School).where(School.school_id == student.school_id)
            ).first()
            school_name = school.school_name if school else None

        result.append({
            "leave_id": leave.leave_id,
            "student_id": leave.student_id,
            "student_name": student_name,
            "school_name": school_name,
            "leave_date": leave.leave_date.isoformat() if leave.leave_date else None,
            "leave_hours": leave.leave_hours,
            "status": leave.status,
            "leave_type": leave.leave_type,
            "remarks": leave.remarks,
            "course_name": course_name,
            "reviewer_name": reviewer_name,
            "teacher_name": teacher_name,
            "audit_remarks": leave.audit_remarks,
            "audit_time": leave.audit_time.isoformat() if leave.audit_time else None,
            "is_modified": leave.is_modified,
            "approval_level": leave.approval_level,
            "guarantee_student_id": leave.guarantee_student_id,
        })

    AuditLogService.log(
        current_user=current_user,
        action=AuditAction.DATA_EXPORT,
        target_type="export",
        target_id=None,
        detail=f"导出请假数据，共 {len(result)} 条",
        session=session,
    )

    return JSONResponse(
        content=result,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=leaves_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        },
    )


@router.get("/export/students/json")
def export_students_json(
    current_user: dict = Depends(check_role(["admin"])),
    session: Session = Depends(get_session),
):
    """导出学生数据为JSON"""
    students = session.exec(select(Student)).all()

    result = []
    for student in students:
        school_name = None
        if student.school_id:
            school = session.exec(
                select(School).where(School.school_id == student.school_id)
            ).first()
            school_name = school.school_name if school else None

        result.append({
            "student_id": student.student_id,
            "student_name": student.student_name,
            "school_name": school_name,
            "reviewer_id": student.reviewer_id,
        })

    AuditLogService.log(
        current_user=current_user,
        action=AuditAction.DATA_EXPORT,
        target_type="export",
        target_id=None,
        detail=f"导出学生数据，共 {len(result)} 条",
        session=session,
    )

    return JSONResponse(
        content=result,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=students_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        },
    )
