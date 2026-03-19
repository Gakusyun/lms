from sqlmodel import Session, select, func
from fastapi import HTTPException
from datetime import datetime, timedelta

from app.models import Leave, Student, Teacher, Course, Reviewer, StudentCourse
from app.api.deps import check_login


class StatisticsService:
    @staticmethod
    def get_leave_statistics(token: str, session: Session):
        """获取请假统计数据"""
        obj = check_login(token, session)
        
        # 构建基础查询
        query = select(
            Leave.status,
            func.count(Leave.leave_id).label('count')
        ).group_by(Leave.status)
        
        # 根据角色应用不同的过滤条件
        if obj["role"] == "student":
            query = query.where(Leave.student_id == obj["id"])
        elif obj["role"] == "reviewer":
            query = query.where(Leave.reviewer_id == obj["id"])
        elif obj["role"] == "teacher":
            # 获取教师教授的课程ID列表
            course_ids = session.exec(
                select(Course.course_id).where(Course.teacher_id == obj["id"])
            ).all()
            if course_ids:
                query = query.where(Leave.course_id.in_(course_ids))
            else:
                # 如果教师没有教授任何课程，则返回空结果
                return {"leave_statistics": []}
        
        results = session.exec(query).all()
        
        # 转换为字典格式
        leave_statistics = [
            {"status": result.status, "count": result.count}
            for result in results
        ]
        
        return {"leave_statistics": leave_statistics}
    
    @staticmethod
    def get_leave_trend(token: str, days: int, session: Session):
        """获取请假趋势数据"""
        obj = check_login(token, session)
        
        # 计算开始日期
        start_date = datetime.now() - timedelta(days=days)
        
        # 构建基础查询
        query = select(
            func.date(Leave.leave_date).label('date'),
            func.count(Leave.leave_id).label('count')
        ).where(
            Leave.leave_date >= start_date
        ).group_by(
            func.date(Leave.leave_date)
        ).order_by(
            func.date(Leave.leave_date)
        )
        
        # 根据角色应用不同的过滤条件
        if obj["role"] == "student":
            query = query.where(Leave.student_id == obj["id"])
        elif obj["role"] == "reviewer":
            query = query.where(Leave.reviewer_id == obj["id"])
        elif obj["role"] == "teacher":
            # 获取教师教授的课程ID列表
            course_ids = session.exec(
                select(Course.course_id).where(Course.teacher_id == obj["id"])
            ).all()
            if course_ids:
                query = query.where(Leave.course_id.in_(course_ids))
            else:
                # 如果教师没有教授任何课程，则返回空结果
                return {"leave_trend": []}
        
        results = session.exec(query).all()
        
        # 转换为字典格式
        leave_trend = [
            {"date": result.date.isoformat(), "count": result.count}
            for result in results
        ]
        
        return {"leave_trend": leave_trend}
    
    @staticmethod
    def get_course_enrollment_statistics(token: str, session: Session):
        """获取课程选课统计数据"""
        obj = check_login(token, session)
        
        # 只有管理员和教师可以查看课程选课统计
        if obj["role"] not in ["admin", "teacher"]:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # 构建基础查询
        query = select(
            Course.course_id,
            Course.course_name,
            func.count(StudentCourse.student_id).label('enrollment_count')
        ).outerjoin(
            StudentCourse, Course.course_id == StudentCourse.course_id
        ).group_by(
            Course.course_id, Course.course_name
        )
        
        # 如果是教师，只能查看自己的课程
        if obj["role"] == "teacher":
            query = query.where(Course.teacher_id == obj["id"])
        
        results = session.exec(query).all()
        
        # 转换为字典格式
        enrollment_statistics = [
            {
                "course_id": result.course_id,
                "course_name": result.course_name,
                "enrollment_count": result.enrollment_count
            }
            for result in results
        ]
        
        return {"enrollment_statistics": enrollment_statistics}
    
    @staticmethod
    def get_user_statistics(session: Session):
        """获取用户统计数据"""
        # 统计各类用户数量
        student_count = session.exec(select(func.count(Student.student_id))).one()
        teacher_count = session.exec(select(func.count(Teacher.teacher_id))).one()
        reviewer_count = session.exec(select(func.count(Reviewer.reviewer_id))).one()
        
        return {
            "user_statistics": {
                "students": student_count,
                "teachers": teacher_count,
                "reviewers": reviewer_count
            }
        }
    
    @staticmethod
    def get_reviewer_performance(token: str, session: Session):
        """获取审核员绩效统计"""
        obj = check_login(token, session)
        
        # 只有管理员可以查看审核员绩效
        if obj["role"] != "admin":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # 构建查询
        query = select(
            Reviewer.reviewer_id,
            Reviewer.reviewer_name,
            func.count(Leave.leave_id).label('total_leaves'),
            func.sum(func.case((Leave.status == "已批准", 1), else_=0)).label('approved_leaves'),
            func.sum(func.case((Leave.status == "已拒绝", 1), else_=0)).label('rejected_leaves')
        ).outerjoin(
            Leave, Reviewer.reviewer_id == Leave.reviewer_id
        ).group_by(
            Reviewer.reviewer_id, Reviewer.reviewer_name
        )
        
        results = session.exec(query).all()
        
        # 转换为字典格式
        reviewer_performance = [
            {
                "reviewer_id": result.reviewer_id,
                "reviewer_name": result.reviewer_name,
                "total_leaves": result.total_leaves,
                "approved_leaves": result.approved_leaves,
                "rejected_leaves": result.rejected_leaves,
                "approval_rate": round(result.approved_leaves / result.total_leaves * 100, 2) if result.total_leaves > 0 else 0
            }
            for result in results
        ]
        
        return {"reviewer_performance": reviewer_performance}
