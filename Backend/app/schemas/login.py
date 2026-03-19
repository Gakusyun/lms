from pydantic import BaseModel, EmailStr


class UserLogin(BaseModel):
    id: int
    password: str


class ChangePassword(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str


class UserRegister(BaseModel):
    """用户注册请求"""
    role: str
    id: int
    name: str
    password: str


class PasswordResetRequest(BaseModel):
    """密码重置请求"""
    id: int
    role: str


class PasswordResetConfirm(BaseModel):
    """密码重置确认"""
    reset_token: str
    new_password: str
