from sqlmodel import Session, select, func
from fastapi import HTTPException
from datetime import timedelta

from app.schemas import UserLogin, ChangePassword
from app.models import Admin, Teacher, Student, Reviewer, Login, AuditAction
from app.utils.jwt import verify_password, get_password_hash, create_access_token, verify_token
from app.utils.logger import get_logger
from app.services.audit_log import AuditLogService

logger = get_logger(__name__)


class AuthService:
    @staticmethod
    def get_role_model_map():
        """获取角色与模型的映射关系"""
        return {
            "teacher": (Teacher, "teacher_id"),
            "student": (Student, "student_id"),
            "reviewer": (Reviewer, "reviewer_id"),
            "admin": (Admin, "admin_id"),
        }

    @staticmethod
    def find_user_by_id(user_id: int, session: Session):
        """根据用户ID自动检测并返回用户对象和角色"""
        role_model_map = AuthService.get_role_model_map()

        for role, (model, field) in role_model_map.items():
            try:
                obj = AuthService.get_by_id(session, model, user_id, field)
                return obj, role, model, field
            except HTTPException:
                continue
            except Exception:
                # 忽略数据库表不存在的错误，继续尝试其他角色
                continue

        raise HTTPException(404, "User not found")

    @staticmethod
    def get_user_name_by_role(obj, role: str):
        """根据角色获取正确的用户名字段"""
        name_field_map = {
            "teacher": "teacher_name",
            "student": "student_name",
            "reviewer": "reviewer_name",
            "admin": "name",
        }
        return getattr(obj, name_field_map.get(role, "name"))

    @staticmethod
    def login(user: UserLogin, session: Session, client_ip: str = None):
        """用户登录"""
        try:
            logger.info(f"Login attempt for user ID: {user.id}")
            
            # 自动检测用户角色
            obj, user_role, model_cls, id_field = AuthService.find_user_by_id(user.id, session)

            if not obj.password:
                logger.warning(f"User {user.id} has no password set")
                raise HTTPException(401, "User has no password set")

            if not verify_password(user.password, obj.password):
                logger.warning(f"Invalid credentials for user {user.id}")
                raise HTTPException(401, "Invalid credentials")

            # 获取用户名
            user_name = AuthService.get_user_name_by_role(obj, user_role)

            # 生成JWT token
            access_token_expires = timedelta(minutes=30)
            access_token = create_access_token(
                data={"sub": str(user.id), "role": user_role, "name": user_name},
                expires_delta=access_token_expires
            )

            # 记录登录信息（可选，用于审计）
            login_record = Login(
                user_role=user_role,
                user_id=user.id,
                user_name=user_name,
                token=access_token,
            )
            session.add(login_record)
            session.commit()

            logger.info(f"Login successful for user {user.id} ({user_name}, role: {user_role})")

            # 审计日志：登录
            AuditLogService.log(
                current_user={"id": user.id, "role": user_role, "name": user_name},
                action=AuditAction.LOGIN,
                target_type="user",
                target_id=user.id,
                detail=f"用户登录成功，角色={user_role}",
                ip_address=client_ip,
                session=session,
            )

            return {
                "role": user_role,
                "id": user.id,
                "name": user_name,
                "token": access_token,  # 返回 JWT token，前端需保存
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during login for user {user.id}: {str(e)}")
            raise HTTPException(500, "Internal server error")

    @staticmethod
    def get_by_id(session: Session, model, id_value: int, id_field: str):
        """根据ID获取对象"""
        field = getattr(model, id_field)
        stmt = select(model).where(field == id_value)
        obj = session.exec(stmt).first()
        if not obj:
            raise HTTPException(
                404, f"{model.__name__} with {id_field}={id_value} not found"
            )
        return obj

    @staticmethod
    def get_admins_count(session: Session) -> int:
        """获取管理员数量"""
        return session.exec(select(func.count(Admin.admin_id))).one()

    @staticmethod
    def change_password(current_user: dict, password_data: ChangePassword, session: Session, target_user_id: int = None, client_ip: str = None):
        """修改密码"""
        # 验证当前用户角色
        role_model_map = AuthService.get_role_model_map()
        if current_user["role"] not in role_model_map:
            raise HTTPException(400, "Invalid role")

        # 确定要修改密码的用户
        if target_user_id is not None:
            # 修改指定用户的密码 - 仅管理员可用
            if current_user["role"] != "admin":
                raise HTTPException(403, "Only admins can change other users' passwords")

            # 查找目标用户
            target_user, target_role, _, _ = AuthService.find_user_by_id(target_user_id, session)
        else:
            # 修改自己的密码
            target_user_id = current_user["id"]
            target_user, target_role, _, _ = AuthService.find_user_by_id(target_user_id, session)

        # 验证原密码 - 管理员可以跳过验证
        if current_user["role"] != "admin":
            if not target_user.password:
                raise HTTPException(400, "User has no password set")

            if not verify_password(password_data.old_password, target_user.password):
                raise HTTPException(400, "Original password is incorrect")

        # 更新密码
        target_user.password = get_password_hash(password_data.new_password)
        session.commit()

        # 审计日志：密码修改
        AuditLogService.log(
            current_user=current_user,
            action=AuditAction.PASSWORD_CHANGE,
            target_type="user",
            target_id=target_user_id,
            detail=f"修改密码，目标用户={target_user_id}，角色={target_role}",
            ip_address=client_ip,
            session=session,
        )

        return {
            "message": "Password changed successfully",
            "target_user_id": target_user_id,
            "target_role": target_role
        }

    @staticmethod
    def register(user: UserRegister, session: Session):
        """用户注册"""
        try:
            logger.info(f"Registration attempt for user ID: {user.id}, role: {user.role}")

            role_model_map = AuthService.get_role_model_map()
            if user.role not in role_model_map:
                raise HTTPException(400, "Invalid role")

            model_cls, id_field = role_model_map[user.role]

            # 检查用户是否已存在
            field = getattr(model_cls, id_field)
            stmt = select(model_cls).where(field == user.id)
            existing_user = session.exec(stmt).first()
            if existing_user:
                raise HTTPException(400, f"User with ID {user.id} already exists")

            # 创建新用户
            name_field = {
                "teacher": "teacher_name",
                "student": "student_name",
                "reviewer": "reviewer_name",
                "admin": "name"
            }[user.role]

            user_data = {
                id_field: user.id,
                name_field: user.name,
                "password": get_password_hash(user.password)
            }

            new_user = model_cls(**user_data)
            session.add(new_user)
            session.commit()
            session.refresh(new_user)

            logger.info(f"Registration successful for user {user.id} ({user.name}, role: {user.role})")

            return {
                "message": "Registration successful",
                "role": user.role,
                "id": user.id,
                "name": user.name
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            raise HTTPException(500, "Internal server error")

    @staticmethod
    def request_password_reset(user_id: int, role: str, session: Session):
        """请求密码重置"""
        try:
            logger.info(f"Password reset request for user ID: {user_id}, role: {role}")

            role_model_map = AuthService.get_role_model_map()
            if role not in role_model_map:
                raise HTTPException(400, "Invalid role")

            # 查找用户
            user, _, _, _ = AuthService.find_user_by_id(user_id, session)

            # 生成重置令牌
            reset_token_expires = timedelta(hours=1)
            reset_token = create_access_token(
                data={"sub": str(user_id), "role": role, "reset": True},
                expires_delta=reset_token_expires
            )

            # 这里可以添加发送邮件的逻辑
            # 暂时只返回重置令牌

            logger.info(f"Password reset token generated for user {user_id}")

            return {
                "message": "Password reset token generated",
                "reset_token": reset_token
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during password reset request: {str(e)}")
            raise HTTPException(500, "Internal server error")

    @staticmethod
    def confirm_password_reset(reset_token: str, new_password: str, session: Session):
        """确认密码重置"""
        try:
            logger.info("Password reset confirmation attempt")

            # 验证重置令牌
            payload = verify_token(reset_token)
            if not payload or payload.get("reset") != True:
                raise HTTPException(400, "Invalid or expired reset token")

            user_id = int(payload.get("sub"))
            role = payload.get("role")

            # 查找用户
            user, _, _, _ = AuthService.find_user_by_id(user_id, session)

            # 更新密码
            user.password = get_password_hash(new_password)
            session.commit()

            logger.info(f"Password reset successful for user {user_id}")

            return {
                "message": "Password reset successful",
                "user_id": user_id,
                "role": role
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during password reset confirmation: {str(e)}")
            raise HTTPException(500, "Internal server error")