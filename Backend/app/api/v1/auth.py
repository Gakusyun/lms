from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.database.connection import get_session
from app.schemas import UserLogin, AdminCreate, ChangePassword, UserRegister, PasswordResetRequest, PasswordResetConfirm
from app.models import Admin, Login
from app.services.auth import AuthService
from app.api.deps import check_login, logout

router = APIRouter()


@router.post("/login", summary="登录")
def login(user: UserLogin, session: Session = Depends(get_session)):
    return AuthService.login(user, session)


@router.get("/login/check")
def login_check(token: str, session: Session = Depends(get_session)):
    """检查登录状态"""
    return check_login(token, session)


@router.get("/logout")
def log_out(token: str, session: Session = Depends(get_session)):
    return logout(token, session)


@router.get("/login/orcode")
def login_qrcode(
    token: str,
    login_token: str,
    session_check: Session = Depends(get_session),
    session_login: Session = Depends(get_session),
):
    obj = check_login(token, session_check)
    if "detail" not in obj:
        login_record = Login(
            user_role=obj["role"],
            user_id=obj["id"],
            user_name=obj["name"],
            token=login_token,
        )
        session_login.add(login_record)
        session_login.commit()
        return {
            "role": obj["role"],
            "id": obj["id"],
            "name": obj["name"],
            "token": login_token,
        }


@router.post("/create/admin")
def create_admin(
    admin_data: AdminCreate,
    session: Session = Depends(get_session),
):
    # 当管理员数为0时可用
    if AuthService.get_admins_count(session) == 0:
        from app.utils.jwt import get_password_hash

        admin_data.password = get_password_hash(admin_data.password)
        admin = Admin(**admin_data.model_dump())
        session.add(admin)
        session.commit()
        session.refresh(admin)
        return admin
    else:
        raise HTTPException(status_code=400, detail="Admin already exists")


@router.post("/change-password", summary="修改密码")
def change_password(
    token: str,
    password_data: ChangePassword,
    session: Session = Depends(get_session),
):
    """修改密码接口 - 修改自己的密码"""
    return AuthService.change_password(token, password_data, session, None)


@router.post("/change-password/{user_id}", summary="修改指定用户密码")
def change_user_password(
    user_id: int,
    token: str,
    password_data: ChangePassword,
    session: Session = Depends(get_session),
):
    """修改指定用户密码接口 - 仅管理员可用"""
    return AuthService.change_password(token, password_data, session, user_id)


@router.post("/register", summary="用户注册")
def register(
    user: UserRegister,
    session: Session = Depends(get_session),
):
    """用户注册接口"""
    return AuthService.register(user, session)


@router.post("/password-reset/request", summary="请求密码重置")
def request_password_reset(
    reset_request: PasswordResetRequest,
    session: Session = Depends(get_session),
):
    """请求密码重置接口"""
    return AuthService.request_password_reset(reset_request.id, reset_request.role, session)


@router.post("/password-reset/confirm", summary="确认密码重置")
def confirm_password_reset(
    reset_confirm: PasswordResetConfirm,
    session: Session = Depends(get_session),
):
    """确认密码重置接口"""
    return AuthService.confirm_password_reset(reset_confirm.reset_token, reset_confirm.new_password, session)


@router.post("/admin/test-db-connection", summary="测试数据库连接")
def test_db_connection(
    db_config: dict,
    session: Session = Depends(get_session),
):
    """测试数据库连接接口"""
    import sqlalchemy
    from sqlalchemy import create_engine
    from sqlalchemy.exc import SQLAlchemyError
    
    try:
        db_type = db_config.get("db_type", "mysql")
        
        if db_type == "mysql":
            host = db_config.get("host", "localhost")
            port = db_config.get("port", 3306)
            database = db_config.get("database", "leave_management")
            username = db_config.get("username", "root")
            password = db_config.get("password", "")
            
            # 创建MySQL连接字符串
            connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
        else:
            # SQLite
            db_path = db_config.get("db_path", "./leave_management.db")
            connection_string = f"sqlite:///{db_path}"
        
        # 测试连接
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            # 执行一个简单的查询来测试连接
            if db_type == "mysql":
                conn.execute(sqlalchemy.text("SELECT 1"))
            else:
                # SQLite不需要执行查询，连接成功即可
                pass
        
        return {"message": "数据库连接成功"}
        
    except SQLAlchemyError as e:
        return {"message": f"数据库连接失败: {str(e)}"}
    except Exception as e:
        return {"message": f"连接测试失败: {str(e)}"}


@router.post("/admin/configure-db", summary="配置数据库")
def configure_database(
    db_config: dict,
    session: Session = Depends(get_session),
):
    """配置数据库接口"""
    from app.config.settings import settings
    from app.database.connection import recreate_engine
    
    # 更新数据库配置
    settings.db_type = db_config.get("db_type", "mysql")
    settings.db_host = db_config.get("host", "localhost")
    settings.db_port = db_config.get("port", 3306)
    settings.db_name = db_config.get("database", "leave_management")
    settings.db_user = db_config.get("username", "root")
    settings.db_password = db_config.get("password", "")
    settings.db_path = db_config.get("db_path", "./leave_management.db")
    
    # 保存配置到文件
    settings.save()
    
    # 重新创建数据库引擎
    recreate_engine()
    
    return {"message": "数据库配置成功"}
