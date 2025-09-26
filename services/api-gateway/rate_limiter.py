"""
Rate Limiter для API Gateway
Ограничение скорости запросов для предотвращения злоупотреблений
"""
import time
from typing import Dict, Optional
from collections import defaultdict, deque
import logging
from dataclasses import dataclass

from utils.logger import get_logger

logger = get_logger("rate-limiter")

@dataclass
class RateLimitConfig:
    """Конфигурация ограничения скорости"""
    requests_per_minute: int
    burst_limit: int = 10
    window_size: int = 60  # секунды

class RateLimiter:
    """Ограничитель скорости запросов"""
    
    def __init__(self, requests_per_minute: int):
        self.config = RateLimitConfig(requests_per_minute)
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.blocked_ips: Dict[str, float] = {}
        self.block_duration = 300  # 5 минут блокировки
        
        logger.info(f"Rate limiter initialized: {requests_per_minute} requests per minute")
    
    def is_allowed(self, client_ip: str) -> bool:
        """Проверка разрешения запроса"""
        try:
            current_time = time.time()
            
            # Проверка блокировки IP
            if client_ip in self.blocked_ips:
                if current_time < self.blocked_ips[client_ip]:
                    logger.warning(f"Blocked IP attempted request: {client_ip}")
                    return False
                else:
                    # Блокировка истекла
                    del self.blocked_ips[client_ip]
            
            # Получение истории запросов для IP
            request_times = self.requests[client_ip]
            
            # Удаление старых запросов (старше окна)
            while request_times and current_time - request_times[0] > self.config.window_size:
                request_times.popleft()
            
            # Проверка лимита
            if len(request_times) >= self.config.requests_per_minute:
                # Превышен лимит - блокировка IP
                self.blocked_ips[client_ip] = current_time + self.block_duration
                logger.warning(f"Rate limit exceeded for IP: {client_ip}, blocked for {self.block_duration} seconds")
                return False
            
            # Проверка burst лимита
            recent_requests = sum(1 for req_time in request_times if current_time - req_time < 10)
            if recent_requests >= self.config.burst_limit:
                logger.warning(f"Burst limit exceeded for IP: {client_ip}")
                return False
            
            # Запрос разрешен - добавление времени запроса
            request_times.append(current_time)
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limiter error for IP {client_ip}: {e}")
            return True  # В случае ошибки разрешаем запрос
    
    def get_remaining_requests(self, client_ip: str) -> int:
        """Получение количества оставшихся запросов"""
        try:
            current_time = time.time()
            request_times = self.requests[client_ip]
            
            # Удаление старых запросов
            while request_times and current_time - request_times[0] > self.config.window_size:
                request_times.popleft()
            
            remaining = max(0, self.config.requests_per_minute - len(request_times))
            return remaining
            
        except Exception as e:
            logger.error(f"Error getting remaining requests for IP {client_ip}: {e}")
            return self.config.requests_per_minute
    
    def get_reset_time(self, client_ip: str) -> Optional[float]:
        """Получение времени сброса лимита"""
        try:
            if client_ip in self.blocked_ips:
                return self.blocked_ips[client_ip]
            
            request_times = self.requests[client_ip]
            if not request_times:
                return None
            
            # Время самого старого запроса + окно
            oldest_request = request_times[0]
            return oldest_request + self.config.window_size
            
        except Exception as e:
            logger.error(f"Error getting reset time for IP {client_ip}: {e}")
            return None
    
    def is_blocked(self, client_ip: str) -> bool:
        """Проверка блокировки IP"""
        if client_ip not in self.blocked_ips:
            return False
        
        current_time = time.time()
        if current_time >= self.blocked_ips[client_ip]:
            # Блокировка истекла
            del self.blocked_ips[client_ip]
            return False
        
        return True
    
    def unblock_ip(self, client_ip: str) -> bool:
        """Разблокировка IP"""
        try:
            if client_ip in self.blocked_ips:
                del self.blocked_ips[client_ip]
                logger.info(f"IP unblocked: {client_ip}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error unblocking IP {client_ip}: {e}")
            return False
    
    def clear_ip_history(self, client_ip: str) -> bool:
        """Очистка истории запросов для IP"""
        try:
            if client_ip in self.requests:
                del self.requests[client_ip]
                logger.info(f"Request history cleared for IP: {client_ip}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error clearing history for IP {client_ip}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, any]:
        """Получение статистики rate limiter"""
        try:
            current_time = time.time()
            
            # Подсчет активных IP
            active_ips = 0
            total_requests = 0
            
            for ip, request_times in self.requests.items():
                # Удаление старых запросов
                while request_times and current_time - request_times[0] > self.config.window_size:
                    request_times.popleft()
                
                if request_times:
                    active_ips += 1
                    total_requests += len(request_times)
            
            # Подсчет заблокированных IP
            blocked_ips = 0
            for block_time in self.blocked_ips.values():
                if current_time < block_time:
                    blocked_ips += 1
            
            return {
                "active_ips": active_ips,
                "blocked_ips": blocked_ips,
                "total_requests": total_requests,
                "requests_per_minute_limit": self.config.requests_per_minute,
                "burst_limit": self.config.burst_limit,
                "window_size": self.config.window_size,
                "block_duration": self.block_duration
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limiter stats: {e}")
            return {}
    
    def cleanup_expired_entries(self):
        """Очистка истекших записей"""
        try:
            current_time = time.time()
            
            # Очистка истекших блокировок
            expired_blocks = [
                ip for ip, block_time in self.blocked_ips.items()
                if current_time >= block_time
            ]
            
            for ip in expired_blocks:
                del self.blocked_ips[ip]
            
            # Очистка старых запросов
            for ip, request_times in self.requests.items():
                while request_times and current_time - request_times[0] > self.config.window_size:
                    request_times.popleft()
                
                # Удаление пустых записей
                if not request_times:
                    del self.requests[ip]
            
            if expired_blocks:
                logger.info(f"Cleaned up {len(expired_blocks)} expired block entries")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def update_config(self, requests_per_minute: int, burst_limit: int = None, window_size: int = None):
        """Обновление конфигурации"""
        try:
            self.config.requests_per_minute = requests_per_minute
            
            if burst_limit is not None:
                self.config.burst_limit = burst_limit
            
            if window_size is not None:
                self.config.window_size = window_size
            
            logger.info(f"Rate limiter config updated: {requests_per_minute} req/min, burst: {self.config.burst_limit}, window: {self.config.window_size}s")
            
        except Exception as e:
            logger.error(f"Error updating rate limiter config: {e}")
    
    def reset_all(self):
        """Сброс всех данных"""
        try:
            self.requests.clear()
            self.blocked_ips.clear()
            logger.info("Rate limiter data reset")
            
        except Exception as e:
            logger.error(f"Error resetting rate limiter: {e}")