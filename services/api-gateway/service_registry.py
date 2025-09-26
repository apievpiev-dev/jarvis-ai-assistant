"""
Реестр сервисов для API Gateway
Управление регистрацией и обнаружением сервисов
"""
import asyncio
import time
from typing import Dict, List, Optional, Any
import logging
import httpx
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from utils.logger import get_logger

logger = get_logger("service-registry")

@dataclass
class ServiceInfo:
    """Информация о сервисе"""
    name: str
    url: str
    health_url: str
    registered_at: datetime
    last_health_check: Optional[datetime]
    is_healthy: bool
    response_time: Optional[float]
    metadata: Dict[str, Any]

class ServiceRegistry:
    """Реестр сервисов"""
    
    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {}
        self.health_check_interval = 30  # секунды
        self.health_check_timeout = 10  # секунды
        self.health_check_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        logger.info("Service registry initialized")
    
    async def register_service(self, name: str, url: str, metadata: Dict[str, Any] = None) -> bool:
        """Регистрация сервиса"""
        try:
            # Нормализация URL
            if not url.startswith(("http://", "https://")):
                url = f"http://{url}"
            
            # Создание URL для проверки здоровья
            health_url = f"{url}/health"
            
            # Проверка доступности сервиса
            is_healthy = await self._check_service_health(health_url)
            
            # Создание информации о сервисе
            service_info = ServiceInfo(
                name=name,
                url=url,
                health_url=health_url,
                registered_at=datetime.now(),
                last_health_check=datetime.now(),
                is_healthy=is_healthy,
                response_time=None,
                metadata=metadata or {}
            )
            
            # Регистрация сервиса
            self.services[name] = service_info
            
            logger.info(f"Service registered: {name} at {url} (healthy: {is_healthy})")
            
            # Запуск мониторинга здоровья, если еще не запущен
            if not self.is_running:
                await self.start_health_monitoring()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to register service {name}: {e}")
            return False
    
    async def unregister_service(self, name: str) -> bool:
        """Отмена регистрации сервиса"""
        try:
            if name in self.services:
                del self.services[name]
                logger.info(f"Service unregistered: {name}")
                return True
            else:
                logger.warning(f"Service not found for unregistration: {name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to unregister service {name}: {e}")
            return False
    
    async def get_service_url(self, name: str) -> Optional[str]:
        """Получение URL сервиса"""
        if name in self.services and self.services[name].is_healthy:
            return self.services[name].url
        return None
    
    async def get_service_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Получение информации о сервисе"""
        if name in self.services:
            service = self.services[name]
            info = asdict(service)
            # Конвертация datetime в строки
            for key, value in info.items():
                if isinstance(value, datetime):
                    info[key] = value.isoformat()
            return info
        return None
    
    def get_all_services(self) -> List[Dict[str, Any]]:
        """Получение информации о всех сервисах"""
        services = []
        for service in self.services.values():
            info = asdict(service)
            # Конвертация datetime в строки
            for key, value in info.items():
                if isinstance(value, datetime):
                    info[key] = value.isoformat()
            services.append(info)
        return services
    
    def get_registered_services(self) -> List[str]:
        """Получение списка зарегистрированных сервисов"""
        return list(self.services.keys())
    
    async def is_service_healthy(self, name: str) -> bool:
        """Проверка здоровья сервиса"""
        if name in self.services:
            return self.services[name].is_healthy
        return False
    
    async def _check_service_health(self, health_url: str) -> bool:
        """Проверка здоровья сервиса"""
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=self.health_check_timeout) as client:
                response = await client.get(health_url)
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    # Проверка содержимого ответа
                    try:
                        data = response.json()
                        is_healthy = data.get("status") == "healthy"
                    except:
                        is_healthy = True  # Если не JSON, считаем здоровым при 200
                    
                    return is_healthy
                else:
                    return False
                    
        except Exception as e:
            logger.debug(f"Health check failed for {health_url}: {e}")
            return False
    
    async def _update_service_health(self, name: str, service_info: ServiceInfo):
        """Обновление информации о здоровье сервиса"""
        try:
            start_time = time.time()
            is_healthy = await self._check_service_health(service_info.health_url)
            response_time = time.time() - start_time
            
            # Обновление информации
            service_info.last_health_check = datetime.now()
            service_info.is_healthy = is_healthy
            service_info.response_time = response_time if is_healthy else None
            
            if is_healthy:
                logger.debug(f"Service {name} is healthy (response time: {response_time:.3f}s)")
            else:
                logger.warning(f"Service {name} is unhealthy")
                
        except Exception as e:
            logger.error(f"Error updating health for service {name}: {e}")
            service_info.is_healthy = False
            service_info.last_health_check = datetime.now()
    
    async def start_health_monitoring(self):
        """Запуск мониторинга здоровья сервисов"""
        if self.is_running:
            return
        
        self.is_running = True
        self.health_check_task = asyncio.create_task(self._health_monitoring_loop())
        logger.info("Health monitoring started")
    
    async def stop_health_monitoring(self):
        """Остановка мониторинга здоровья сервисов"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Health monitoring stopped")
    
    async def _health_monitoring_loop(self):
        """Основной цикл мониторинга здоровья"""
        while self.is_running:
            try:
                # Проверка здоровья всех сервисов
                tasks = []
                for name, service_info in self.services.items():
                    task = self._update_service_health(name, service_info)
                    tasks.append(task)
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                # Ожидание до следующей проверки
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring loop error: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def get_healthy_services(self) -> List[str]:
        """Получение списка здоровых сервисов"""
        healthy_services = []
        for name, service_info in self.services.items():
            if service_info.is_healthy:
                healthy_services.append(name)
        return healthy_services
    
    async def get_unhealthy_services(self) -> List[str]:
        """Получение списка нездоровых сервисов"""
        unhealthy_services = []
        for name, service_info in self.services.items():
            if not service_info.is_healthy:
                unhealthy_services.append(name)
        return unhealthy_services
    
    def get_service_statistics(self) -> Dict[str, Any]:
        """Получение статистики сервисов"""
        total_services = len(self.services)
        healthy_services = sum(1 for s in self.services.values() if s.is_healthy)
        unhealthy_services = total_services - healthy_services
        
        # Среднее время ответа
        response_times = [s.response_time for s in self.services.values() if s.response_time is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "unhealthy_services": unhealthy_services,
            "health_percentage": (healthy_services / total_services * 100) if total_services > 0 else 0,
            "average_response_time": avg_response_time,
            "monitoring_active": self.is_running
        }
    
    async def cleanup(self):
        """Очистка ресурсов"""
        try:
            await self.stop_health_monitoring()
            self.services.clear()
            logger.info("Service registry cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during service registry cleanup: {e}")