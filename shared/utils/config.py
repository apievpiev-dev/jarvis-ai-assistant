"""
Configuration utilities for Jarvis AI Assistant
"""
import os
import json
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class DatabaseConfig:
    """Конфигурация базы данных"""
    postgres_url: str
    redis_url: str
    max_connections: int = 20
    min_connections: int = 5
    command_timeout: int = 60

@dataclass
class ModelConfig:
    """Конфигурация AI моделей"""
    model_path: str
    whisper_model: str = "base"
    phi2_model: str = "microsoft/phi-2"
    tts_model: str = "tts_models/ru/ruslan"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    device: str = "cpu"
    max_tokens: int = 2048
    temperature: float = 0.7

@dataclass
class ServiceConfig:
    """Конфигурация сервиса"""
    name: str
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    log_level: str = "INFO"
    debug: bool = False

@dataclass
class SecurityConfig:
    """Конфигурация безопасности"""
    secret_key: str
    jwt_expire_hours: int = 24
    allowed_origins: List[str] = None
    rate_limit_per_minute: int = 100
    
    def __post_init__(self):
        if self.allowed_origins is None:
            self.allowed_origins = ["*"]

@dataclass
class MonitoringConfig:
    """Конфигурация мониторинга"""
    prometheus_port: int = 9090
    grafana_port: int = 3001
    metrics_enabled: bool = True
    health_check_interval: int = 30

@dataclass
class JarvisConfig:
    """Основная конфигурация Jarvis"""
    database: DatabaseConfig
    model: ModelConfig
    service: ServiceConfig
    security: SecurityConfig
    monitoring: MonitoringConfig
    
    # Дополнительные настройки
    language: str = "ru"
    auto_learning: bool = True
    voice_enabled: bool = True
    max_concurrent_tasks: int = 10
    task_timeout: int = 300

class ConfigManager:
    """Менеджер конфигурации"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.getenv("JARVIS_CONFIG_PATH", "./config")
        self._config: Optional[JarvisConfig] = None
    
    def load_config(self) -> JarvisConfig:
        """Загрузка конфигурации"""
        if self._config is not None:
            return self._config
        
        # Загрузка из переменных окружения
        config_data = self._load_from_env()
        
        # Загрузка из файлов конфигурации
        config_files = self._find_config_files()
        for config_file in config_files:
            file_config = self._load_from_file(config_file)
            config_data = self._merge_configs(config_data, file_config)
        
        # Создание объекта конфигурации
        self._config = self._create_config_object(config_data)
        return self._config
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Загрузка конфигурации из переменных окружения"""
        return {
            "database": {
                "postgres_url": os.getenv("POSTGRES_URL", "postgresql://jarvis:jarvis_password@localhost:5432/jarvis"),
                "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
                "max_connections": int(os.getenv("DB_MAX_CONNECTIONS", "20")),
                "min_connections": int(os.getenv("DB_MIN_CONNECTIONS", "5")),
                "command_timeout": int(os.getenv("DB_COMMAND_TIMEOUT", "60"))
            },
            "model": {
                "model_path": os.getenv("MODEL_PATH", "./models"),
                "whisper_model": os.getenv("WHISPER_MODEL", "base"),
                "phi2_model": os.getenv("PHI2_MODEL", "microsoft/phi-2"),
                "tts_model": os.getenv("TTS_MODEL", "tts_models/ru/ruslan"),
                "embedding_model": os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
                "device": os.getenv("MODEL_DEVICE", "cpu"),
                "max_tokens": int(os.getenv("MODEL_MAX_TOKENS", "2048")),
                "temperature": float(os.getenv("MODEL_TEMPERATURE", "0.7"))
            },
            "service": {
                "name": os.getenv("SERVICE_NAME", "jarvis"),
                "host": os.getenv("SERVICE_HOST", "0.0.0.0"),
                "port": int(os.getenv("SERVICE_PORT", "8000")),
                "workers": int(os.getenv("SERVICE_WORKERS", "1")),
                "log_level": os.getenv("LOG_LEVEL", "INFO"),
                "debug": os.getenv("DEBUG", "false").lower() == "true"
            },
            "security": {
                "secret_key": os.getenv("SECRET_KEY", "jarvis-secret-key-change-in-production"),
                "jwt_expire_hours": int(os.getenv("JWT_EXPIRE_HOURS", "24")),
                "allowed_origins": os.getenv("ALLOWED_ORIGINS", "*").split(","),
                "rate_limit_per_minute": int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
            },
            "monitoring": {
                "prometheus_port": int(os.getenv("PROMETHEUS_PORT", "9090")),
                "grafana_port": int(os.getenv("GRAFANA_PORT", "3001")),
                "metrics_enabled": os.getenv("METRICS_ENABLED", "true").lower() == "true",
                "health_check_interval": int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
            },
            "language": os.getenv("JARVIS_LANGUAGE", "ru"),
            "auto_learning": os.getenv("AUTO_LEARNING", "true").lower() == "true",
            "voice_enabled": os.getenv("VOICE_ENABLED", "true").lower() == "true",
            "max_concurrent_tasks": int(os.getenv("MAX_CONCURRENT_TASKS", "10")),
            "task_timeout": int(os.getenv("TASK_TIMEOUT", "300"))
        }
    
    def _find_config_files(self) -> List[Path]:
        """Поиск файлов конфигурации"""
        config_dir = Path(self.config_path)
        config_files = []
        
        if config_dir.exists():
            # Поиск файлов конфигурации
            for pattern in ["*.yaml", "*.yml", "*.json"]:
                config_files.extend(config_dir.glob(pattern))
        
        return sorted(config_files)
    
    def _load_from_file(self, config_file: Path) -> Dict[str, Any]:
        """Загрузка конфигурации из файла"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.suffix in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                elif config_file.suffix == '.json':
                    return json.load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to load config file {config_file}: {e}")
        
        return {}
    
    def _merge_configs(self, base_config: Dict[str, Any], 
                      override_config: Dict[str, Any]) -> Dict[str, Any]:
        """Слияние конфигураций"""
        result = base_config.copy()
        
        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _create_config_object(self, config_data: Dict[str, Any]) -> JarvisConfig:
        """Создание объекта конфигурации"""
        return JarvisConfig(
            database=DatabaseConfig(**config_data.get("database", {})),
            model=ModelConfig(**config_data.get("model", {})),
            service=ServiceConfig(**config_data.get("service", {})),
            security=SecurityConfig(**config_data.get("security", {})),
            monitoring=MonitoringConfig(**config_data.get("monitoring", {})),
            language=config_data.get("language", "ru"),
            auto_learning=config_data.get("auto_learning", True),
            voice_enabled=config_data.get("voice_enabled", True),
            max_concurrent_tasks=config_data.get("max_concurrent_tasks", 10),
            task_timeout=config_data.get("task_timeout", 300)
        )
    
    def save_config(self, config: JarvisConfig, file_path: str):
        """Сохранение конфигурации в файл"""
        config_dict = asdict(config)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            if file_path.endswith('.json'):
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            else:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
    
    def get_config(self) -> JarvisConfig:
        """Получение текущей конфигурации"""
        return self.load_config()
    
    def reload_config(self) -> JarvisConfig:
        """Перезагрузка конфигурации"""
        self._config = None
        return self.load_config()

# Глобальный экземпляр менеджера конфигурации
config_manager = ConfigManager()

def get_config() -> JarvisConfig:
    """Получение конфигурации"""
    return config_manager.get_config()

def reload_config() -> JarvisConfig:
    """Перезагрузка конфигурации"""
    return config_manager.reload_config()