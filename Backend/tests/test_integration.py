import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from app.main import app
from app.database.connection import get_session
from app.models import Admin, Reviewer, Student, Teacher, Course, Leave, StudentCourse, School, Role, Login
from app.utils.password import hash_password

# 创建内存数据库用于测试
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# 覆盖依赖项
def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

# 创建测试客户端
client = TestClient(app)


@pytest.fixture
def setup_database():
    """设置测试数据库"""
    # 确保所有模型都被导入，以便SQLModel能够创建所有表
    from app.models import Admin, Reviewer, Student, Teacher, Course, Leave, StudentCourse, School, Role, Login
    SQLModel.metadata.create_all(engine)
    
    # 创建测试学校和角色
    test_school = School(
        school_id=1,
        school_name="测试学校"
    )
    
    test_role = Role(
        role_id=1,
        role_name="审核员"
    )
    
    # 创建测试管理员
    test_admin = Admin(
        admin_id=1001,
        name="Admin",
        password=hash_password("admin123"),
    )
    
    # 创建测试教师
    test_teacher = Teacher(
        teacher_id=3001,
        teacher_name="Teacher",
        password=hash_password("teacher123"),
    )
    
    # 创建测试审核员
    test_reviewer = Reviewer(
        reviewer_id=4001,
        reviewer_name="Reviewer",
        password=hash_password("reviewer123"),
        school_id=1,
        role_id=1
    )
    
    # 创建测试学生
    test_student = Student(
        student_id=2001,
        student_name="Student",
        password=hash_password("student123"),
        reviewer_id=4001,
        school_id=1,
    )
    
    # 创建测试课程
    test_course = Course(
        course_id=101,
        teacher_id=3001,
        course_name="数学",
        class_hours="48"
    )
    
    with Session(engine) as session:
        session.add(test_school)
        session.add(test_role)
        session.add(test_admin)
        session.add(test_teacher)
        session.add(test_reviewer)
        session.add(test_student)
        session.add(test_course)
        session.commit()
    
    yield
    
    # 清理数据库
    SQLModel.metadata.drop_all(engine)


def test_user_authentication_flow(setup_database):
    """测试用户认证流程"""
    # 测试管理员登录
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    admin_token = login_response.json()["token"]
    assert login_response.json()["role"] == "admin"
    
    # 测试学生登录
    login_response = client.post(
        "/api/v1/login",
        json={"id": 2001, "password": "student123"}
    )
    assert login_response.status_code == 200
    student_token = login_response.json()["token"]
    assert login_response.json()["role"] == "student"
    
    # 测试教师登录
    login_response = client.post(
        "/api/v1/login",
        json={"id": 3001, "password": "teacher123"}
    )
    assert login_response.status_code == 200
    teacher_token = login_response.json()["token"]
    assert login_response.json()["role"] == "teacher"
    
    # 测试审核员登录
    login_response = client.post(
        "/api/v1/login",
        json={"id": 4001, "password": "reviewer123"}
    )
    assert login_response.status_code == 200
    reviewer_token = login_response.json()["token"]
    assert login_response.json()["role"] == "reviewer"


def test_leave_application_flow(setup_database):
    """测试请假申请和审批流程"""
    # 登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 2001, "password": "student123"}
    )
    assert login_response.status_code == 200
    student_token = login_response.json()["token"]
    
    # 先为学生关联课程
    association_data = {
        "student_id": 2001,
        "course_id": 101
    }
    create_association_response = client.post(
        "/api/v1/student-courses",
        json=association_data,
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert create_association_response.status_code == 200
    
    # 提交请假申请
    leave_data = {
        "student_id": 2001,
        "leave_date": "2026-03-20",
        "leave_hours": "4",
        "status": "待审批",
        "leave_type": "事假",
        "remarks": "家中有事",
        "course_id": 101
    }
    create_leave_response = client.post(
        "/api/v1/leaves",
        json=leave_data,
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert create_leave_response.status_code == 200
    leave_id = create_leave_response.json()["leave_id"]
    
    # 登录审核员账号
    login_response = client.post(
        "/api/v1/login",
        json={"id": 4001, "password": "reviewer123"}
    )
    assert login_response.status_code == 200
    reviewer_token = login_response.json()["token"]
    
    # 审批请假申请
    approve_response = client.post(
        "/api/v1/leaves/approve/" + str(leave_id),
        params={"audit_remarks": "同意请假"},
        headers={"Authorization": f"Bearer {reviewer_token}"}
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "已批准"


def test_course_management_flow(setup_database):
    """测试课程管理流程"""
    # 登录管理员账号
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    admin_token = login_response.json()["token"]
    
    # 创建新课程
    course_data = {
        "course_id": 102,
        "teacher_id": 3001,
        "course_name": "英语",
        "class_hours": "48"
    }
    create_course_response = client.post(
        "/api/v1/courses",
        json=course_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_course_response.status_code == 200
    assert create_course_response.json()["course_name"] == "英语"
    
    # 更新课程信息
    update_data = {
        "course_id": 102,
        "teacher_id": 3001,
        "course_name": "英语口语",
        "class_hours": "60"
    }
    update_course_response = client.put(
        "/api/v1/courses/102",
        json=update_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert update_course_response.status_code == 200
    assert update_course_response.json()["course_name"] == "英语口语"
    assert update_course_response.json()["class_hours"] == "60"


def test_student_course_association_flow(setup_database):
    """测试学生-课程关联流程"""
    # 登录管理员账号
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    admin_token = login_response.json()["token"]
    
    # 关联学生和课程
    association_data = {
        "student_id": 2001,
        "course_id": 101
    }
    create_association_response = client.post(
        "/api/v1/student-courses",
        json=association_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_association_response.status_code == 200
    assert create_association_response.json()["student_id"] == 2001
    assert create_association_response.json()["course_id"] == 101
    
    # 查询学生的课程
    get_courses_response = client.get(
        "/api/v1/student-courses/student/2001",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_courses_response.status_code == 200
    assert len(get_courses_response.json()) > 0


def test_reviewer_management_flow(setup_database):
    """测试审核人管理流程"""
    # 登录管理员账号
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    admin_token = login_response.json()["token"]
    
    # 创建新审核员
    reviewer_data = {
        "reviewer_id": 4002,
        "reviewer_name": "新审核员",
        "school_id": 1,
        "role_id": 1,
        "password": "password123"
    }
    create_reviewer_response = client.post(
        "/api/v1/reviewers",
        json=reviewer_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_reviewer_response.status_code == 200
    assert create_reviewer_response.json()["reviewer_name"] == "新审核员"
    
    # 更新审核员信息
    update_data = {
        "reviewer_id": 4002,
        "reviewer_name": "更新后的审核员",
        "school_id": 1,
        "role_id": 1,
        "password": "newpassword123"
    }
    update_reviewer_response = client.put(
        "/api/v1/reviewers/4002",
        json=update_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert update_reviewer_response.status_code == 200
    assert update_reviewer_response.json()["reviewer_name"] == "更新后的审核员"


def test_statistics_flow(setup_database):
    """测试数据统计功能"""
    # 登录管理员账号
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    admin_token = login_response.json()["token"]
    
    # 获取用户统计
    user_stats_response = client.get(
        "/api/v1/statistics/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert user_stats_response.status_code == 200
    assert "user_statistics" in user_stats_response.json()
    
    # 获取课程选课统计
    course_stats_response = client.get(
        "/api/v1/statistics/courses/enrollment",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert course_stats_response.status_code == 200
    assert "enrollment_statistics" in course_stats_response.json()
