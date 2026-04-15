import toml
from pathlib import Path
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Settings:
    def __init__(self, config_file: str = "config.toml"):
        self.config_file = Path(config_file)
        self._config_data = None
        self._load_config()

    def _load_config(self):
        try:
            self._config_data = toml.load(self.config_file)
        except FileNotFoundError:
            # 如果配置文件不存在，创建默认配置
            self._config_data = {
                "database": {
                    "type": "sqlite",
                    "host": "localhost",
                    "port": 3306,
                    "name": "leave_management",
                    "user": "root",
                    "password": "",
                    "path": "./leave_management.db"
                },
                "cors": {
                    "origins": ["http://localhost:3000", "http://127.0.0.1:3000", "https://lms.gxj62.cn", "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"]
                }
            }
            self.save()
        except toml.TomlDecodeError as e:
            logger.error(f"❌ Invalid TOML: {e}")
            raise RuntimeError("Database config corrupted")

    @property
    def database_url(self) -> str:
        db_type = self._config_data["database"].get("type", "sqlite")
        if db_type == "mysql":
            host = self._config_data["database"].get("host", "localhost")
            port = self._config_data["database"].get("port", 3306)
            name = self._config_data["database"].get("name", "leave_management")
            user = self._config_data["database"].get("user", "root")
            password = self._config_data["database"].get("password", "")
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
        else:
            # SQLite
            db_path = self._config_data["database"].get("path", "./leave_management.db")
            return f"sqlite:///{db_path}"

    @property
    def db_type(self) -> str:
        return self._config_data["database"].get("type", "sqlite")

    @db_type.setter
    def db_type(self, value: str):
        self._config_data["database"]["type"] = value

    @property
    def db_host(self) -> str:
        return self._config_data["database"].get("host", "localhost")

    @db_host.setter
    def db_host(self, value: str):
        self._config_data["database"]["host"] = value

    @property
    def db_port(self) -> int:
        return self._config_data["database"].get("port", 3306)

    @db_port.setter
    def db_port(self, value: int):
        self._config_data["database"]["port"] = value

    @property
    def db_name(self) -> str:
        return self._config_data["database"].get("name", "leave_management")

    @db_name.setter
    def db_name(self, value: str):
        self._config_data["database"]["name"] = value

    @property
    def db_user(self) -> str:
        return self._config_data["database"].get("user", "root")

    @db_user.setter
    def db_user(self, value: str):
        self._config_data["database"]["user"] = value

    @property
    def db_password(self) -> str:
        return self._config_data["database"].get("password", "")

    @db_password.setter
    def db_password(self, value: str):
        self._config_data["database"]["password"] = value

    @property
    def db_path(self) -> str:
        return self._config_data["database"].get("path", "./leave_management.db")

    @db_path.setter
    def db_path(self, value: str):
        self._config_data["database"]["path"] = value

    @property
    def jwt_secret_key(self) -> str:
        """获取JWT密钥"""
        import os
        return os.environ.get("JWT_SECRET_KEY") or self._config_data.get("jwt", {}).get("secret_key", "LXah6-fGpXGsVig2sHVBDIXa3_h4N0nIbjVlv3dC7Vk")

    @property
    def jwt_algorithm(self) -> str:
        return self._config_data.get("jwt", {}).get("algorithm", "HS256")

    @property
    def jwt_expire_minutes(self) -> int:
        return self._config_data.get("jwt", {}).get("access_token_expire_minutes", 30)

    @property
    def cors_origins(self) -> list:
        """获取CORS允许的来源"""
        return self._config_data.get("cors", {}).get("origins", ["http://localhost:3000", "http://127.0.0.1:3000"])

    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, "w") as f:
                toml.dump(self._config_data, f)
            logger.info("✅ Configuration saved successfully")
        except Exception as e:
            logger.error(f"❌ Failed to save configuration: {e}")


settings = Settings()