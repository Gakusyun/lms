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
from app.models import Admin, Reviewer
from app.utils.password import hash_password

# 创建内存数据库用于测试
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# 创建测试客户端
client = TestClient(app)

# 覆盖依赖项
def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session


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
        password=hash_password("admin123"),
    )
    
    # 创建测试学校和角色
    test_school = School(
        school_id=1,
        school_name="测试学校"
    )
    
    test_role = Role(
        role_id=1,
        role_name="审核员"
    )
    
    with Session(engine) as session:
        session.add(test_admin)
        session.add(test_school)
        session.add(test_role)
        session.commit()
    
    yield
    
    # 清理数据库
    SQLModel.metadata.drop_all(engine)


def test_get_reviewers(setup_database):
    """测试获取审核员列表"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    response = client.get(
        "/api/v1/reviewers",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data


def test_get_reviewers_count(setup_database):
    """测试获取审核员数量"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    response = client.get(
        "/api/v1/reviewers/count",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "reviewers_count" in data
    assert isinstance(data["reviewers_count"], int)


def test_get_reviewer_by_id_not_found(setup_database):
    """测试获取不存在的审核员"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    response = client.get(
        "/api/v1/reviewers/999",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404
    assert "detail" in response.json()


def test_create_reviewer(setup_database):
    """测试创建审核员"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    reviewer_data = {
        "reviewer_id": 1,
        "reviewer_name": "审核员1",
        "school_id": 1,
        "role_id": 1,
        "password": "password123"
    }
    response = client.post("/api/v1/reviewers", json=reviewer_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["reviewer_id"] == reviewer_data["reviewer_id"]
    assert data["reviewer_name"] == reviewer_data["reviewer_name"]
    assert data["school_id"] == reviewer_data["school_id"]
    assert data["role_id"] == reviewer_data["role_id"]
    # 密码应该被哈希，所以不应该与原始密码相同
    assert data["password"] != reviewer_data["password"]


def test_create_duplicate_reviewer(setup_database):
    """测试创建重复的审核员"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    # 首先创建一个审核员
    reviewer_data = {
        "reviewer_id": 2,
        "reviewer_name": "审核员2",
        "school_id": 1,
        "role_id": 1,
        "password": "password123"
    }
    response = client.post("/api/v1/reviewers", json=reviewer_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    # 再次尝试创建相同ID的审核员
    response = client.post("/api/v1/reviewers", json=reviewer_data, headers={"Authorization": f"Bearer {token}"})
    # 应该返回400错误，因为ID重复
    assert response.status_code == 400


def test_update_reviewer(setup_database):
    """测试编辑审核员"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    # 首先创建一个审核员
    reviewer_data = {
        "reviewer_id": 3,
        "reviewer_name": "审核员3",
        "school_id": 1,
        "role_id": 1,
        "password": "password123"
    }
    response = client.post("/api/v1/reviewers", json=reviewer_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    # 编辑审核员
    update_data = {
        "reviewer_id": 3,
        "reviewer_name": "审核员3更新",
        "school_id": 2,
        "role_id": 2,
        "password": "newpassword123"
    }
    response = client.put("/api/v1/reviewers/3", json=update_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["reviewer_name"] == update_data["reviewer_name"]
    assert data["school_id"] == update_data["school_id"]
    assert data["role_id"] == update_data["role_id"]


def test_update_non_existent_reviewer(setup_database):
    """测试编辑不存在的审核员"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    update_data = {
        "reviewer_id": 999,
        "reviewer_name": "不存在的审核员",
        "school_id": 1,
        "role_id": 1,
        "password": "password123"
    }
    response = client.put("/api/v1/reviewers/999", json=update_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_delete_reviewer(setup_database):
    """测试删除审核员"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    # 首先创建一个审核员
    reviewer_data = {
        "reviewer_id": 4,
        "reviewer_name": "审核员4",
        "school_id": 1,
        "role_id": 1,
        "password": "password123"
    }
    response = client.post("/api/v1/reviewers", json=reviewer_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    # 删除审核员
    response = client.delete("/api/v1/reviewers/4", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Reviewer deleted successfully"

    # 验证审核员已被删除
    response = client.get("/api/v1/reviewers/4", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_delete_non_existent_reviewer(setup_database):
    """测试删除不存在的审核员"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/login",
        json={"id": 1001, "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    response = client.delete("/api/v1/reviewers/999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
