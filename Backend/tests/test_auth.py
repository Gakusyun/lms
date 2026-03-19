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
from app.models import Admin, Student, Teacher, Reviewer
from app.utils.jwt import get_password_hash

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
    # 确保所有模型都被导入，以便SQLModel能够创建所有表
    from app.models import Admin, Reviewer, Student, Teacher, Course, Leave, StudentCourse, School, Role
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
        password=get_password_hash("admin123"),
    )
    
    # 创建测试教师
    test_teacher = Teacher(
        teacher_id=3001,
        teacher_name="Teacher",
        password=get_password_hash("teacher123"),
    )
    
    # 创建测试审核员
    test_reviewer = Reviewer(
        reviewer_id=4001,
        reviewer_name="Reviewer",
        password=get_password_hash("reviewer123"),
        school_id=1,
        role_id=1
    )
    
    # 创建测试学生
    test_student = Student(
        student_id=2001,
        student_name="Student",
        password=get_password_hash("student123"),
        reviewer_id=4001,
        school_id=1,
    )
    
    with Session(engine) as session:
        session.add(test_school)
        session.add(test_role)
        session.add(test_admin)
        session.add(test_teacher)
        session.add(test_reviewer)
        session.add(test_student)
        session.commit()
    
    yield
    
    # 清理数据库
    SQLModel.metadata.drop_all(engine)


def test_login_admin(setup_database):
    """测试管理员登录"""
    response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123", "token": "test_token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "admin"
    assert data["id"] == 1001
    assert data["name"] == "Admin"
    assert "token" in data


def test_login_student(setup_database):
    """测试学生登录"""
    response = client.post(
        "/api/v1/login",
        json={"id": 2001, "password": "student123", "token": "test_token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "student"
    assert data["id"] == 2001
    assert data["name"] == "Student"
    assert "token" in data


def test_login_teacher(setup_database):
    """测试教师登录"""
    response = client.post(
        "/api/v1/login",
        json={"id": 3001, "password": "teacher123", "token": "test_token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "teacher"
    assert data["id"] == 3001
    assert data["name"] == "Teacher"
    assert "token" in data


def test_login_reviewer(setup_database):
    """测试审核员登录"""
    response = client.post(
        "/api/v1/login",
        json={"id": 4001, "password": "reviewer123", "token": "test_token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "reviewer"
    assert data["id"] == 4001
    assert data["name"] == "Reviewer"
    assert "token" in data


def test_login_invalid_credentials(setup_database):
    """测试无效的登录凭证"""
    response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "wrong_password", "token": "test_token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_nonexistent_user(setup_database):
    """测试不存在的用户"""
    response = client.post(
        "/api/v1/login",
        json={"id": 999, "password": "password123", "token": "test_token"}
    )
    assert response.status_code == 404


def test_create_admin(setup_database):
    """测试创建管理员"""
    # 首先删除所有管理员
    with Session(engine) as session:
        session.query(Admin).delete()
        session.commit()
    
    response = client.post(
        "/api/v1/create/admin",
        json={"admin_id": 2, "name": "NewAdmin", "password": "newadmin123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["admin_id"] == 2
    assert data["name"] == "NewAdmin"


def test_create_admin_existing(setup_database):
    """测试创建已存在的管理员"""
    response = client.post(
        "/api/v1/create/admin",
        json={"admin_id": 1, "name": "Admin", "password": "admin123"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Admin already exists"