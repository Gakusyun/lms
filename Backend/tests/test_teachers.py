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
from app.models import Admin, Teacher
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
    from app.models import Admin, Reviewer, Student, Teacher, Course, Leave, StudentCourse, School, Role, Login
    SQLModel.metadata.create_all(engine)
    
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
    
    with Session(engine) as session:
        session.add(test_admin)
        session.add(test_teacher)
        session.commit()
    
    yield
    
    # 清理数据库
    SQLModel.metadata.drop_all(engine)


def test_get_teachers(setup_database):
    """测试获取教师列表"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    # 使用获取的token访问教师列表
    response = client.get(
        "/api/v1/teachers",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0


def test_get_teacher_by_id(setup_database):
    """测试通过ID获取教师"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    # 使用获取的token访问教师详情
    response = client.get(
        "/api/v1/teachers/3001",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["teacher_id"] == 3001
    assert data["teacher_name"] == "Teacher"


def test_get_nonexistent_teacher(setup_database):
    """测试获取不存在的教师"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    # 使用获取的token访问不存在的教师
    response = client.get(
        "/api/v1/teachers/9999",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_create_teacher(setup_database):
    """测试创建教师"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    # 使用获取的token创建教师
    response = client.post(
        "/api/v1/teachers",
        json={
            "teacher_id": 3002,
            "name": "NewTeach",
            "password": "password123"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["teacher_id"] == 3002
    assert data["teacher_name"] == "NewTeach"


def test_create_teacher_existing(setup_database):
    """测试创建已存在的教师"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    # 使用获取的token创建已存在的教师
    response = client.post(
        "/api/v1/teachers",
        json={
            "teacher_id": 3001,
            "name": "Teacher",
            "password": "password123"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
