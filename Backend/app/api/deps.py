from typing import List, Optional
from sqlmodel import Session
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database.connection import get_session
from app.utils.jwt import verify_token

security = HTTPBearer()


def check_login(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
):
    """验证登录状态"""
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token: missing subject")

    return {
        "role": payload.get("role"),
        "id": int(sub),
        "name": payload.get("name"),
    }


def check_role(allowed_roles: List[str]):
    """
    集中化 RBAC 中间件 - 基于角色的访问控制
    非法越权请求会被拦截并返回明确错误

    用法示例：
        @router.post("/leaves/approve/{leave_id}")
        def approve_leave(
            leave_id: int,
            current_user: dict = Depends(check_role(["admin", "reviewer"])),
        ):
            ...
    """
    def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        session: Session = Depends(get_session),
    ):
        token = credentials.credentials
        payload = verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid token: missing subject")

        user_info = {
            "role": payload.get("role"),
            "id": int(sub),
            "name": payload.get("name"),
        }

        # 角色白名单校验
        if user_info["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied. Required roles: {', '.join(allowed_roles)}. Your role: {user_info['role']}"
            )

        return user_info

    return role_checker


def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
):
    """登出"""
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"message": "Successfully logged out"}
