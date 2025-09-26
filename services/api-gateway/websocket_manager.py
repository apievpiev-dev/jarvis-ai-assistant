"""
WebSocket менеджер для API Gateway
Управление WebSocket соединениями и маршрутизация сообщений
"""
import asyncio
import json
import logging
from typing import Dict, List, Set, Any
from fastapi import WebSocket
from collections import defaultdict

from utils.logger import get_logger

logger = get_logger("gateway-websocket-manager")

class WebSocketManager:
    """Менеджер WebSocket соединений для API Gateway"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        self.service_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self.message_queues: Dict[WebSocket, asyncio.Queue] = {}
        
        # Статистика
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_routed": 0,
            "messages_failed": 0,
            "errors": 0
        }
    
    async def connect(self, websocket: WebSocket):
        """Подключение нового WebSocket клиента"""
        try:
            await websocket.accept()
            
            # Добавление в активные соединения
            self.active_connections.add(websocket)
            self.connection_info[websocket] = {
                "connected_at": asyncio.get_event_loop().time(),
                "last_activity": asyncio.get_event_loop().time(),
                "messages_sent": 0,
                "messages_received": 0,
                "session_id": f"gateway_session_{len(self.active_connections)}",
                "services_subscribed": set()
            }
            
            # Создание очереди сообщений
            self.message_queues[websocket] = asyncio.Queue()
            
            # Обновление статистики
            self.stats["total_connections"] += 1
            self.stats["active_connections"] = len(self.active_connections)
            
            logger.info(f"Gateway WebSocket client connected. Total connections: {self.stats['active_connections']}")
            
            # Отправка приветственного сообщения
            await self.send_message(websocket, {
                "type": "connection_established",
                "message": "Подключение к API Gateway установлено",
                "session_id": self.connection_info[websocket]["session_id"],
                "server_time": asyncio.get_event_loop().time()
            })
            
        except Exception as e:
            logger.error(f"Failed to connect Gateway WebSocket: {e}")
            self.stats["errors"] += 1
            raise
    
    async def disconnect(self, websocket: WebSocket):
        """Отключение WebSocket клиента"""
        try:
            # Удаление из активных соединений
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            
            # Удаление из подписок на сервисы
            if websocket in self.connection_info:
                for service in self.connection_info[websocket]["services_subscribed"]:
                    self.service_connections[service].discard(websocket)
                    if not self.service_connections[service]:
                        del self.service_connections[service]
                
                del self.connection_info[websocket]
            
            # Удаление очереди сообщений
            if websocket in self.message_queues:
                del self.message_queues[websocket]
            
            # Обновление статистики
            self.stats["active_connections"] = len(self.active_connections)
            
            logger.info(f"Gateway WebSocket client disconnected. Active connections: {self.stats['active_connections']}")
            
        except Exception as e:
            logger.error(f"Error during Gateway WebSocket disconnect: {e}")
            self.stats["errors"] += 1
    
    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Отправка сообщения конкретному клиенту"""
        try:
            if websocket in self.active_connections:
                message_json = json.dumps(message, ensure_ascii=False)
                await websocket.send_text(message_json)
                
                # Обновление статистики
                self.stats["messages_routed"] += 1
                
                # Обновление информации о соединении
                if websocket in self.connection_info:
                    self.connection_info[websocket]["last_activity"] = asyncio.get_event_loop().time()
                    self.connection_info[websocket]["messages_sent"] += 1
                
                logger.debug(f"Gateway message sent: {message.get('type', 'unknown')}")
                
        except Exception as e:
            logger.error(f"Failed to send Gateway message: {e}")
            self.stats["messages_failed"] += 1
            self.stats["errors"] += 1
            
            # Удаление неактивного соединения
            await self.disconnect(websocket)
    
    async def broadcast_message(self, message: Dict[str, Any], service: str = None):
        """Отправка сообщения всем клиентам или клиентам подписанным на сервис"""
        try:
            if service and service in self.service_connections:
                # Отправка клиентам подписанным на конкретный сервис
                connections = self.service_connections[service].copy()
            else:
                # Отправка всем активным соединениям
                connections = self.active_connections.copy()
            
            # Отправка сообщения всем соединениям
            tasks = []
            for websocket in connections:
                if websocket in self.active_connections:
                    tasks.append(self.send_message(websocket, message))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info(f"Gateway message broadcasted to {len(connections)} clients")
            
        except Exception as e:
            logger.error(f"Failed to broadcast Gateway message: {e}")
            self.stats["errors"] += 1
    
    async def subscribe_to_service(self, websocket: WebSocket, service: str):
        """Подписка клиента на сообщения от сервиса"""
        try:
            if websocket in self.active_connections:
                self.service_connections[service].add(websocket)
                
                if websocket in self.connection_info:
                    self.connection_info[websocket]["services_subscribed"].add(service)
                
                # Отправка уведомления о подписке
                await self.send_message(websocket, {
                    "type": "service_subscribed",
                    "service": service,
                    "message": f"Подписка на сервис {service} активирована"
                })
                
                logger.info(f"Gateway WebSocket client subscribed to service: {service}")
                
        except Exception as e:
            logger.error(f"Failed to subscribe to service: {e}")
            self.stats["errors"] += 1
    
    async def unsubscribe_from_service(self, websocket: WebSocket, service: str):
        """Отписка клиента от сообщений сервиса"""
        try:
            if service in self.service_connections and websocket in self.service_connections[service]:
                self.service_connections[service].discard(websocket)
                
                if websocket in self.connection_info:
                    self.connection_info[websocket]["services_subscribed"].discard(service)
                
                # Отправка уведомления об отписке
                await self.send_message(websocket, {
                    "type": "service_unsubscribed",
                    "service": service,
                    "message": f"Подписка на сервис {service} отменена"
                })
                
                # Удаление пустой подписки
                if not self.service_connections[service]:
                    del self.service_connections[service]
                
                logger.info(f"Gateway WebSocket client unsubscribed from service: {service}")
                
        except Exception as e:
            logger.error(f"Failed to unsubscribe from service: {e}")
            self.stats["errors"] += 1
    
    async def handle_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Обработка входящего сообщения"""
        try:
            # Обновление статистики
            self.stats["messages_routed"] += 1
            
            # Обновление информации о соединении
            if websocket in self.connection_info:
                self.connection_info[websocket]["last_activity"] = asyncio.get_event_loop().time()
                self.connection_info[websocket]["messages_received"] += 1
            
            message_type = message.get("type")
            
            # Обработка различных типов сообщений
            if message_type == "subscribe_service":
                service = message.get("service")
                if service:
                    await self.subscribe_to_service(websocket, service)
            
            elif message_type == "unsubscribe_service":
                service = message.get("service")
                if service:
                    await self.unsubscribe_from_service(websocket, service)
            
            elif message_type == "ping":
                await self.send_message(websocket, {
                    "type": "pong",
                    "timestamp": asyncio.get_event_loop().time()
                })
            
            elif message_type == "get_stats":
                await self.send_message(websocket, {
                    "type": "stats_response",
                    "stats": self.get_stats()
                })
            
            elif message_type == "get_connection_info":
                connection_info = self.get_connection_info(websocket)
                await self.send_message(websocket, {
                    "type": "connection_info",
                    "info": connection_info
                })
            
            elif message_type == "get_subscribed_services":
                if websocket in self.connection_info:
                    services = list(self.connection_info[websocket]["services_subscribed"])
                    await self.send_message(websocket, {
                        "type": "subscribed_services",
                        "services": services
                    })
            
            else:
                # Передача сообщения в очередь для обработки
                if websocket in self.message_queues:
                    await self.message_queues[websocket].put(message)
            
            logger.debug(f"Gateway message handled: {message_type}")
            
        except Exception as e:
            logger.error(f"Failed to handle Gateway message: {e}")
            self.stats["errors"] += 1
    
    async def get_message(self, websocket: WebSocket) -> Dict[str, Any]:
        """Получение сообщения из очереди"""
        try:
            if websocket in self.message_queues:
                return await self.message_queues[websocket].get()
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get Gateway message: {e}")
            return None
    
    def get_connection_info(self, websocket: WebSocket) -> Dict[str, Any]:
        """Получение информации о соединении"""
        return self.connection_info.get(websocket, {})
    
    def get_service_subscribers(self, service: str) -> List[WebSocket]:
        """Получение списка подписчиков на сервис"""
        return list(self.service_connections.get(service, set()))
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики"""
        return {
            **self.stats,
            "service_subscriptions": {
                service: len(connections) 
                for service, connections in self.service_connections.items()
            },
            "avg_messages_per_connection": (
                self.stats["messages_routed"] / max(self.stats["total_connections"], 1)
            )
        }
    
    async def cleanup_inactive_connections(self, timeout: int = 300):
        """Очистка неактивных соединений"""
        try:
            current_time = asyncio.get_event_loop().time()
            inactive_connections = []
            
            for websocket, info in self.connection_info.items():
                if current_time - info["last_activity"] > timeout:
                    inactive_connections.append(websocket)
            
            for websocket in inactive_connections:
                logger.info("Removing inactive Gateway WebSocket connection")
                await self.disconnect(websocket)
            
            if inactive_connections:
                logger.info(f"Cleaned up {len(inactive_connections)} inactive Gateway connections")
                
        except Exception as e:
            logger.error(f"Failed to cleanup inactive Gateway connections: {e}")
    
    async def start_cleanup_task(self, interval: int = 60):
        """Запуск задачи очистки неактивных соединений"""
        while True:
            try:
                await asyncio.sleep(interval)
                await self.cleanup_inactive_connections()
            except Exception as e:
                logger.error(f"Gateway cleanup task error: {e}")
                await asyncio.sleep(interval)