from sqlmodel import Session, select, func
from fastapi import Depends, HTTPException, Query
from datetime import datetime
import io

from app.models import Student, Reviewer, School, Role
from app.schemas import StudentCreate
from app.services.common import CommonService
from app.utils.jwt import get_password_hash


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


class StudentService:
    @staticmethod
    def get_students(
        current_user: dict,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        session: Session = None,
    ):
        """分页获取学生列表"""
        obj = current_user

        # 只允许审核员查看全部学生列表
        if obj["role"] == "teacher":
            raise HTTPException(status_code=403, detail="Permission denied")

        # 构建查询条件
        query = select(Student)

        # 如果是审核员，根据角色显示不同范围的学生
        if obj["role"] == "reviewer":
            reviewer = session.exec(
                select(Reviewer).where(Reviewer.reviewer_id == obj["id"])
            ).first()
            if reviewer:
                role_name = get_reviewer_role_name(reviewer, session)
                reviewer_school_id = get_reviewer_school_id(reviewer)
                if "学工处" in role_name or "处长" in role_name:
                    # 学工处/处长：看全校所有学生（不筛选）
                    pass
                elif "书记" in role_name:
                    # 书记：看本学院所有学生
                    query = query.where(Student.school_id == reviewer_school_id)
                elif "辅导员" in role_name:
                    # 辅导员：只看自己负责的学生
                    query = query.where(Student.reviewer_id == obj["id"])
                else:
                    # 其他角色：只显示自己负责的学生
                    query = query.where(Student.reviewer_id == obj["id"])
            else:
                query = query.where(Student.reviewer_id == obj["id"])

        elif obj["role"] == "student":
            query = query.where(Student.student_id == obj["id"])

        # 应用分页
        offset = (page - 1) * page_size
        students = session.exec(query.offset(offset).limit(page_size)).all()

        # 计算总数
        pk_col = list(Student.__table__.primary_key.columns)[0]
        total_stmt = select(func.count(pk_col))
        if obj["role"] == "reviewer":
            reviewer = session.exec(
                select(Reviewer).where(Reviewer.reviewer_id == obj["id"])
            ).first()
            if reviewer:
                role_name = get_reviewer_role_name(reviewer, session)
                reviewer_school_id = get_reviewer_school_id(reviewer)
                if "学工处" in role_name or "处长" in role_name:
                    # 学工处/处长：统计全校所有学生（不筛选）
                    pass
                elif "书记" in role_name:
                    # 书记：统计本学院所有学生
                    total_stmt = total_stmt.where(Student.school_id == reviewer_school_id)
                elif "辅导员" in role_name:
                    # 辅导员：只统计自己负责的学生
                    total_stmt = total_stmt.where(Student.reviewer_id == obj["id"])
                else:
                    # 其他角色：只统计自己负责的学生
                    total_stmt = total_stmt.where(Student.reviewer_id == obj["id"])
            else:
                total_stmt = total_stmt.where(Student.reviewer_id == obj["id"])
        total = session.exec(total_stmt).one()

        total_pages = (total + page_size - 1) // page_size

        items = CommonService.inject_relations(
            session,
            students,
            {
                "reviewer_id": (
                    Reviewer,
                    "reviewer_id",
                    "reviewer_name",
                    "reviewer_name",
                ),
                "school_id": (
                    School,
                    "school_id",
                    "school_name",
                    "school_name",
                )
            },
        )
        # 过滤password字段
        for item in items:
            item.pop("password", None)
        return items, total, total_pages

    @staticmethod
    def get_students_count(current_user: dict, session: Session):
        """获取学生数量"""
        obj = current_user
        if obj["role"] == "admin":
            count = session.exec(select(func.count(Student.student_id))).one()
            return {"students_count": count}
        elif obj["role"] == "teacher":
            raise HTTPException(status_code=403, detail="Permission denied")
        elif obj["role"] == "student":
            return {"students_count": "自己"}
        else:
            # 修复：根据角色正确计算学生数量
            reviewer = session.exec(
                select(Reviewer).where(Reviewer.reviewer_id == obj["id"])
            ).first()
            if reviewer:
                role_name = get_reviewer_role_name(reviewer, session)
                reviewer_school_id = get_reviewer_school_id(reviewer)
                if "学工处" in role_name or "处长" in role_name:
                    # 学工处/处长：统计全校所有学生
                    count = session.exec(select(func.count(Student.student_id))).one()
                elif "书记" in role_name:
                    # 书记：统计本学院所有学生
                    count = session.exec(
                        select(func.count(Student.student_id)).where(
                            Student.school_id == reviewer_school_id
                        )
                    ).one()
                elif "辅导员" in role_name:
                    # 辅导员：只统计自己负责的学生
                    count = session.exec(
                        select(func.count(Student.student_id)).where(
                            Student.reviewer_id == obj["id"]
                        )
                    ).one()
                else:
                    # 其他角色：只统计自己负责的学生
                    count = session.exec(
                        select(func.count(Student.student_id)).where(
                            Student.reviewer_id == obj["id"]
                        )
                    ).one()
            else:
                count = session.exec(
                    select(func.count(Student.student_id)).where(
                        Student.reviewer_id == obj["id"]
                    )
                ).one()
            return {"students_count": count}

    @staticmethod
    def get_student_by_id(current_user: dict, student_id: int, session: Session):
        """根据ID获取学生"""
        obj = current_user
        if obj["role"] == "student":
            if obj["id"] != student_id:
                raise HTTPException(status_code=403, detail="Permission denied")
            else:
                return CommonService.get_by_id(
                    session, Student, student_id, "student_id"
                )
        return CommonService.get_by_id(session, Student, student_id, "student_id")

    @staticmethod
    def create_student(
        current_user: dict,
        student_data: StudentCreate,
        session: Session,
    ):
        """创建学生"""
        obj = current_user
        if obj["role"] not in ["reviewer", "admin"]:
            raise HTTPException(status_code=403, detail="Permission denied")

        # 检查学生是否已存在
        existing_student = session.exec(
            select(Student).where(Student.student_id == student_data.student_id)
        ).first()
        if existing_student:
            raise HTTPException(status_code=400, detail="Student already exists")

        student = Student(**student_data.model_dump())
        if student.password:
            student.password = get_password_hash(student.password)
        session.add(student)
        session.commit()
        session.refresh(student)
        return student

    @staticmethod
    def batch_import_students(current_user: dict, file, session: Session):
        """批量导入学生数据 (Excel或CSV)"""
        from app.services.audit_log import AuditLogService, AuditAction
        from app.utils.jwt import get_password_hash

        filename = file.filename or ""
        content = file.file.read()

        if filename.endswith(('.xlsx', '.xls')):
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(min_row=2, values_only=True))
        elif filename.endswith('.csv'):
            text = content.decode('utf-8-sig')
            import csv as csv_mod
            reader = csv_mod.reader(io.StringIO(text))
            rows = list(reader)
        else:
            raise HTTPException(
                status_code=400,
                detail="不支持的文件格式，请使用 .xlsx 或 .csv 文件"
            )

        if not rows:
            raise HTTPException(status_code=400, detail="文件内容为空")

        imported = []
        errors = []
        skipped = 0

        for idx, row in enumerate(rows):
            try:
                if not row or len(row) < 2:
                    errors.append({"row": idx + 2, "error": "数据不完整，至少需要 student_id 和 student_name"})
                    continue

                student_id = int(row[0])
                student_name = str(row[1]).strip()
                if not student_name:
                    errors.append({"row": idx + 2, "error": "学生姓名不能为空"})
                    continue

                password = str(row[2]).strip() if len(row) > 2 and row[2] else "123456"
                school_id = int(row[3]) if len(row) > 3 and row[3] else None
                reviewer_id = int(row[4]) if len(row) > 4 and row[4] else None

                # guarantee_permission: 0或空表示从未处罚有权限（无截止时间），其他时间戳表示处罚截止时间
                guarantee_permission = None
                if len(row) > 5 and row[5]:
                    try:
                        val = int(row[5])
                        # 0表示从未被处罚，有担保权限，保持None（无时间限制）
                        # 其他正数表示处罚截止时间
                        if val != 0:
                            guarantee_permission = datetime.fromtimestamp(val) if val > 0 else None
                    except (ValueError, TypeError):
                        guarantee_permission = None

                # 检查是否已存在
                existing = session.exec(
                    select(Student).where(Student.student_id == student_id)
                ).first()
                if existing:
                    skipped += 1
                    continue

                student = Student(
                    student_id=student_id,
                    student_name=student_name,
                    password=get_password_hash(password),
                    school_id=school_id,
                    reviewer_id=reviewer_id,
                    guarantee_permission=guarantee_permission,
                )
                session.add(student)
                imported.append({"student_id": student_id, "student_name": student_name})
            except (ValueError, TypeError) as e:
                errors.append({"row": idx + 2, "error": f"数据格式错误: {str(e)}"})
            except Exception as e:
                errors.append({"row": idx + 2, "error": str(e)})

        session.commit()

        AuditLogService.log(
            current_user=current_user,
            action=AuditAction.USER_CREATE,
            target_type="student",
            detail=f"批量导入学生 {len(imported)} 条，跳过 {skipped} 条，失败 {len(errors)} 条",
            session=session,
        )

        return {
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
            "total": len(rows),
            "success_count": len(imported),
            "error_count": len(errors),
        }
