#!/usr/bin/env python3
"""
插入测试数据的脚本
用于在LMS系统中创建测试数据
"""

import sys
import os
from datetime import datetime, timedelta
import random
from sqlmodel import Session, select

# 添加Backend目录到Python路径，使app模块可被导入
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from app.database.connection import engine
from app.models import Admin, Reviewer, Student, Teacher, Course, Leave, StudentCourse, School, Role
from app.utils.password import hash_password
from sqlmodel import SQLModel

# 确保所有模型都被导入和注册
import app.models


def create_tables():
    """创建所有数据库表"""
    print("正在创建数据库表...")
    # 先删除所有表，然后重新创建
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    print("数据库表创建完成")


def create_admin(session: Session):
    """创建管理员用户"""
    admin = Admin(admin_id=8001, name="管理员", password=hash_password("1"))
    session.add(admin)
    session.commit()
    print(f"创建管理员: {admin.name} (ID: {admin.admin_id}, 密码: 1)")
    return admin


def create_test_reviewers(session: Session):
    """创建测试审核员数据 - 按角色分类，模拟真实层级"""
    surnames = [
        "李", "王", "张", "刘", "陈", "杨", "赵", "黄",
        "周", "吴", "徐", "孙", "胡", "朱", "高", "林",
    ]
    names = [
        "伟", "芳", "娜", "秀英", "敏", "静", "丽", "强",
        "磊", "军", "洋", "勇", "艳", "杰", "涛", "明",
    ]

    # 创建学校和角色数据
    # 角色按审批层级定义：辅导员(一级)、书记(二级)、学工处(三级)
    schools = [
        "学生处",
        "智能制造学院",
        "信息工程学院",
        "城市建设学院",
        "经济与管理学院",
        "会计学院",
        "艺术设计学院",
        "人文与教育学院",
        "体育学院",
    ]
    roles_list = ["辅导员", "书记", "学工处", "副院长"]

    school_map = {}
    for idx, school_name in enumerate(schools, start=1):
        school = School(school_id=idx, school_name=school_name)
        session.add(school)
        school_map[school_name] = idx
        print(f"创建学校/院系: {school_name} (ID: {idx})")

    role_map = {}
    for idx, role_name in enumerate(roles_list, start=1):
        role = Role(role_id=idx, role_name=role_name)
        session.add(role)
        role_map[role_name] = idx
        print(f"创建角色: {role_name} (ID: {idx})")

    session.commit()

    # 各学院的辅导员和书记（ID 1001-1014）
    college_schools = [s for s in schools if s not in ("学生处", "教务处")]
    college_school_ids = [school_map[s] for s in college_schools]

    created_reviewers = []
    reviewer_id = 1001
    used_names = set()

    def gen_name():
        while True:
            n = random.choice(surnames) + random.choice(names)
            if n not in used_names:
                used_names.add(n)
                return n

    # 为每个学院创建2个辅导员 + 1个书记
    for school_id in college_school_ids:
        # 辅导员 (2个)
        for j in range(2):
            reviewer = Reviewer(
                reviewer_id=reviewer_id,
                reviewer_name=gen_name(),
                school_id=school_id,
                role_id=role_map["辅导员"],
                password=hash_password("1"),
            )
            session.add(reviewer)
            created_reviewers.append(reviewer)
            print(f"创建辅导员{j+1}: {reviewer.reviewer_name} (ID: {reviewer_id}, {college_schools[college_school_ids.index(school_id)]})")
            reviewer_id += 1

        # 书记 (1个)
        reviewer = Reviewer(
            reviewer_id=reviewer_id,
            reviewer_name=gen_name(),
            school_id=school_id,
            role_id=role_map["书记"],
            password=hash_password("1"),
        )
        session.add(reviewer)
        created_reviewers.append(reviewer)
        print(f"创建书记: {reviewer.reviewer_name} (ID: {reviewer_id}, {college_schools[college_school_ids.index(school_id)]})")
        reviewer_id += 1

    # 学工处审核员（2个，全校权限）
    for _ in range(2):
        reviewer = Reviewer(
            reviewer_id=reviewer_id,
            reviewer_name=gen_name(),
            school_id=school_map["学生处"],
            role_id=role_map["处长"],
            password=hash_password("1"),
        )
        session.add(reviewer)
        created_reviewers.append(reviewer)
        print(f"创建学工处: {reviewer.reviewer_name} (ID: {reviewer_id}, 学生处/处长)")
        reviewer_id += 1

    session.commit()
    return created_reviewers, school_map


def create_test_teachers(session: Session):
    """创建测试教师数据 - 随机名称"""
    # 随机中文姓名生成
    surnames = ["王", "李", "张", "陈", "刘", "杨", "赵", "黄", "周", "吴"]
    names = ["教授", "老师", "博士", "副教授", "讲师", "导师"]

    created_teachers = []
    for i in range(15):  # 创建10个教师
        teacher_id = 2001 + i
        name = random.choice(surnames) + random.choice(names)

        teacher = Teacher(teacher_id=teacher_id, teacher_name=name, password=hash_password("1"))

        session.add(teacher)
        created_teachers.append(teacher)
        print(f"创建教师: {teacher.teacher_name} (ID: {teacher.teacher_id}, 密码: 1)")

    session.commit()
    return created_teachers


def create_test_courses(session: Session, teachers):
    """创建测试课程数据 - 每个老师教授所有课程"""
    course_names = [
        "数据结构",
        "算法分析",
        "数据库原理",
        "软件工程",
        "计算机网络",
        "操作系统",
        "Web开发",
        "移动应用开发",
        "人工智能",
        "机器学习",
        "编译原理",
        "计算机组成原理",
        "离散数学",
        "线性代数",
        "概率统计",
        "云计算",
        "大数据技术",
        "网络安全",
        "物联网工程",
        "区块链技术",
    ]

    created_courses = []
    course_id_counter = 3001

    # 为每个老师创建所有课程
    for teacher in teachers:
        for course_name in course_names:
            course_data = {
                "course_id": course_id_counter,
                "teacher_id": teacher.teacher_id,
                "course_name": f"{teacher.teacher_name}的{course_name}",
                "class_hours": str(random.randint(32, 80)),
            }

            course = Course(**course_data)
            session.add(course)
            created_courses.append(course)
            print(
                f"创建课程: {course.course_name} (ID: {course.course_id}, 教师: {teacher.teacher_name})"
            )

            course_id_counter += 1

    session.commit()
    return created_courses


def create_test_students(session: Session, reviewers, school_map):
    """创建测试学生数据 - 学生分配到同学院的辅导员"""
    schools = [
        "智能制造学院",
        "信息工程学院",
        "城市建设学院",
        "经济与管理学院",
        "会计学院",
        "艺术设计学院",
        "人文与教育学院",
        "体育学院",
    ]

    # 按学校分组辅导员（只分配辅导员角色的审核员）
    counselor_role = session.exec(
        select(Role).where(Role.role_name == "辅导员")
    ).first()
    counselor_reviewers = {}
    for r in reviewers:
        if r.role_id == (counselor_role.role_id if counselor_role else None):
            sid = r.school_id or 0
            if sid not in counselor_reviewers:
                counselor_reviewers[sid] = []
            counselor_reviewers[sid].append(r)

    created_students = []
    for i in range(1, 151):  # 创建150个学生
        school_name = random.choice(schools)
        school_id = school_map.get(school_name, 1)

        # 分配同学院的辅导员
        available_counselors = counselor_reviewers.get(school_id, list(reviewers))
        assigned_reviewer = random.choice(available_counselors) if available_counselors else random.choice(reviewers)

        student_data = {
            "student_id": 4000 + i,
            "student_name": f"学生{i:03d}",
            "password": "1",
            "school_id": school_id,
            "reviewer_id": assigned_reviewer.reviewer_id,
            "guarantee_permission": datetime.now()
            + timedelta(days=random.randint(1, 365)),
        }

        password_plain = student_data.pop("password", None)
        student = Student(**student_data)
        if password_plain:
            student.password = hash_password(password_plain)

        session.add(student)
        created_students.append(student)
        print(
            f"创建学生: {student.student_name} (学号: {student.student_id}, 密码: 1, 审核员: {student.reviewer_id})"
        )

    session.commit()
    return created_students


def create_student_course_enrollments(session: Session, students, courses):
    """创建学生选课记录 - 每个学生随机选择5-12门课程"""
    created_enrollments = []

    for student in students:
        # 每个学生随机选择5-12门课程
        num_courses = random.randint(5, 12)
        selected_courses = random.sample(courses, num_courses)

        for course in selected_courses:
            enrollment = StudentCourse(
                student_id=student.student_id,
                course_id=course.course_id,
                enrollment_date=datetime.now().strftime("%Y-%m-%d"),
                status="已选课",
            )
            session.add(enrollment)
            created_enrollments.append(enrollment)

        print(f"学生 {student.student_name} 选择了 {num_courses} 门课程")

    session.commit()
    print(f"创建了 {len(created_enrollments)} 条选课记录")
    return created_enrollments


def create_test_leaves(session: Session, students, courses):
    """创建测试请假记录数据 - 比例符合实际"""
    leave_types = ["事假", "病假", "公假", "婚假", "丧假"]
    # 实际比例：已批准60%、已拒绝25%、待审批10%、已销假5%
    status_weights = ["已批准"] * 60 + ["已拒绝"] * 25 + ["待审批"] * 10 + ["已销假"] * 5

    created_leaves = []
    leave_id_counter = 5001

    for i, student in enumerate(students[:120]):  # 为前120个学生创建请假记录
        num_leaves = random.randint(1, 8)  # 每个学生1-8条请假记录

        # 获取该学生的选课记录
        student_courses = session.exec(
            select(StudentCourse).where(StudentCourse.student_id == student.student_id)
        ).all()

        if not student_courses:
            continue

        student_course_ids = [sc.course_id for sc in student_courses]
        student_courses = [c for c in courses if c.course_id in student_course_ids]

        for j in range(num_leaves):
            if not student_courses:
                break

            leave_date = datetime.now() - timedelta(days=random.randint(1, 180))
            leave_days = random.randint(1, 7)
            selected_course = random.choice(student_courses)

            # 根据状态决定审核意见，保持一致
            status = random.choice(status_weights)
            if status == "已批准":
                audit_remarks = "已批准"
            elif status == "已拒绝":
                audit_remarks = "已拒绝"
            elif status == "已销假":
                audit_remarks = "已批准"  # 销假是从已批准转来的
            else:
                audit_remarks = ""  # 待审批状态没有审核意见

            leave_data = {
                "leave_id": leave_id_counter,
                "student_id": student.student_id,
                "leave_date": leave_date,
                "leave_hours": str(random.choice([2, 4, 6, 8, 12, 16, 24, 32, 48, 60, 72])),
                "status": status,
                "leave_type": random.choice(leave_types),
                "remarks": f"{student.student_name}的请假申请",
                "materials": "请假材料.pdf" if random.random() > 0.6 else "",
                "reviewer_id": student.reviewer_id,  # 使用学生的审核员
                "teacher_id": selected_course.teacher_id,
                "audit_remarks": audit_remarks,
                "audit_time": leave_date + timedelta(hours=random.randint(1, 48)),
                "course_id": selected_course.course_id,
                "is_modified": False,  # 改为布尔类型
                "guarantee_student_id": random.choice(students).student_id
                if random.random() > 0.7
                else None,
            }

            leave = Leave(**leave_data)
            session.add(leave)
            created_leaves.append(leave)
            print(
                f"创建请假记录: {student.student_name} - {leave.leave_type} {leave.leave_hours} (ID: {leave.leave_id})"
            )

            leave_id_counter += 1

    session.commit()
    return created_leaves


def clear_all_data(session: Session):
    """清空所有测试数据"""
    print("正在清空现有数据...")

    # 按依赖关系顺序删除数据
    session.exec(Leave.__table__.delete())
    session.exec(StudentCourse.__table__.delete())
    session.exec(Course.__table__.delete())
    session.exec(Student.__table__.delete())
    session.exec(Teacher.__table__.delete())
    session.exec(Reviewer.__table__.delete())
    session.exec(Role.__table__.delete())
    session.exec(School.__table__.delete())
    session.exec(Admin.__table__.delete())

    session.commit()
    print("数据清空完成")


def main():
    """主函数"""
    print("开始创建测试数据...")

    # 首先创建数据库表
    create_tables()

    # 使用 engine 获取会话
    with Session(engine) as session:
        # 询问是否清空现有数据
        clear_data = input("是否清空现有数据? (y/N): ").lower().strip()
        if clear_data == "y":
            clear_all_data(session)

        print("\n1. 创建管理员...")
        admin = create_admin(session)

        print("\n2. 创建学校、角色和审核员...")
        reviewers, school_map = create_test_reviewers(session)

        print("\n3. 创建教师...")
        teachers = create_test_teachers(session)

        print("\n4. 创建课程...")
        courses = create_test_courses(session, teachers)

        print("\n5. 创建学生...")
        students = create_test_students(session, reviewers, school_map)

        print("\n6. 创建学生选课记录...")
        enrollments = create_student_course_enrollments(session, students, courses)

        print("\n7. 创建请假记录...")
        leaves = create_test_leaves(session, students, courses)

        print(f"\n测试数据创建完成!")
        print(f"- 管理员: 1 个 (ID: 8001, 密码: 1)")
        print(f"- 学校/院系: {len(school_map)} 个")
        print(f"- 角色: 6 个 (辅导员、书记、处长、主任、副院长、科长)")
        print(f"- 审核员: {len(reviewers)} 个 (每学院1辅导员+1书记 + 2学工处, 密码: 1)")
        print(f"- 教师: {len(teachers)} 个 (ID: 2001-2015, 密码: 1)")
        print(f"- 课程: {len(courses)} 门")
        print(f"- 学生: {len(students)} 个 (ID: 4001-4150, 密码: 1)")
        print(f"- 选课记录: {len(enrollments)} 条")
        print(f"- 请假记录: {len(leaves)} 条")

        print(f"\n数据统计:")
        print(f"- 每个教师教授 {len(courses) // len(teachers)} 门课程")
        print(f"- 每个学生平均选择 {len(enrollments) / len(students):.1f} 门课程")
        print(f"- 学生审核员已随机分配")
        print(f"- 所有密码均为 '1'")


if __name__ == "__main__":
    main()
