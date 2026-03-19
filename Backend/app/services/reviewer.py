from sqlmodel import Session, select, func
from fastapi import Depends, Query, HTTPException

from app.models import Reviewer, School, Role
from app.schemas import ReviewerCreate
from app.api.deps import check_login
from app.services.common import CommonService
from app.utils.password import hash_password


class ReviewerService:
    @staticmethod
    def get_reviewers(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        session: Session = Depends(lambda: None),
    ):
        """分页获取审核员列表"""
        reviewers, total, total_pages = CommonService.paginate_query(
            session, Reviewer, page, page_size
        )

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

        return items, total, total_pages

    @staticmethod
    def get_reviewers_count(session: Session):
        """获取审核员数量"""
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
