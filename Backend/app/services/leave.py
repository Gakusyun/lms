from sqlmodel import Session, select, func
from fastapi import Depends, Query, HTTPException
from datetime import datetime

from app.models import Leave, Student, Reviewer, Teacher, Course
from app.services.student_course import StudentCourseService
from app.schemas import LeaveCreate
from app.services.common import CommonService


class LeaveService:
    @staticmethod
    def get_leaves(
        current_user: dict,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        session: Session = Depends(lambda: None),
    ):
        """分页获取请假记录"""
        # 构建基础查询
        query = select(Leave)

        # 根据角色应用不同的过滤条件
        if current_user["role"] == "student":
            query = query.where(Leave.student_id == current_user["id"])
        elif current_user["role"] == "reviewer":
            query = query.where(Leave.reviewer_id == current_user["id"])
        elif current_user["role"] == "teacher":
            course_ids = session.exec(
                select(Course.course_id).where(Course.teacher_id == current_user["id"])
            ).all()
            if course_ids:
                query = query.where(Leave.course_id.in_(course_ids))
            else:
                query = query.where(Leave.course_id.is_(None))

        # 应用分页
        offset = (page - 1) * page_size
        leaves = session.exec(query.offset(offset).limit(page_size)).all()

        # 计算总数
        pk_col = list(Leave.__table__.primary_key.columns)[0]
        total_stmt = select(func.count(pk_col))
        if current_user["role"] == "student":
            total_stmt = total_stmt.where(Leave.student_id == current_user["id"])
        elif current_user["role"] == "reviewer":
            total_stmt = total_stmt.where(Leave.reviewer_id == current_user["id"])
        elif current_user["role"] == "teacher":
            course_ids = session.exec(
                select(Course.course_id).where(Course.teacher_id == current_user["id"])
            ).all()
            if course_ids:
                total_stmt = total_stmt.where(Leave.course_id.in_(course_ids))
            else:
                total_stmt = total_stmt.where(Leave.course_id.is_(None))
        total = session.exec(total_stmt).one()

        total_pages = (total + page_size - 1) // page_size

        items = CommonService.inject_relations(
            session,
            leaves,
            {
                "student_id": (Student, "student_id", "student_name", "student_name"),
                "reviewer_id": (Reviewer, "reviewer_id", "reviewer_name", "reviewer_name"),
                "teacher_id": (Teacher, "teacher_id", "teacher_name", "teacher_name"),
                "guarantee_student_id": (
                    Student,
                    "student_id",
                    "student_name",
                    "guarantee_student_name",
                ),
            },
        )
        course_ids = {item["course_id"] for item in items if item.get("course_id")}
        if course_ids:
            courses = session.exec(
                select(Course).where(Course.course_id.in_(course_ids))
            ).all()
            course_map = {c.course_id: c.course_name for c in courses}
            for item in items:
                item["course_name"] = course_map.get(item.get("course_id"))
        else:
            for item in items:
                item["course_name"] = None

        return items, total, total_pages

    @staticmethod
    def get_leaves_count(current_user: dict, session: Session):
        """获取请假记录数量"""
        if current_user["role"] == "admin":
            count = session.exec(select(func.count(Leave.leave_id))).one()
        elif current_user["role"] == "student":
            count = session.exec(
                select(func.count(Leave.leave_id)).where(Leave.student_id == current_user["id"])
            ).one()
        elif current_user["role"] == "reviewer":
            count = session.exec(
                select(func.count(Leave.leave_id)).where(Leave.reviewer_id == current_user["id"])
            ).one()
        elif current_user["role"] == "teacher":
            course_ids = session.exec(
                select(Course.course_id).where(Course.teacher_id == current_user["id"])
            ).all()
            if course_ids:
                count = session.exec(
                    select(func.count(Leave.leave_id)).where(Leave.course_id.in_(course_ids))
                ).one()
            else:
                count = 0
        else:
            raise HTTPException(status_code=403, detail="Permission denied")

        return {"leaves_count": count}

    @staticmethod
    def create_leave(
        current_user: dict,
        leave_data: LeaveCreate,
        session: Session,
    ):
        leave_dict = leave_data.model_dump()

        # 根据用户角色自动设置student_id
        if current_user["role"] == "student":
            leave_dict["student_id"] = current_user["id"]
        elif not leave_dict.get("student_id"):
            raise HTTPException(status_code=400, detail="student_id is required for non-student users")

        # 自动设置reviewer_id
        student = session.exec(
            select(Student).where(Student.student_id == leave_dict["student_id"])
        ).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        if student.reviewer_id:
            leave_dict["reviewer_id"] = student.reviewer_id
        else:
            raise HTTPException(status_code=400, detail="Student has no assigned reviewer")

        # 验证学生是否选择了该课程
        if leave_dict.get("course_id"):
            if not StudentCourseService.verify_student_enrollment(
                leave_dict["student_id"],
                leave_dict["course_id"],
                session
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Student has not enrolled in this course"
                )

        if not leave_dict.get("leave_date"):
            leave_dict["leave_date"] = datetime.now()

        leave = Leave(**leave_dict)
        session.add(leave)
        session.commit()
        session.refresh(leave)
        return leave

    @staticmethod
    def get_leaves_by_student(current_user: dict, student_id: int, session: Session):
        # 管理员和审核员可以查看任意学生的请假记录
        if current_user["role"] in ["admin", "reviewer"]:
            pass
        elif current_user["role"] == "student":
            if current_user["id"] != student_id:
                raise HTTPException(status_code=403, detail="Permission denied")
        elif current_user["role"] == "teacher":
            course_ids = session.exec(
                select(Course.course_id).where(Course.teacher_id == current_user["id"])
            ).all()
            if course_ids:
                student_in_courses = session.exec(
                    select(Leave.leave_id)
                    .where(Leave.student_id == student_id)
                    .where(Leave.course_id.in_(course_ids))
                ).first()
                if not student_in_courses:
                    raise HTTPException(status_code=403, detail="Permission denied")
            else:
                raise HTTPException(status_code=403, detail="Permission denied")

        leaves = session.exec(select(Leave).where(Leave.student_id == student_id)).all()

        items = CommonService.inject_relations(
            session,
            leaves,
            {
                "student_id": (Student, "student_id", "student_name", "student_name"),
                "reviewer_id": (Reviewer, "reviewer_id", "reviewer_name", "reviewer_name"),
                "teacher_id": (Teacher, "teacher_id", "teacher_name", "teacher_name"),
                "guarantee_student_id": (
                    Student,
                    "student_id",
                    "student_name",
                    "guarantee_student_name",
                ),
            },
        )
        course_ids = {item["course_id"] for item in items if item.get("course_id")}
        if course_ids:
            courses = session.exec(
                select(Course).where(Course.course_id.in_(course_ids))
            ).all()
            course_map = {c.course_id: c.course_name for c in courses}
            for item in items:
                item["course_name"] = course_map.get(item.get("course_id"))
        else:
            for item in items:
                item["course_name"] = None

        return items

    @staticmethod
    def get_leaves_by_reviewer(current_user: dict, reviewer_id: int, session: Session):
        if current_user["role"] == "reviewer":
            if current_user["id"] != reviewer_id:
                raise HTTPException(status_code=403, detail="Permission denied")
        elif current_user["role"] == "admin":
            pass
        else:
            raise HTTPException(status_code=403, detail="Permission denied")
        return session.exec(select(Leave).where(Leave.reviewer_id == reviewer_id)).all()

    @staticmethod
    def get_leaves_by_course(course_id: int, session: Session):
        return session.exec(select(Leave).where(Leave.course_id == course_id)).all()

    @staticmethod
    def get_leaves_by_teacher(teacher_id: int, session: Session):
        course_ids = session.exec(
            select(Course.course_id).where(Course.teacher_id == teacher_id)
        ).all()
        if not course_ids:
            return []
        return session.exec(select(Leave).where(Leave.course_id.in_(course_ids))).all()

    @staticmethod
    def edit_leave(
        current_user: dict,
        leave_id: int,
        leave_data: LeaveCreate,
        session: Session,
    ):
        """编辑请假记录"""
        leave = session.exec(
            select(Leave).where(Leave.leave_id == leave_id)
        ).first()

        if not leave:
            raise HTTPException(status_code=404, detail="Leave record not found")

        # 只有待审批的记录可以修改
        if leave.status != "待审批":
            raise HTTPException(status_code=403, detail="Only pending leave requests can be edited")

        # 权限验证
        if current_user["role"] == "student":
            if leave.student_id != current_user["id"]:
                raise HTTPException(status_code=403, detail="Students can only edit their own leave requests")
        elif current_user["role"] == "reviewer":
            if leave.reviewer_id != current_user["id"]:
                raise HTTPException(status_code=403, detail="Reviewers can only edit leave requests of their assigned students")
        elif current_user["role"] == "admin":
            pass
        else:
            raise HTTPException(status_code=403, detail="Permission denied")

        update_data = leave_data.model_dump(exclude_unset=True)

        # 不允许修改student_id
        if "student_id" in update_data:
            if update_data["student_id"] != leave.student_id:
                update_data["student_id"] = leave.student_id

        # 不允许修改status，防止状态机绕过
        update_data.pop("status", None)

        # 验证课程
        if "course_id" in update_data and update_data["course_id"]:
            if not StudentCourseService.verify_student_enrollment(
                leave.student_id,
                update_data["course_id"],
                session
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Student has not enrolled in this course"
                )

        update_data["is_modified"] = True

        for key, value in update_data.items():
            setattr(leave, key, value)

        session.commit()
        session.refresh(leave)
        return leave

    @staticmethod
    def approve_leave(
        current_user: dict,
        leave_id: int,
        audit_remarks: str,
        session: Session,
    ):
        """批准请假"""
        leave = session.exec(
            select(Leave).where(Leave.leave_id == leave_id)
        ).first()

        if not leave:
            raise HTTPException(status_code=404, detail="Leave record not found")

        if leave.status != "待审批":
            raise HTTPException(status_code=403, detail="Only pending leave requests can be approved")

        if current_user["role"] == "reviewer":
            if leave.reviewer_id != current_user["id"]:
                raise HTTPException(status_code=403, detail="Reviewers can only approve leave requests of their assigned students")
        elif current_user["role"] == "admin":
            pass
        else:
            raise HTTPException(status_code=403, detail="Permission denied")

        leave.status = "已批准"
        leave.audit_remarks = audit_remarks
        leave.audit_time = datetime.now()

        session.commit()
        session.refresh(leave)
        return leave

    @staticmethod
    def reject_leave(
        current_user: dict,
        leave_id: int,
        audit_remarks: str,
        session: Session,
    ):
        """拒绝请假"""
        leave = session.exec(
            select(Leave).where(Leave.leave_id == leave_id)
        ).first()

        if not leave:
            raise HTTPException(status_code=404, detail="Leave record not found")

        if leave.status != "待审批":
            raise HTTPException(status_code=403, detail="Only pending leave requests can be rejected")

        if current_user["role"] == "reviewer":
            if leave.reviewer_id != current_user["id"]:
                raise HTTPException(status_code=403, detail="Reviewers can only reject leave requests of their assigned students")
        elif current_user["role"] == "admin":
            pass
        else:
            raise HTTPException(status_code=403, detail="Permission denied")

        leave.status = "已拒绝"
        leave.audit_remarks = audit_remarks
        leave.audit_time = datetime.now()

        session.commit()
        session.refresh(leave)
        return leave

    @staticmethod
    def cancel_leave(
        current_user: dict,
        leave_id: int,
        session: Session,
    ):
        """撤销请假"""
        leave = session.exec(
            select(Leave).where(Leave.leave_id == leave_id)
        ).first()

        if not leave:
            raise HTTPException(status_code=404, detail="Leave record not found")

        # 只有待审批的记录可以撤销
        if leave.status != "待审批":
            raise HTTPException(status_code=403, detail="Only pending leave requests can be cancelled")

        # 权限验证：学生只能撤销自己的，管理员可以撤销所有
        if current_user["role"] == "student":
            if leave.student_id != current_user["id"]:
                raise HTTPException(status_code=403, detail="Students can only cancel their own leave requests")
        elif current_user["role"] == "admin":
            pass
        else:
            raise HTTPException(status_code=403, detail="Permission denied")

        leave.status = "已撤销"
        leave.audit_time = datetime.now()

        session.commit()
        session.refresh(leave)
        return leave
