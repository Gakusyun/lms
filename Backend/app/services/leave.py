from sqlmodel import Session, select, func
from fastapi import Depends, Query, HTTPException
from datetime import datetime
from typing import List

from app.models import Leave, Student, Reviewer, Teacher, Course, AuditAction
from app.services.student_course import StudentCourseService
from app.schemas import LeaveCreate
from app.services.common import CommonService
from app.services.audit_log import AuditLogService


class LeaveService:
    @staticmethod
    def get_leaves(
        current_user: dict,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        session: Session = Depends(lambda: None),
    ):
        """分页获取请假记录"""
        query = select(Leave)

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

        offset = (page - 1) * page_size
        leaves = session.exec(query.offset(offset).limit(page_size)).all()

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
                    Student, "student_id", "student_name", "guarantee_student_name",
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

        if current_user["role"] == "student":
            leave_dict["student_id"] = current_user["id"]
        elif not leave_dict.get("student_id"):
            raise HTTPException(status_code=400, detail="student_id is required for non-student users")

        student = session.exec(
            select(Student).where(Student.student_id == leave_dict["student_id"])
        ).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        if student.reviewer_id:
            leave_dict["reviewer_id"] = student.reviewer_id
        else:
            raise HTTPException(status_code=400, detail="Student has no assigned reviewer")

        if leave_dict.get("course_id"):
            if not StudentCourseService.verify_student_enrollment(
                leave_dict["student_id"], leave_dict["course_id"], session
            ):
                raise HTTPException(
                    status_code=400, detail="Student has not enrolled in this course"
                )

        if not leave_dict.get("leave_date"):
            leave_dict["leave_date"] = datetime.now()

        # ========== 自动业务校验 ==========

        # 2.1 课程冲突检测：查询该学生当天是否已有请假记录与同一课程时间冲突
        if leave_dict.get("course_id") and leave_dict.get("leave_date"):
            existing_conflict = session.exec(
                select(Leave).where(
                    Leave.student_id == leave_dict["student_id"],
                    Leave.course_id == leave_dict["course_id"],
                    Leave.leave_date == leave_dict["leave_date"],
                    Leave.status.in_(["待审批", "已批准"]),
                )
            ).first()
            if existing_conflict:
                raise HTTPException(
                    status_code=400,
                    detail=f"课程冲突：该学生当天已有请假记录（ID:{existing_conflict.leave_id}），同一课程同一时间不得重复请假"
                )

        # 2.2 历史请假频次校验：统计该学生近30天请假次数
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_leaves_count = session.exec(
            select(func.count(Leave.leave_id)).where(
                Leave.student_id == leave_dict["student_id"],
                Leave.leave_date >= thirty_days_ago,
            )
        ).one()
        if recent_leaves_count >= 5:
            raise HTTPException(
                status_code=400,
                detail=f"请假频次超限：该学生近30天已有 {recent_leaves_count} 次请假记录，请联系审核员"
            )

        # 2.4 紧急请假担保人关联校验
        if leave_dict.get("guarantee_student_id"):
            guarantee_student = session.exec(
                select(Student).where(Student.student_id == leave_dict["guarantee_student_id"])
            ).first()
            if not guarantee_student:
                raise HTTPException(
                    status_code=400,
                    detail="担保学生不存在"
                )
            if not guarantee_student.guarantee_permission or guarantee_student.guarantee_permission < datetime.now():
                raise HTTPException(
                    status_code=400,
                    detail="担保学生无担保权限或权限已过期"
                )

        leave = Leave(**leave_dict)
        session.add(leave)
        session.commit()
        session.refresh(leave)

        AuditLogService.log(
            current_user=current_user,
            action=AuditAction.LEAVE_CREATE,
            target_type="leave",
            target_id=leave.leave_id,
            detail=f"创建请假，类型={leave_dict.get('leave_type')}",
            session=session,
        )
        return leave

    @staticmethod
    def get_leaves_by_student(current_user: dict, student_id: int, session: Session):
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
                    Student, "student_id", "student_name", "guarantee_student_name",
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

        if leave.status != "待审批":
            raise HTTPException(status_code=403, detail="Only pending leave requests can be edited")

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

        if "student_id" in update_data:
            if update_data["student_id"] != leave.student_id:
                update_data["student_id"] = leave.student_id

        update_data.pop("status", None)

        if "course_id" in update_data and update_data["course_id"]:
            if not StudentCourseService.verify_student_enrollment(
                leave.student_id, update_data["course_id"], session
            ):
                raise HTTPException(
                    status_code=400, detail="Student has not enrolled in this course"
                )

        update_data["is_modified"] = True

        for key, value in update_data.items():
            setattr(leave, key, value)

        session.commit()
        session.refresh(leave)

        AuditLogService.log(
            current_user=current_user,
            action=AuditAction.LEAVE_EDIT,
            target_type="leave",
            target_id=leave.leave_id,
            detail="编辑请假记录",
            session=session,
        )
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

        AuditLogService.log(
            current_user=current_user,
            action=AuditAction.LEAVE_APPROVE,
            target_type="leave",
            target_id=leave.leave_id,
            detail=f"批准请假，意见={audit_remarks}",
            session=session,
        )

        # 审批通过后自动生成二维码凭证
        from app.services.qr_code import QRCodeService
        try:
            QRCodeService.generate_qr_for_leave(leave, session)
            session.refresh(leave)
        except Exception:
            pass

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

        AuditLogService.log(
            current_user=current_user,
            action=AuditAction.LEAVE_REJECT,
            target_type="leave",
            target_id=leave.leave_id,
            detail=f"拒绝请假，意见={audit_remarks}",
            session=session,
        )
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

        if leave.status != "待审批":
            raise HTTPException(status_code=403, detail="Only pending leave requests can be cancelled")

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

        AuditLogService.log(
            current_user=current_user,
            action=AuditAction.LEAVE_CANCEL,
            target_type="leave",
            target_id=leave.leave_id,
            detail="撤销请假申请",
            session=session,
        )
        return leave

    @staticmethod
    def batch_approve_leaves(
        current_user: dict,
        leave_ids: List[int],
        audit_remarks: str,
        session: Session,
    ):
        """批量批准请假"""
        if not leave_ids:
            raise HTTPException(status_code=400, detail="leave_ids cannot be empty")

        approved_leaves = []
        errors = []

        for leave_id in leave_ids:
            try:
                leave = session.exec(
                    select(Leave).where(Leave.leave_id == leave_id)
                ).first()

                if not leave:
                    errors.append({"leave_id": leave_id, "error": "Leave record not found"})
                    continue

                if leave.status != "待审批":
                    errors.append({"leave_id": leave_id, "error": "Only pending leaves can be approved"})
                    continue

                if current_user["role"] == "reviewer":
                    if leave.reviewer_id != current_user["id"]:
                        errors.append({"leave_id": leave_id, "error": "Not authorized"})
                        continue
                elif current_user["role"] != "admin":
                    errors.append({"leave_id": leave_id, "error": "Permission denied"})
                    continue

                leave.status = "已批准"
                leave.audit_remarks = audit_remarks
                leave.audit_time = datetime.now()
                session.commit()
                session.refresh(leave)

                # 批量审批通过后生成二维码
                from app.services.qr_code import QRCodeService
                try:
                    QRCodeService.generate_qr_for_leave(leave, session)
                except Exception:
                    pass

                approved_leaves.append(leave)
            except Exception as e:
                errors.append({"leave_id": leave_id, "error": str(e)})

        AuditLogService.log(
            current_user=current_user,
            action=AuditAction.LEAVE_BATCH_APPROVE,
            target_type="leave",
            detail=f"批量批准 {len(approved_leaves)} 条请假",
            session=session,
        )

        return {
            "approved": approved_leaves,
            "errors": errors,
            "total": len(leave_ids),
            "success_count": len(approved_leaves),
            "error_count": len(errors),
        }

    @staticmethod
    def batch_reject_leaves(
        current_user: dict,
        leave_ids: List[int],
        audit_remarks: str,
        session: Session,
    ):
        """批量拒绝请假"""
        if not leave_ids:
            raise HTTPException(status_code=400, detail="leave_ids cannot be empty")

        rejected_leaves = []
        errors = []

        for leave_id in leave_ids:
            try:
                leave = session.exec(
                    select(Leave).where(Leave.leave_id == leave_id)
                ).first()

                if not leave:
                    errors.append({"leave_id": leave_id, "error": "Leave record not found"})
                    continue

                if leave.status != "待审批":
                    errors.append({"leave_id": leave_id, "error": "Only pending leaves can be rejected"})
                    continue

                if current_user["role"] == "reviewer":
                    if leave.reviewer_id != current_user["id"]:
                        errors.append({"leave_id": leave_id, "error": "Not authorized"})
                        continue
                elif current_user["role"] != "admin":
                    errors.append({"leave_id": leave_id, "error": "Permission denied"})
                    continue

                leave.status = "已拒绝"
                leave.audit_remarks = audit_remarks
                leave.audit_time = datetime.now()
                session.commit()
                session.refresh(leave)
                rejected_leaves.append(leave)
            except Exception as e:
                errors.append({"leave_id": leave_id, "error": str(e)})

        AuditLogService.log(
            current_user=current_user,
            action=AuditAction.LEAVE_BATCH_REJECT,
            target_type="leave",
            detail=f"批量拒绝 {len(rejected_leaves)} 条请假",
            session=session,
        )

        return {
            "rejected": rejected_leaves,
            "errors": errors,
            "total": len(leave_ids),
            "success_count": len(rejected_leaves),
            "error_count": len(errors),
        }
