from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.database.connection import get_session
from app.schemas import UserLogin, AdminCreate, ChangePassword, UserRegister, PasswordResetRequest, PasswordResetConfirm
from app.models import Admin, Login
from app.services.auth import AuthService
from app.api.deps import check_login, logout

router = APIRouter()


@router.post("/login", summary="登录")
def login(user: UserLogin, request: Request, session: Session = Depends(get_session)):
    client_ip = request.client.host if request.client else None
    return AuthService.login(user, session, client_ip)


@router.get("/login/check")
def login_check(current_user: dict = Depends(check_login)):
    """检查登录状态"""
    return current_user


@router.post("/logout")
def log_out(current_user: dict = Depends(logout)):
    return current_user


@router.get("/login/orcode")
def login_qrcode(
    login_token: str,
    token: str | None = None,
    session_check: Session = Depends(get_session),
    session_login: Session = Depends(get_session),
):
    # 小程序端扫码：有 token 参数，创建登录记录
    if token:
        from app.utils.jwt import verify_token as jwt_verify
        obj = jwt_verify(token)
        if not obj or not obj.get("sub"):
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        user_info = {
            "role": obj.get("role"),
            "id": int(obj.get("sub")),
            "name": obj.get("name"),
        }
        login_record = Login(
            user_role=user_info["role"],
            user_id=user_info["id"],
            user_name=user_info["name"],
            token=login_token,
            jwt_token=token,
        )
        session_login.add(login_record)
        session_login.commit()
        return {
            "role": user_info["role"],
            "id": user_info["id"],
            "name": user_info["name"],
            "token": token,
        }
    # 前端轮询：只有 login_token，查询数据库
    else:
        login_record = session_login.exec(
            select(Login).where(Login.token == login_token, Login.can_be_used == True)
        ).first()

        if login_record:
            login_record.can_be_used = False
            session_login.commit()
            return {
                "role": login_record.user_role,
                "id": login_record.user_id,
                "name": login_record.user_name,
                "token": login_record.jwt_token,
            }
        else:
            raise HTTPException(status_code=422, detail="未扫码或二维码已过期")


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
    request: Request,
    current_user: dict = Depends(check_login),
    password_data: ChangePassword = None,
    session: Session = Depends(get_session),
):
    """修改密码接口 - 修改自己的密码"""
    client_ip = request.client.host if request.client else None
    # 从current_user中获取token相关信息，传递user信息给service
    return AuthService.change_password(current_user, password_data, session, None, client_ip)


@router.post("/change-password/{user_id}", summary="修改指定用户密码")
def change_user_password(
    request: Request,
    user_id: int,
    current_user: dict = Depends(check_login),
    password_data: ChangePassword = None,
    session: Session = Depends(get_session),
):
    """修改指定用户密码接口 - 仅管理员可用"""
    client_ip = request.client.host if request.client else None
    return AuthService.change_password(current_user, password_data, session, user_id, client_ip)


@router.post("/register", summary="用户注册")
def register(
    user: UserRegister,
    session: Session = Depends(get_session),
):
    """用户注册接口 - 不允许注册admin角色"""
    if user.role == "admin":
        raise HTTPException(status_code=403, detail="Cannot register as admin")
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
    db_config: dict = None,
):
    """测试数据库连接接口 - 首次启动时无需认证"""

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

            connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
        else:
            db_path = db_config.get("db_path", "./leave_management.db")
            connection_string = f"sqlite:///{db_path}"

        engine = create_engine(connection_string)
        with engine.connect() as conn:
            if db_type == "mysql":
                conn.execute(sqlalchemy.text("SELECT 1"))

        return {"message": "数据库连接成功"}

    except SQLAlchemyError as e:
        return {"message": f"数据库连接失败: {str(e)}"}
    except Exception as e:
        return {"message": f"连接测试失败: {str(e)}"}


@router.post("/admin/configure-db", summary="配置数据库")
def configure_database(
    db_config: dict = None,
):
    """配置数据库接口 - 首次启动时无需认证"""

    from app.config.settings import settings
    from app.database.connection import recreate_engine

    settings.db_type = db_config.get("db_type", "mysql")
    settings.db_host = db_config.get("host", "localhost")
    settings.db_port = db_config.get("port", 3306)
    settings.db_name = db_config.get("database", "leave_management")
    settings.db_user = db_config.get("username", "root")
    settings.db_password = db_config.get("password", "")
    settings.db_path = db_config.get("db_path", "./leave_management.db")

    settings.save()

    new_engine = recreate_engine()

    # 在新数据库上创建所有表
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(new_engine, checkfirst=True)

    return {"message": "数据库配置成功"}
