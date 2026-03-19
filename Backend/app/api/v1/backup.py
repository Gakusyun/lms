from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from app.database.connection import get_session
from app.services.backup import BackupService

router = APIRouter()


@router.post("/backup/create", summary="创建数据库备份")
def create_backup(
    backup_dir: str = Query("./backups", description="备份文件存储目录"),
    session: Session = Depends(get_session)
):
    """创建数据库备份"""
    result = BackupService.create_backup(backup_dir)
    return result


@router.get("/backup/list", summary="列出所有备份文件")
def list_backups(
    backup_dir: str = Query("./backups", description="备份文件存储目录"),
    session: Session = Depends(get_session)
):
    """列出所有备份文件"""
    backups = BackupService.list_backups(backup_dir)
    return {"backups": backups}


@router.post("/backup/restore", summary="从备份文件恢复数据库")
def restore_backup(
    backup_file: str = Query(..., description="备份文件名"),
    backup_dir: str = Query("./backups", description="备份文件存储目录"),
    session: Session = Depends(get_session)
):
    """从备份文件恢复数据库"""
    result = BackupService.restore_backup(backup_file, backup_dir)
    return result


@router.post("/backup/cleanup", summary="清理旧备份文件")
def cleanup_backups(
    keep_days: int = Query(7, description="保留的备份天数"),
    backup_dir: str = Query("./backups", description="备份文件存储目录"),
    session: Session = Depends(get_session)
):
    """清理旧备份文件"""
    result = BackupService.cleanup_old_backups(backup_dir, keep_days)
    return result
