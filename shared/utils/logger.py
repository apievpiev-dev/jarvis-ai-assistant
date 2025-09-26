"""
Logging utilities for Jarvis AI Assistant
"""
import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
import sys
import os

class JarvisLogger:
    """Централизованный логгер для Jarvis"""
    
    def __init__(self, service_name: str, log_level: str = "INFO"):
        self.service_name = service_name
        self.log_level = getattr(logging, log_level.upper())
        
        # Настройка логгера
        self.logger = logging.getLogger(f"jarvis.{service_name}")
        self.logger.setLevel(self.log_level)
        
        # Удаление существующих обработчиков
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Форматтер
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Консольный обработчик
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Файловый обработчик
        log_dir = "/app/logs" if os.path.exists("/app/logs") else "./logs"
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(f"{log_dir}/{service_name}.log")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def _log_with_context(self, level: str, message: str, context: Optional[Dict[str, Any]] = None):
        """Логирование с контекстом"""
        log_data = {
            "service": self.service_name,
            "level": level,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "context": context or {}
        }
        
        getattr(self.logger, level.lower())(json.dumps(log_data, ensure_ascii=False))
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Debug уровень логирования"""
        self._log_with_context("DEBUG", message, context)
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Info уровень логирования"""
        self._log_with_context("INFO", message, context)
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Warning уровень логирования"""
        self._log_with_context("WARNING", message, context)
    
    def error(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Error уровень логирования"""
        self._log_with_context("ERROR", message, context)
    
    def critical(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Critical уровень логирования"""
        self._log_with_context("CRITICAL", message, context)

class MetricsLogger:
    """Логгер метрик для мониторинга"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.metrics = {}
    
    def increment_counter(self, metric_name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """Увеличение счетчика"""
        key = f"{metric_name}_{json.dumps(labels or {}, sort_keys=True)}"
        self.metrics[key] = self.metrics.get(key, 0) + value
    
    def set_gauge(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Установка значения gauge"""
        key = f"{metric_name}_{json.dumps(labels or {}, sort_keys=True)}"
        self.metrics[key] = value
    
    def record_histogram(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Запись значения в гистограмму"""
        key = f"{metric_name}_{json.dumps(labels or {}, sort_keys=True)}"
        if key not in self.metrics:
            self.metrics[key] = []
        self.metrics[key].append(value)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Получение всех метрик"""
        return {
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": self.metrics
        }

class PerformanceLogger:
    """Логгер производительности"""
    
    def __init__(self, logger: JarvisLogger):
        self.logger = logger
        self.start_times = {}
    
    @asynccontextmanager
    async def time_operation(self, operation_name: str, context: Optional[Dict[str, Any]] = None):
        """Контекстный менеджер для измерения времени выполнения"""
        start_time = datetime.utcnow()
        self.start_times[operation_name] = start_time
        
        try:
            yield
        finally:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.info(
                f"Operation '{operation_name}' completed",
                context={
                    **(context or {}),
                    "duration_seconds": duration,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                }
            )
            
            # Очистка
            if operation_name in self.start_times:
                del self.start_times[operation_name]
    
    def start_timer(self, operation_name: str):
        """Начало измерения времени"""
        self.start_times[operation_name] = datetime.utcnow()
    
    def end_timer(self, operation_name: str, context: Optional[Dict[str, Any]] = None):
        """Окончание измерения времени"""
        if operation_name not in self.start_times:
            self.logger.warning(f"Timer '{operation_name}' was not started")
            return
        
        start_time = self.start_times[operation_name]
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        self.logger.info(
            f"Operation '{operation_name}' completed",
            context={
                **(context or {}),
                "duration_seconds": duration,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
        )
        
        del self.start_times[operation_name]

class ErrorLogger:
    """Специализированный логгер ошибок"""
    
    def __init__(self, logger: JarvisLogger):
        self.logger = logger
    
    def log_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None):
        """Логирование исключения с полным контекстом"""
        import traceback
        
        self.logger.error(
            f"Exception occurred: {str(exception)}",
            context={
                **(context or {}),
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "traceback": traceback.format_exc()
            }
        )
    
    def log_error_with_recovery(self, error: str, recovery_action: str, 
                               context: Optional[Dict[str, Any]] = None):
        """Логирование ошибки с действием восстановления"""
        self.logger.warning(
            f"Error occurred: {error}. Recovery action: {recovery_action}",
            context={
                **(context or {}),
                "error": error,
                "recovery_action": recovery_action
            }
        )

# Глобальные экземпляры логгеров
_loggers = {}
_metrics_loggers = {}

def get_logger(service_name: str, log_level: str = "INFO") -> JarvisLogger:
    """Получение логгера для сервиса"""
    if service_name not in _loggers:
        _loggers[service_name] = JarvisLogger(service_name, log_level)
    return _loggers[service_name]

def get_metrics_logger(service_name: str) -> MetricsLogger:
    """Получение логгера метрик для сервиса"""
    if service_name not in _metrics_loggers:
        _metrics_loggers[service_name] = MetricsLogger(service_name)
    return _metrics_loggers[service_name]

def get_performance_logger(service_name: str) -> PerformanceLogger:
    """Получение логгера производительности для сервиса"""
    logger = get_logger(service_name)
    return PerformanceLogger(logger)

def get_error_logger(service_name: str) -> ErrorLogger:
    """Получение логгера ошибок для сервиса"""
    logger = get_logger(service_name)
    return ErrorLogger(logger)