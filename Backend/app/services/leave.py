import re
import os
from sqlmodel import Session, select, func
from fastapi import Depends, Query, HTTPException, UploadFile, File, Request
from datetime import datetime, timedelta
from typing import List

from app.models import Leave, Student, Reviewer, Teacher, Course, School, Role, AuditAction
from app.services.student_course import StudentCourseService
from app.schemas import LeaveCreate
from app.services.common import CommonService
from app.services.audit_log import AuditLogService
from app.services.notification import NotificationService

# 上传文件存储目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 审批层级对应的课时阈值
APPROVAL_LEVEL_1_THRESHOLD = 8    # ≤8课时：辅导员审批
APPROVAL_LEVEL_2_THRESHOLD = 56   # 8-56课时：书记审批


def get_reviewer_role_name(reviewer: Reviewer, session: Session) -> str:
    """获取审核员的角色名称"""
    if not reviewer or not reviewer.role_id:
        return ""
    role = session.exec(select(Role).where(Role.role_id == reviewer.role_id)).first()
    return role.role_name if role else ""


def parse_leave_hours(leave_hours_str) -> float:
    """从leave_hours字符串中解析出数字（支持 '8'、'8课时' 等格式）"""
    if not leave_hours_str:
        return 0
    try:
        return float(str(leave_hours_str))
    except (ValueError, TypeError):
        # 尝试从字符串中提取数字
        match = re.search(r'[\d.]+', str(leave_hours_str))
        return float(match.group()) if match else 0


def get_reviewer_role_name(reviewer, session: Session) -> str:
    """获取审核员的职务名称"""
    if reviewer.role_id:
        role = session.exec(
            select(Role).where(Role.role_id == reviewer.role_id)
        ).first()
        if role:
            return role.role_name
    return ""


def get_reviewer_school_id(reviewer) -> int:
    """获取审核员的院系ID"""
    return reviewer.school_id or 0


class LeaveService:
    @staticmethod
    def get_leaves(
        current_user: dict,
        page: int = 1,
        page_size: int = 20,
        session: Session = None,
        scope: str = None,
    ):
        """分页获取请假记录
        scope=school: 书记/学工处查看本院所有待审批（可代审）
        """
        query = select(Leave)

        # scope=school: 本院所有待审批（书记/学工处代审用）
        if scope == "school" and current_user["role"] == "reviewer":
            reviewer = session.exec(
                select(Reviewer).where(Reviewer.reviewer_id == current_user["id"])
            ).first()
            if reviewer:
                role_name = get_reviewer_role_name(reviewer, session)
                reviewer_school_id = get_reviewer_school_id(reviewer)
                if "书记" in role_name:
                    # 书记：看本学院所有请假（所有状态）
                    school_student_ids = session.exec(
                        select(Student.student_id).where(Student.school_id == reviewer_school_id)
                    ).all()
                    if school_student_ids:
                        query = query.where(Leave.student_id.in_(school_student_ids))
                    else:
                        query = query.where(Leave.leave_id == -1)
                elif "学工处" in role_name:
                    # 学工处：看全校所有请假（所有状态）
                    pass  # 不过滤状态
                else:
                    # 辅导员不看scope=school
                    query = query.where(Leave.leave_id == -1)
            else:
                query = query.where(Leave.leave_id == -1)

            # 手动分页
            offset = (page - 1) * page_size
            all_leaves = session.exec(query.order_by(Leave.leave_date.desc())).all()
            total = len(all_leaves)
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0
            leaves = all_leaves[offset:offset + page_size]

            items = CommonService.inject_relations(
                session, leaves,
                {
                    "student_id": (Student, "student_id", "student_name", "student_name"),
                    "reviewer_id": (Reviewer, "reviewer_id", "reviewer_name", "reviewer_name"),
                    "teacher_id": (Teacher, "teacher_id", "teacher_name", "teacher_name"),
                    "guarantee_student_id": (Student, "student_id", "student_name", "guarantee_student_name"),
                },
            )
            for item in items:
                item.pop("password", None) if "password" in item else None
            return items, total, total_pages

        # 普通查询（非scope=school）
        if current_user["role"] == "student":
            query = query.where(Leave.student_id == current_user["id"])
        elif current_user["role"] == "reviewer":
            reviewer = session.exec(
                select(Reviewer).where(Reviewer.reviewer_id == current_user["id"])
            ).first()
            role_name = get_reviewer_role_name(reviewer, session) if reviewer else ""
            reviewer_school_id = get_reviewer_school_id(reviewer) if reviewer else 0

            if "辅导员" in role_name:
                # 辅导员只看自己直属学生的请假
                query = query.where(Leave.reviewer_id == current_user["id"])
            elif "书记" in role_name:
                # 书记看本学院所有请假
                school_student_ids = session.exec(
                    select(Student.student_id).where(Student.school_id == reviewer_school_id)
                ).all()
                if school_student_ids:
                    query = query.where(Leave.student_id.in_(school_student_ids))
                else:
                    query = query.where(Leave.student_id == -1)  # no results
            else:
                # 学工处/其他角色看全校请假
                pass  # no filter
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
            reviewer = session.exec(
                select(Reviewer).where(Reviewer.reviewer_id == current_user["id"])
            ).first()
            role_name = get_reviewer_role_name(reviewer, session) if reviewer else ""
            reviewer_school_id = get_reviewer_school_id(reviewer) if reviewer else 0

            if "辅导员" in role_name:
                total_stmt = total_stmt.where(Leave.reviewer_id == current_user["id"])
            elif "书记" in role_name:
                school_student_ids = session.exec(
                    select(Student.student_id).where(Student.school_id == reviewer_school_id)
                ).all()
                if school_student_ids:
                    total_stmt = total_stmt.where(Leave.student_id.in_(school_student_ids))
                else:
                    total_stmt = total_stmt.where(Leave.student_id == -1)
            else:
                pass
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
            reviewer = session.exec(
                select(Reviewer).where(Reviewer.reviewer_id == current_user["id"])
            ).first()
            role_name = get_reviewer_role_name(reviewer, session) if reviewer else ""
            reviewer_school_id = get_reviewer_school_id(reviewer) if reviewer else 0

            if "辅导员" in role_name:
                count = session.exec(
                    select(func.count(Leave.leave_id)).where(Leave.reviewer_id == current_user["id"])
                ).one()
            elif "书记" in role_name:
                school_student_ids = session.exec(
                    select(Student.student_id).where(Student.school_id == reviewer_school_id)
                ).all()
                if school_student_ids:
                    count = session.exec(
                        select(func.count(Leave.leave_id)).where(Leave.student_id.in_(school_student_ids))
                    ).one()
                else:
                    count = 0
            else:
                # 学工处/其他看全校
                count = session.exec(select(func.count(Leave.leave_id))).one()
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
        request: Request = None,
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

        # 2.2 历史请假频次校验：统计该学生近30天请假次数（排除已撤销）
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_leaves_count = session.exec(
            select(func.count(Leave.leave_id)).where(
                Leave.student_id == leave_dict["student_id"],
                Leave.leave_date >= thirty_days_ago,
                Leave.status.not_in(["已撤销"]),
            )
        ).one()
        if recent_leaves_count >= 5:
            raise HTTPException(
                status_code=400,
                detail=f"请假频次超限：该学生近30天已有 {recent_leaves_count} 次请假记录，请联系审核员"
            )

        # 2.4 紧急请假担保人关联校验：被担保人和担保人都需要在有效期内
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
            # 被担保学生本人也需要有有效的担保权限
            if not student.guarantee_permission or student.guarantee_permission < datetime.now():
                raise HTTPException(
                    status_code=400,
                    detail="你当前无担保权限或权限已过期，不能发起紧急请假"
                )

        # 2.3 时长分级审批路由：按请假课时分配不同审批层级
        # ≤8课时：辅导员审批 | 8-56课时：书记审批 | >56课时：学工处审批
        leave_hours = parse_leave_hours(leave_dict.get("leave_hours"))

        if leave_hours <= APPROVAL_LEVEL_1_THRESHOLD:
            leave_dict["approval_level"] = 1
        elif leave_hours <= APPROVAL_LEVEL_2_THRESHOLD:
            leave_dict["approval_level"] = 2
        else:
            leave_dict["approval_level"] = 3

        # 二级及以上审批时，记录备注提示
        if leave_dict["approval_level"] >= 2:
            level_labels = {2: "学院书记", 3: "学工处"}
            level_msg = f"请假{leave_hours}课时，需{level_labels[leave_dict['approval_level']]}审批"
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
            request=request,
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
        request: Request = None,
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
            request=request,
            session=session,
        )
        return leave

    @staticmethod
    def approve_leave(
        current_user: dict,
        leave_id: int,
        audit_remarks: str,
        session: Session,
        request: Request = None,
    ):
        """批准请假 - 基于审核员角色分级审批"""
        leave = session.exec(
            select(Leave).where(Leave.leave_id == leave_id)
        ).first()

        if not leave:
            raise HTTPException(status_code=404, detail="Leave record not found")

        if leave.status != "待审批":
            raise HTTPException(status_code=403, detail="Only pending leave requests can be approved")

        if current_user["role"] == "reviewer":
            reviewer = session.exec(
                select(Reviewer).where(Reviewer.reviewer_id == current_user["id"])
            ).first()
            if not reviewer:
                raise HTTPException(status_code=403, detail="Reviewer not found")

            role_name = get_reviewer_role_name(reviewer, session)
            reviewer_school_id = get_reviewer_school_id(reviewer)

            # 辅导员：只能审批≤8课时（一级）
            if "辅导员" in role_name:
                if leave.approval_level > 1:
                    raise HTTPException(
                        status_code=403,
                        detail=f"该请假{leave.leave_hours}触发二级审批，需由学院书记审批"
                    )
                if leave.reviewer_id != current_user["id"]:
                    raise HTTPException(status_code=403, detail="辅导员只能审批自己直属学生的请假")
            # 书记：可审批≤56课时（一级、二级）
            elif "书记" in role_name:
                if leave.approval_level > 2:
                    raise HTTPException(
                        status_code=403,
                        detail=f"该请假{leave.leave_hours}触发三级审批，需由学工处审批"
                    )
                # 验证是本学院的请假
                leave_student = session.exec(
                    select(Student).where(Student.student_id == leave.student_id)
                ).first()
                if leave_student and leave_student.school_id != reviewer_school_id:
                    raise HTTPException(status_code=403, detail="只能审批本学院的请假申请")
            # 学工处/其他：可审批所有级别
            # no additional check needed
        elif current_user["role"] == "admin":
            pass
        else:
            raise HTTPException(status_code=403, detail="Permission denied")

        # 三级审批(>56课时)时强制要求审核意见
        if leave.approval_level == 3 and not audit_remarks:
            raise HTTPException(
                status_code=400,
                detail="超长请假(>56课时)必须填写审核意见"
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
            request=request,
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
        request: Request = None,
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
            request=request,
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
        request: Request = None,
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
            request=request,
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
        request: Request = None,
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
                    reviewer = session.exec(
                        select(Reviewer).where(Reviewer.reviewer_id == current_user["id"])
                    ).first()
                    role_name = get_reviewer_role_name(reviewer, session) if reviewer else ""
                    reviewer_school_id = get_reviewer_school_id(reviewer) if reviewer else 0

                    if "辅导员" in role_name:
                        if leave.approval_level > 1:
                            errors.append({"leave_id": leave_id, "error": f"需由学院书记审批"})
                            continue
                        if leave.reviewer_id != current_user["id"]:
                            errors.append({"leave_id": leave_id, "error": "Not authorized"})
                            continue
                    elif "书记" in role_name:
                        if leave.approval_level > 2:
                            errors.append({"leave_id": leave_id, "error": f"需由学工处审批"})
                            continue
                        leave_student = session.exec(
                            select(Student).where(Student.student_id == leave.student_id)
                        ).first()
                        if leave_student and leave_student.school_id != reviewer_school_id:
                            errors.append({"leave_id": leave_id, "error": "Not authorized - different school"})
                            continue
                elif current_user["role"] != "admin":
                    errors.append({"leave_id": leave_id, "error": "Permission denied"})
                    continue

                # 三级审批强制要求审核意见
                if leave.approval_level == 3 and not audit_remarks:
                    errors.append({"leave_id": leave_id, "error": "超长请假(>56课时)必须填写审核意见"})
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
            request=request,
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
        request: Request = None,
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
            request=request,
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
        leave_hours = parse_leave_hours(leave.leave_hours)
        if leave_hours <= APPROVAL_LEVEL_1_THRESHOLD:
            duration_score = 20
            duration_reason = f"短期请假(≤{APPROVAL_LEVEL_1_THRESHOLD}课时) +20分"
        elif leave_hours <= APPROVAL_LEVEL_2_THRESHOLD:
            duration_score = 10
            duration_reason = f"中期请假({APPROVAL_LEVEL_1_THRESHOLD}-{APPROVAL_LEVEL_2_THRESHOLD}课时) +10分"
        else:
            duration_score = 0
            duration_reason = f"长期请假(>{APPROVAL_LEVEL_2_THRESHOLD}课时) +0分，需重点审核"
        score += duration_score
        factors.append({
            "name": "请假时长",
            "value": f"{leave_hours}课时",
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

    @staticmethod
    def close_off_leave(
        current_user: dict,
        leave_id: int,
        session: Session,
        request: Request = None,
        ip_address: str = None,
    ):
        """销假 - 辅导员确认学生已返校报到，请假流程闭环"""
        leave = session.exec(select(Leave).where(Leave.leave_id == leave_id)).first()

        if not leave:
            raise HTTPException(status_code=404, detail="Leave record not found")

        if leave.status != "已批准":
            raise HTTPException(status_code=403, detail="只能对已批准的请假进行销假操作")

        if current_user["role"] == "reviewer":
            reviewer = session.exec(
                select(Reviewer).where(Reviewer.reviewer_id == current_user["id"])
            ).first()
            role_name = get_reviewer_role_name(reviewer, session) if reviewer else ""
            # 辅导员可以销假（学生向辅导员报到）
            if "辅导员" not in role_name and "书记" not in role_name:
                raise HTTPException(status_code=403, detail="只有辅导员或书记可以执行销假操作")
        elif current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Permission denied")

        leave.status = "已销假"
        leave.audit_time = datetime.now()

        session.commit()
        session.refresh(leave)

        AuditLogService.log(
            current_user=current_user,
            action="close_off",
            target_type="leave",
            target_id=leave.leave_id,
            detail="销假：学生已返校报到",
            ip_address=ip_address,
            request=request,
            session=session,
        )

        NotificationService.notify_leave_status_change(leave, "已销假", session)

        return leave

    @staticmethod
    async def upload_file(file: UploadFile, session: Session = None) -> dict:
        """上传证明文件"""
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")

        # 安全检查：只允许图片和文档
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".pdf", ".doc", ".docx"}
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")

        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        safe_name = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_name)

        # 保存文件
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # 返回相对路径用于存储到 materials 字段
        return {
            "file_path": f"uploads/{safe_name}",
            "file_name": file.filename,
            "file_size": len(content),
        }

    @staticmethod
    async def upload_leave_files(leave_id: int, files: List[UploadFile], session: Session = None) -> dict:
        """上传请假证明文件（关联到请假条，使用leave_id作为文件夹）"""
        from sqlmodel import select
        from app.models import Leave

        # 验证请假条是否存在
        if session is None:
            from app.database.connection import engine
            with Session(engine) as temp_session:
                leave = temp_session.exec(
                    select(Leave).where(Leave.leave_id == leave_id)
                ).first()
        else:
            leave = session.exec(
                select(Leave).where(Leave.leave_id == leave_id)
            ).first()
        if not leave:
            raise HTTPException(status_code=404, detail="请假记录不存在")

        # 创建以leave_id命名的文件夹
        leave_folder = os.path.join(UPLOAD_DIR, str(leave_id))
        os.makedirs(leave_folder, exist_ok=True)

        # 安全检查：只允许图片和文档
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".pdf", ".doc", ".docx"}

        uploaded_files = []
        for file in files:
            if not file.filename:
                continue
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in allowed_extensions:
                continue

            # 生成 UUID 文件名（无序、不可预测）
            import uuid
            uuid_name = f"{uuid.uuid4().hex}{ext}"
            file_path = os.path.join(leave_folder, uuid_name)

            # 保存文件
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            uploaded_files.append({
                "file_path": f"uploads/{leave_id}/{uuid_name}",
                "file_name": file.filename,
                "file_size": len(content),
            })

        return {
            "leave_id": leave_id,
            "files": uploaded_files,
            "count": len(uploaded_files),
        }
