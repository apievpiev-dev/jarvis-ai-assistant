"""
Балансировщик нагрузки для API Gateway
Распределение запросов между экземплярами сервисов
"""
import random
import time
from typing import Dict, List, Optional, Any
import logging
from enum import Enum
from dataclasses import dataclass

from utils.logger import get_logger

logger = get_logger("load-balancer")

class LoadBalancingStrategy(Enum):
    """Стратегии балансировки нагрузки"""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_RESPONSE_TIME = "least_response_time"

@dataclass
class ServiceInstance:
    """Экземпляр сервиса"""
    url: str
    weight: int = 1
    active_connections: int = 0
    response_time: float = 0.0
    last_used: float = 0.0
    is_healthy: bool = True

class LoadBalancer:
    """Балансировщик нагрузки"""
    
    def __init__(self, service_registry, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN):
        self.service_registry = service_registry
        self.strategy = strategy
        self.service_instances: Dict[str, List[ServiceInstance]] = {}
        self.round_robin_counters: Dict[str, int] = {}
        
        logger.info(f"Load balancer initialized with strategy: {strategy.value}")
    
    async def get_service_url(self, service_name: str) -> Optional[str]:
        """Получение URL сервиса с балансировкой нагрузки"""
        try:
            # Получение экземпляров сервиса
            instances = self.service_instances.get(service_name, [])
            
            if not instances:
                # Если нет экземпляров, попробуем получить из реестра
                service_url = await self.service_registry.get_service_url(service_name)
                if service_url:
                    # Создание экземпляра по умолчанию
                    instance = ServiceInstance(url=service_url)
                    self.service_instances[service_name] = [instance]
                    instances = [instance]
                else:
                    return None
            
            # Фильтрация здоровых экземпляров
            healthy_instances = [inst for inst in instances if inst.is_healthy]
            
            if not healthy_instances:
                logger.warning(f"No healthy instances available for service: {service_name}")
                return None
            
            # Выбор экземпляра по стратегии
            selected_instance = self._select_instance(service_name, healthy_instances)
            
            if selected_instance:
                # Обновление статистики
                selected_instance.active_connections += 1
                selected_instance.last_used = time.time()
                
                return selected_instance.url
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting service URL for {service_name}: {e}")
            return None
    
    def _select_instance(self, service_name: str, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """Выбор экземпляра сервиса по стратегии"""
        if not instances:
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_selection(service_name, instances)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return self._random_selection(instances)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_selection(instances)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_selection(service_name, instances)
        elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return self._least_response_time_selection(instances)
        else:
            # По умолчанию используем round robin
            return self._round_robin_selection(service_name, instances)
    
    def _round_robin_selection(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """Выбор экземпляра по принципу round robin"""
        if service_name not in self.round_robin_counters:
            self.round_robin_counters[service_name] = 0
        
        counter = self.round_robin_counters[service_name]
        selected_instance = instances[counter % len(instances)]
        
        self.round_robin_counters[service_name] = (counter + 1) % len(instances)
        
        return selected_instance
    
    def _random_selection(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Случайный выбор экземпляра"""
        return random.choice(instances)
    
    def _least_connections_selection(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Выбор экземпляра с наименьшим количеством соединений"""
        return min(instances, key=lambda inst: inst.active_connections)
    
    def _weighted_round_robin_selection(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """Взвешенный round robin выбор"""
        # Создание списка экземпляров с учетом весов
        weighted_instances = []
        for instance in instances:
            for _ in range(instance.weight):
                weighted_instances.append(instance)
        
        if not weighted_instances:
            return instances[0]
        
        # Round robin по взвешенному списку
        if service_name not in self.round_robin_counters:
            self.round_robin_counters[service_name] = 0
        
        counter = self.round_robin_counters[service_name]
        selected_instance = weighted_instances[counter % len(weighted_instances)]
        
        self.round_robin_counters[service_name] = (counter + 1) % len(weighted_instances)
        
        return selected_instance
    
    def _least_response_time_selection(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Выбор экземпляра с наименьшим временем ответа"""
        # Фильтрация экземпляров с известным временем ответа
        instances_with_response_time = [inst for inst in instances if inst.response_time > 0]
        
        if instances_with_response_time:
            return min(instances_with_response_time, key=lambda inst: inst.response_time)
        else:
            # Если нет данных о времени ответа, используем round robin
            return instances[0]
    
    async def add_service_instance(self, service_name: str, url: str, weight: int = 1) -> bool:
        """Добавление экземпляра сервиса"""
        try:
            instance = ServiceInstance(url=url, weight=weight)
            
            if service_name not in self.service_instances:
                self.service_instances[service_name] = []
            
            self.service_instances[service_name].append(instance)
            
            logger.info(f"Added service instance: {service_name} at {url} (weight: {weight})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add service instance {service_name}: {e}")
            return False
    
    async def remove_service_instance(self, service_name: str, url: str) -> bool:
        """Удаление экземпляра сервиса"""
        try:
            if service_name in self.service_instances:
                self.service_instances[service_name] = [
                    inst for inst in self.service_instances[service_name] 
                    if inst.url != url
                ]
                
                if not self.service_instances[service_name]:
                    del self.service_instances[service_name]
                
                logger.info(f"Removed service instance: {service_name} at {url}")
                return True
            else:
                logger.warning(f"Service not found for instance removal: {service_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove service instance {service_name}: {e}")
            return False
    
    async def update_instance_health(self, service_name: str, url: str, is_healthy: bool) -> bool:
        """Обновление состояния здоровья экземпляра"""
        try:
            if service_name in self.service_instances:
                for instance in self.service_instances[service_name]:
                    if instance.url == url:
                        instance.is_healthy = is_healthy
                        logger.debug(f"Updated health for {service_name} at {url}: {is_healthy}")
                        return True
            
            logger.warning(f"Instance not found for health update: {service_name} at {url}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to update instance health {service_name}: {e}")
            return False
    
    async def update_instance_response_time(self, service_name: str, url: str, response_time: float) -> bool:
        """Обновление времени ответа экземпляра"""
        try:
            if service_name in self.service_instances:
                for instance in self.service_instances[service_name]:
                    if instance.url == url:
                        instance.response_time = response_time
                        logger.debug(f"Updated response time for {service_name} at {url}: {response_time:.3f}s")
                        return True
            
            logger.warning(f"Instance not found for response time update: {service_name} at {url}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to update instance response time {service_name}: {e}")
            return False
    
    def get_service_instances(self, service_name: str) -> List[ServiceInstance]:
        """Получение экземпляров сервиса"""
        return self.service_instances.get(service_name, [])
    
    def get_all_instances(self) -> Dict[str, List[ServiceInstance]]:
        """Получение всех экземпляров"""
        return self.service_instances.copy()
    
    def get_load_balancer_statistics(self) -> Dict[str, Any]:
        """Получение статистики балансировщика нагрузки"""
        total_instances = sum(len(instances) for instances in self.service_instances.values())
        healthy_instances = sum(
            len([inst for inst in instances if inst.is_healthy]) 
            for instances in self.service_instances.values()
        )
        
        total_connections = sum(
            sum(inst.active_connections for inst in instances)
            for instances in self.service_instances.values()
        )
        
        return {
            "strategy": self.strategy.value,
            "total_instances": total_instances,
            "healthy_instances": healthy_instances,
            "unhealthy_instances": total_instances - healthy_instances,
            "total_active_connections": total_connections,
            "services": {
                service_name: {
                    "total_instances": len(instances),
                    "healthy_instances": len([inst for inst in instances if inst.is_healthy]),
                    "total_connections": sum(inst.active_connections for inst in instances),
                    "average_response_time": sum(inst.response_time for inst in instances) / len(instances) if instances else 0
                }
                for service_name, instances in self.service_instances.items()
            }
        }
    
    def set_strategy(self, strategy: LoadBalancingStrategy):
        """Изменение стратегии балансировки нагрузки"""
        self.strategy = strategy
        logger.info(f"Load balancing strategy changed to: {strategy.value}")
    
    async def cleanup(self):
        """Очистка ресурсов"""
        try:
            self.service_instances.clear()
            self.round_robin_counters.clear()
            logger.info("Load balancer cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during load balancer cleanup: {e}")