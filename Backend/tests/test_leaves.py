import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.database.connection import get_session
from app.models import Admin, Student, Reviewer, Teacher, Course, Leave, School, Role, StudentCourse, Login
from app.utils.password import hash_password
from datetime import datetime

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
    from sqlmodel import SQLModel
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
    
    # 创建测试学生-课程关联
    test_student_course = StudentCourse(
        student_id=2001,
        course_id=101
    )
    
    # 创建测试请假记录
    test_leave = Leave(
        leave_id=1,
        student_id=2001,
        leave_date=datetime(2026, 3, 20),
        leave_hours="4",
        status="待审批",
        leave_type="事假",
        remarks="家中有事",
        course_id=101,
        reviewer_id=4001
    )
    
    with Session(engine) as session:
        session.add(test_school)
        session.add(test_role)
        session.add(test_admin)
        session.add(test_teacher)
        session.add(test_reviewer)
        session.add(test_student)
        session.add(test_course)
        session.add(test_student_course)
        session.add(test_leave)
        session.commit()
    
    yield
    
    # 清理数据库
    SQLModel.metadata.drop_all(engine)


def test_create_leave(setup_database):
    """测试创建请假记录"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 2001, "password": "student123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    # 使用获取的token创建请假记录
    leave_data = {
        "leave_date": "2026-03-21",
        "leave_hours": "6",
        "status": "待审批",
        "leave_type": "病假",
        "remarks": "身体不适",
        "course_id": 101
    }
    response = client.post(
        "/api/v1/leaves",
        json=leave_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["leave_type"] == "病假"
    assert data["remarks"] == "身体不适"
    assert data["course_id"] == 101


def test_get_leaves(setup_database):
    """测试获取请假列表"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    # 使用获取的token访问请假列表
    response = client.get(
        "/api/v1/leaves",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0


def test_get_leaves_count(setup_database):
    """测试获取请假记录数量"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    # 使用获取的token获取请假记录数量
    response = client.get(
        "/api/v1/leaves/count",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "leaves_count" in data
    assert isinstance(data["leaves_count"], int)


def test_approve_leave(setup_database):
    """测试批准请假"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 4001, "password": "reviewer123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    # 使用获取的token批准请假
    response = client.post(
        "/api/v1/leaves/approve/1",
        params={"audit_remarks": "同意请假"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "已批准"
    assert data["audit_remarks"] == "同意请假"


def test_reject_leave(setup_database):
    """测试拒绝请假"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 4001, "password": "reviewer123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    # 使用获取的token拒绝请假
    response = client.post(
        "/api/v1/leaves/reject/1",
        params={"audit_remarks": "不同意请假"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "已拒绝"
    assert data["audit_remarks"] == "不同意请假"


def test_edit_leave(setup_database):
    """测试编辑请假记录"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 2001, "password": "student123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    # 先创建一个请假记录
    leave_data = {
        "leave_date": "2026-03-21",
        "leave_hours": "6",
        "status": "待审批",
        "leave_type": "病假",
        "remarks": "身体不适",
        "course_id": 101
    }
    create_response = client.post(
        "/api/v1/leaves",
        json=leave_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 200
    leave_id = create_response.json()["leave_id"]
    
    # 使用获取的token编辑请假记录
    update_data = {
        "leave_hours": "8",
        "remarks": "家中有急事",
        "status": "待审批"
    }
    response = client.put(
        f"/api/v1/leaves/edit/{leave_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["leave_hours"] == "8"
    assert data["remarks"] == "家中有急事"
