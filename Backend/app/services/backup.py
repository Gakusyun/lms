import os
import time
import shutil
from datetime import datetime
from sqlmodel import Session
from app.database.connection import engine


class BackupService:
    """数据库备份服务"""
    
    @staticmethod
    def create_backup(backup_dir: str = "./backups"):
        """创建数据库备份"""
        # 确保备份目录存在
        os.makedirs(backup_dir, exist_ok=True)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"backup_{timestamp}.db")
        
        try:
            # 获取数据库文件路径
            db_url = str(engine.url)
            if db_url.startswith("sqlite"):
                # 对于SQLite，直接复制数据库文件
                db_path = db_url.replace("sqlite:///", "")
                if os.path.exists(db_path):
                    shutil.copy2(db_path, backup_file)
                    return {"status": "success", "backup_file": backup_file}
                else:
                    return {"status": "error", "message": "Database file not found"}
            else:
                # 对于其他数据库，使用SQLAlchemy的备份方法
                # 这里仅作为示例，实际实现需要根据具体数据库类型调整
                return {"status": "error", "message": "Backup not supported for this database type"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def list_backups(backup_dir: str = "./backups"):
        """列出所有备份文件"""
        if not os.path.exists(backup_dir):
            return []
        
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.startswith("backup_") and filename.endswith(".db"):
                filepath = os.path.join(backup_dir, filename)
                stat = os.stat(filepath)
                backups.append({
                    "filename": filename,
                    "path": filepath,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
        
        # 按创建时间降序排序
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups
    
    @staticmethod
    def restore_backup(backup_file: str, backup_dir: str = "./backups"):
        """从备份文件恢复数据库"""
        backup_path = os.path.join(backup_dir, backup_file)
        
        if not os.path.exists(backup_path):
            return {"status": "error", "message": "Backup file not found"}
        
        try:
            # 获取数据库文件路径
            db_url = str(engine.url)
            if db_url.startswith("sqlite"):
                # 对于SQLite，直接复制备份文件到数据库位置
                db_path = db_url.replace("sqlite:///", "")
                # 先备份当前数据库，以防恢复失败
                temp_backup = f"{db_path}.bak"
                if os.path.exists(db_path):
                    shutil.copy2(db_path, temp_backup)
                
                # 恢复备份
                shutil.copy2(backup_path, db_path)
                
                # 恢复成功后删除临时备份
                if os.path.exists(temp_backup):
                    os.remove(temp_backup)
                
                return {"status": "success", "message": "Database restored successfully"}
            else:
                # 对于其他数据库，使用SQLAlchemy的恢复方法
                # 这里仅作为示例，实际实现需要根据具体数据库类型调整
                return {"status": "error", "message": "Restore not supported for this database type"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def cleanup_old_backups(backup_dir: str = "./backups", keep_days: int = 7):
        """清理旧备份文件"""
        if not os.path.exists(backup_dir):
            return {"status": "success", "message": "Backup directory not found"}
        
        cutoff_time = time.time() - (keep_days * 24 * 3600)
        deleted = []
        
        for filename in os.listdir(backup_dir):
            if filename.startswith("backup_") and filename.endswith(".db"):
                filepath = os.path.join(backup_dir, filename)
                if os.stat(filepath).st_ctime < cutoff_time:
                    os.remove(filepath)
                    deleted.append(filename)
        
        return {"status": "success", "deleted": deleted}
