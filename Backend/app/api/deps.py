from sqlmodel import Session
from fastapi import Depends, HTTPException
from app.database.connection import get_session
from app.utils.jwt import verify_token


def check_login(token: str, session: Session = Depends(get_session)):
    """验证登录状态"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {
        "role": payload.get("role"),
        "id": int(payload.get("sub")),
        "name": payload.get("name"),
    }


def logout(token: str, session: Session = Depends(get_session)):
    """登出"""
    # 验证token是否有效
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # JWT是无状态的，登出只需要前端删除token即可
    # 这里可以添加可选的token黑名单机制
    return {"message": "Successfully logged out"}