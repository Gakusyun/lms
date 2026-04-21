from sqlmodel import Session, select, func
from fastapi import Depends, Query, HTTPException
import io

from app.models import School
from app.services.common import CommonService


class SchoolService:
    @staticmethod
    def get_schools(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        session: Session = Depends(lambda: None),
    ):
        """分页获取学校/院系列表"""
        schools, total, total_pages = CommonService.paginate_query(
            session, School, page, page_size
        )
        return schools, total, total_pages

    @staticmethod
    def get_schools_count(session: Session):
        """获取学校/院系数量"""
        return {
            "schools_count": session.exec(
                select(func.count(School.school_id))
            ).one()
        }

    @staticmethod
    def get_school_by_id(school_id: int, session: Session):
        """根据ID获取学校/院系"""
        return CommonService.get_by_id(session, School, school_id, "school_id")

    @staticmethod
    def create_school(school_data: dict, session: Session):
        """创建学校/院系（自动分配ID）"""
        school_name = school_data.get("school_name")
        if not school_name:
            raise HTTPException(status_code=400, detail="部门名称不能为空")

        # 自动生成下一个 school_id
        max_id = session.exec(select(func.max(School.school_id))).one()
        school_id = (max_id or 0) + 1

        school = School(school_id=school_id, school_name=school_name)
        session.add(school)
        session.commit()
        session.refresh(school)
        return school

    @staticmethod
    def get_or_create_school_by_name(school_name: str, session: Session) -> School:
        """根据名称获取或创建学校/院系"""
        school = session.exec(
            select(School).where(School.school_name == school_name)
        ).first()
        if not school:
            # 创建新学校，使用自增ID
            school = School(school_name=school_name)
            session.add(school)
            session.commit()
            session.refresh(school)
        return school

    @staticmethod
    def batch_import_schools(current_user: dict, file, session: Session):
        """批量导入部门数据 (Excel或CSV)"""
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

        for idx, row in enumerate(rows):
            try:
                if not row or len(row) < 1:
                    errors.append({"row": idx + 2, "error": "数据不完整"})
                    continue

                school_name = str(row[0]).strip()
                if not school_name:
                    errors.append({"row": idx + 2, "error": "部门名称不能为空"})
                    continue

                # 检查是否已存在
                existing = session.exec(
                    select(School).where(School.school_name == school_name)
                ).first()
                if existing:
                    errors.append({"row": idx + 2, "error": f"部门「{school_name}」已存在"})
                    continue

                # 自动生成下一个 school_id
                max_id = session.exec(select(func.max(School.school_id))).one()
                school_id = (max_id or 0) + 1

                school = School(school_id=school_id, school_name=school_name)
                session.add(school)
                session.commit()
                session.refresh(school)
                imported.append({"school_id": school.school_id, "school_name": school.school_name})

            except Exception as e:
                errors.append({"row": idx + 2, "error": str(e)})

        return {
            "imported": imported,
            "total": len(imported),
            "errors": errors
        }
