from sqlmodel import Session, select, func
from fastapi import Depends, Query, HTTPException
from datetime import datetime, timedelta
from typing import List

from app.models import Leave, Student, Reviewer, Teacher, Course, AuditAction
from app.services.student_course import StudentCourseService
from app.schemas import LeaveCreate
from app.services.common import CommonService
from app.services.audit_log import AuditLogService
from app.services.notification import NotificationService


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

        # 2.3 时长分级审批路由：按请假时长分配不同审批层级
        leave_hours_str = leave_dict.get("leave_hours")
        leave_hours = 0
        try:
            leave_hours = float(leave_hours_str) if leave_hours_str else 0
        except (ValueError, TypeError):
            leave_hours = 0

        if leave_hours <= 4:
            # ≤4小时：一级审批（审核员直接审批）
            leave_dict["approval_level"] = 1
        elif leave_hours <= 24:
            # 4-24小时(含)：二级审批，需管理员确认
            leave_dict["approval_level"] = 2
        else:
            # >24小时：三级审批，标记为需重点关注
            leave_dict["approval_level"] = 3

        # 二级及以上审批时，记录备注提示
        if leave_dict["approval_level"] >= 2:
            level_msg = f"请假{leave_hours}小时，触发{leave_dict['approval_level']}级审批"
            existing_remarks = leave_dict.get("remarks") or ""
            if level_msg not in existing_remarks:
                leave_dict["remarks"] = f"{existing_remarks}[{level_msg}]".strip() if existing_remarks else f"[{level_msg}]"

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
            # 审核员只能审批一级请假(≤4h)，二级/三级请假必须由管理员审批
            if leave.approval_level > 1:
                raise HTTPException(
                    status_code=403,
                    detail=f"该请假触发{leave.approval_level}级审批（时长超过4小时），需由管理员审批"
                )
            if leave.reviewer_id != current_user["id"]:
                raise HTTPException(status_code=403, detail="Reviewers can only approve leave requests of their assigned students")
        elif current_user["role"] == "admin":
            pass
        else:
            raise HTTPException(status_code=403, detail="Permission denied")

        # 三级审批(>24h)时强制要求审核意见
        if leave.approval_level == 3 and not audit_remarks:
            raise HTTPException(
                status_code=400,
                detail="超长请假(>24小时)必须填写审核意见"
            )

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

        # 审批通过后通知学生
        NotificationService.notify_leave_status_change(leave, "已批准", session)

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

        # 拒绝后通知学生
        NotificationService.notify_leave_status_change(leave, "已拒绝", session)

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

        NotificationService.notify_leave_status_change(leave, "已撤销", session)

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
                    if leave.approval_level > 1:
                        errors.append({"leave_id": leave_id, "error": f"该请假触发{leave.approval_level}级审批，需由管理员审批"})
                        continue
                    if leave.reviewer_id != current_user["id"]:
                        errors.append({"leave_id": leave_id, "error": "Not authorized"})
                        continue
                elif current_user["role"] != "admin":
                    errors.append({"leave_id": leave_id, "error": "Permission denied"})
                    continue

                # 三级审批强制要求审核意见
                if leave.approval_level == 3 and not audit_remarks:
                    errors.append({"leave_id": leave_id, "error": "超长请假(>24小时)必须填写审核意见"})
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

    @staticmethod
    def get_approval_recommendation(leave_id: int, session: Session) -> dict:
        """
        智能审批推荐：根据请假事由、历史频次、课程重要性打分
        返回: {score, verdict, verdict_label, factors}
        """
        leave = session.exec(
            select(Leave).where(Leave.leave_id == leave_id)
        ).first()

        if not leave:
            return {"error": "Leave not found"}

        score = 0  # 初始分值 0-100
        factors = []

        # ---------- 1. 请假类型评分 ----------
        leave_type_scores = {
            "病假": 20,
            "事假": 0,
            "公假": 10,
            "婚假": 15,
            "丧假": 15,
        }
        lt_score = leave_type_scores.get(leave.leave_type, 0)
        score += lt_score
        factors.append({
            "name": "请假类型",
            "value": leave.leave_type or "未填写",
            "score": lt_score,
            "max_score": 20,
            "reason": f"{leave.leave_type or '未填写'} +{lt_score}分" if lt_score > 0 else f"{leave.leave_type or '未填写'} +{lt_score}分",
        })

        # ---------- 2. 历史请假频次评分（近90天） ----------
        ninety_days_ago = datetime.now() - timedelta(days=90)
        recent_count = session.exec(
            select(func.count(Leave.leave_id)).where(
                Leave.student_id == leave.student_id,
                Leave.leave_date >= ninety_days_ago,
                Leave.leave_id != leave.leave_id,
            )
        ).one()
        freq_score = max(0, 30 - recent_count * 5)  # 每多1次扣5分，上限扣30分
        score += freq_score
        factors.append({
            "name": "历史请假频次",
            "value": f"近90天{recent_count}次",
            "score": freq_score,
            "max_score": 30,
            "reason": f"近90天请假{recent_count}次，{'无扣分' if recent_count == 0 else f'扣{freq_score}分'}",
        })

        # ---------- 3. 请假时长评分 ----------
        try:
            leave_hours = float(leave.leave_hours) if leave.leave_hours else 0
        except (ValueError, TypeError):
            leave_hours = 0
        if leave_hours <= 4:
            duration_score = 20
            duration_reason = "短期请假(≤4h) +20分"
        elif leave_hours <= 24:
            duration_score = 10
            duration_reason = "中期请假(4-24h) +10分"
        else:
            duration_score = 0
            duration_reason = "长期请假(>24h) +0分，需重点审核"
        score += duration_score
        factors.append({
            "name": "请假时长",
            "value": f"{leave_hours}小时",
            "score": duration_score,
            "max_score": 20,
            "reason": duration_reason,
        })

        # ---------- 4. 课程重要性评分 ----------
        course_score = 0
        if leave.course_id:
            course = session.exec(
                select(Course).where(Course.course_id == leave.course_id)
            ).first()
            if course:
                course_score = 10
                course_name = course.course_name
            else:
                course_name = "未知课程"
                course_score = 0
        else:
            course_name = "无课程"
            course_score = 5  # 无课程关联适当加分
        score += course_score
        factors.append({
            "name": "课程关联",
            "value": course_name,
            "score": course_score,
            "max_score": 10,
            "reason": f"关联课程{course_name} +{course_score}分",
        })

        # ---------- 5. 审批级别加成 ----------
        level_score = max(0, 20 - (leave.approval_level - 1) * 10)
        score += level_score
        factors.append({
            "name": "审批级别",
            "value": f"第{leave.approval_level}级",
            "score": level_score,
            "max_score": 20,
            "reason": f"触发第{leave.approval_level}级审批 +{level_score}分",
        })

        # ---------- 综合评级 ----------
        max_score = sum(f["max_score"] for f in factors)
        score = min(score, max_score)

        # 计算百分制
        score_pct = round(score / max_score * 100, 1) if max_score > 0 else 0

        if score_pct >= 80:
            verdict = "approve"
            verdict_label = "建议通过"
            verdict_reason = "综合评分较高，请假理由充分"
        elif score_pct >= 50:
            verdict = "verify"
            verdict_label = "建议核实"
            verdict_reason = "综合评分一般，建议核实情况后决定"
        else:
            verdict = "reject"
            verdict_label = "建议驳回"
            verdict_reason = "综合评分偏低，请假理由不充分"

        # 特殊豁免：病假/婚假/丧假无论分数都提升一级
        if leave.leave_type in ("病假", "婚假", "丧假"):
            if verdict == "reject":
                verdict = "verify"
                verdict_label = "建议核实"
                verdict_reason = f"因{leave.leave_type}特殊原因，转为建议核实"

        return {
            "leave_id": leave.leave_id,
            "score": score,
            "max_score": max_score,
            "score_pct": score_pct,
            "verdict": verdict,
            "verdict_label": verdict_label,
            "verdict_reason": verdict_reason,
            "factors": factors,
        }
