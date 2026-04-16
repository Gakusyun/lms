from sqlmodel import Session, select, func
from fastapi import Depends, Query, HTTPException
from sqlalchemy import and_, or_

from app.models import Reviewer, School, Role, Student
from app.schemas import ReviewerCreate
from app.api.deps import check_login
from app.services.common import CommonService
from app.utils.password import hash_password


class ReviewerService:
    @staticmethod
    def get_reviewers(
        current_user: dict,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        session: Session = Depends(lambda: None),
    ):
        """分页获取审核员列表（学生看自己辅导员+本院书记+学工处）"""
        query = select(Reviewer)

        if current_user["role"] == "student":
            student = session.exec(
                select(Student).where(Student.student_id == current_user["id"])
            ).first()
            if student:
                student_school_id = student.school_id
                student_reviewer_id = student.reviewer_id
            else:
                student_school_id = None
                student_reviewer_id = None

            # 找出该学生能看到的审核员条件
            # 1. 自己的辅导员
            # 2. 本学院的书记（仅限自己学校）
            # 3. 学工处（全校可见）
            conditions = []
            if student_reviewer_id:
                conditions.append(Reviewer.reviewer_id == student_reviewer_id)

            dean_role_ids = session.exec(
                select(Role.role_id).where(Role.role_name.like("%书记%"))
            ).all()
            if dean_role_ids:
                conditions.append(
                    and_(
                        Reviewer.school_id == student_school_id,
                        Reviewer.role_id.in_(dean_role_ids)
                    )
                )

            affairs_role_ids = session.exec(
                select(Role.role_id).where(Role.role_name.like("%学工处%"))
            ).all()
            if affairs_role_ids:
                conditions.append(Reviewer.role_id.in_(affairs_role_ids))

            if conditions:
                query = query.where(or_(*conditions))
            else:
                query = query.where(Reviewer.reviewer_id == -1)

        # 手动分页
        offset = (page - 1) * page_size
        all_reviewers = session.exec(query).all()
        total = len(all_reviewers)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        reviewers = all_reviewers[offset:offset + page_size]

        # 注入关联数据
        items = CommonService.inject_relations(
            session,
            reviewers,
            {
                "school_id": (
                    School,
                    "school_id",
                    "school_name",
                    "school_name",
                ),
                "role_id": (
                    Role,
                    "role_id",
                    "role_name",
                    "role_name",
                )
            },
        )
        # 过滤password字段
        for item in items:
            item.pop("password", None)
        return items, total, total_pages

    @staticmethod
    def get_reviewers_count(current_user: dict, session: Session):
        """获取审核员数量（学生：辅导员+本院书记+学工处，admin/reviewer返回全部）"""
        if current_user["role"] == "student":
            student = session.exec(
                select(Student).where(Student.student_id == current_user["id"])
            ).first()
            if not student:
                return {"reviewers_count": 0}
            student_school_id = student.school_id
            student_reviewer_id = student.reviewer_id

            count = 0
            # 自己的辅导员
            if student_reviewer_id:
                count += 1
            # 本学院书记
            if student_school_id:
                dean_count = session.exec(
                    select(func.count(Reviewer.reviewer_id))
                    .join(Role, Reviewer.role_id == Role.role_id)
                    .where(Reviewer.school_id == student_school_id)
                    .where(Role.role_name.like("%书记%"))
                ).one()
                count += dean_count
            # 学工处
            affairs_count = session.exec(
                select(func.count(Reviewer.reviewer_id))
                .join(Role, Reviewer.role_id == Role.role_id)
                .where(Role.role_name.like("%学工处%"))
            ).one()
            count += affairs_count
            return {"reviewers_count": count}
        else:
            return {
                "reviewers_count": session.exec(
                    select(func.count(Reviewer.reviewer_id))
                ).one()
            }

    @staticmethod
    def get_reviewer_by_id(reviewer_id: int, session: Session):
        """根据ID获取审核员"""
        return CommonService.get_by_id(session, Reviewer, reviewer_id, "reviewer_id")

    @staticmethod
    def create_reviewer(
        reviewer_data: ReviewerCreate,
        session: Session,
    ):
        """创建审核员"""
        # 检查审核员是否已存在
        existing_reviewer = session.exec(
            select(Reviewer).where(Reviewer.reviewer_id == reviewer_data.reviewer_id)
        ).first()
        if existing_reviewer:
            raise HTTPException(status_code=400, detail="Reviewer with this ID already exists")
        
        reviewer = Reviewer(**reviewer_data.model_dump())
        if reviewer.password:
            reviewer.password = hash_password(reviewer.password)
        session.add(reviewer)
        session.commit()
        session.refresh(reviewer)
        return reviewer

    @staticmethod
    def update_reviewer(
        reviewer_id: int,
        reviewer_data: ReviewerCreate,
        session: Session,
    ):
        """编辑审核员"""
        # 获取审核员
        reviewer = CommonService.get_by_id(session, Reviewer, reviewer_id, "reviewer_id")
        
        # 更新审核员信息
        update_data = reviewer_data.model_dump(exclude_unset=True)
        
        # 如果更新密码，需要哈希处理
        if "password" in update_data and update_data["password"]:
            update_data["password"] = hash_password(update_data["password"])
        
        for key, value in update_data.items():
            setattr(reviewer, key, value)
        
        session.commit()
        session.refresh(reviewer)
        return reviewer

    @staticmethod
    def delete_reviewer(
        reviewer_id: int,
        session: Session,
    ):
        """删除审核员"""
        # 获取审核员
        reviewer = CommonService.get_by_id(session, Reviewer, reviewer_id, "reviewer_id")
        
        # 检查是否有学生关联
        from app.models import Student
        student_count = session.exec(
            select(func.count(Student.student_id)).where(Student.reviewer_id == reviewer_id)
        ).one()
        
        if student_count > 0:
            raise HTTPException(status_code=400, detail="Cannot delete reviewer with assigned students")
        
        session.delete(reviewer)
        session.commit()
        return {"message": "Reviewer deleted successfully"}
