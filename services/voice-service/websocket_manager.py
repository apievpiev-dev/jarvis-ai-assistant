"""
WebSocket менеджер для Voice Service
Управление WebSocket соединениями в реальном времени
"""
import asyncio
import json
import logging
from typing import Dict, List, Set, Any
from fastapi import WebSocket
from collections import defaultdict

from utils.logger import get_logger

logger = get_logger("websocket-manager")

class WebSocketManager:
    """Менеджер WebSocket соединений"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        self.rooms: Dict[str, Set[WebSocket]] = defaultdict(set)
        self.message_queues: Dict[WebSocket, asyncio.Queue] = {}
        
        # Статистика
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
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
                "message_count": 0
            }
            
            # Создание очереди сообщений
            self.message_queues[websocket] = asyncio.Queue()
            
            # Обновление статистики
            self.stats["total_connections"] += 1
            self.stats["active_connections"] = len(self.active_connections)
            
            logger.info(f"WebSocket client connected. Total connections: {self.stats['active_connections']}")
            
            # Отправка приветственного сообщения
            await self.send_message(websocket, {
                "type": "connection_established",
                "message": "Подключение установлено",
                "server_time": asyncio.get_event_loop().time()
            })
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            self.stats["errors"] += 1
            raise
    
    async def disconnect(self, websocket: WebSocket):
        """Отключение WebSocket клиента"""
        try:
            # Удаление из активных соединений
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            
            # Удаление информации о соединении
            if websocket in self.connection_info:
                del self.connection_info[websocket]
            
            # Удаление из всех комнат
            for room_name, room_connections in self.rooms.items():
                room_connections.discard(websocket)
                if not room_connections:
                    del self.rooms[room_name]
            
            # Удаление очереди сообщений
            if websocket in self.message_queues:
                del self.message_queues[websocket]
            
            # Обновление статистики
            self.stats["active_connections"] = len(self.active_connections)
            
            logger.info(f"WebSocket client disconnected. Active connections: {self.stats['active_connections']}")
            
        except Exception as e:
            logger.error(f"Error during WebSocket disconnect: {e}")
            self.stats["errors"] += 1
    
    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Отправка сообщения конкретному клиенту"""
        try:
            if websocket in self.active_connections:
                message_json = json.dumps(message, ensure_ascii=False)
                await websocket.send_text(message_json)
                
                # Обновление статистики
                self.stats["messages_sent"] += 1
                
                # Обновление информации о соединении
                if websocket in self.connection_info:
                    self.connection_info[websocket]["last_activity"] = asyncio.get_event_loop().time()
                
                logger.debug(f"Message sent to WebSocket client: {message['type']}")
                
        except Exception as e:
            logger.error(f"Failed to send message to WebSocket: {e}")
            self.stats["errors"] += 1
            
            # Удаление неактивного соединения
            await self.disconnect(websocket)
    
    async def broadcast_message(self, message: Dict[str, Any], room: str = None):
        """Отправка сообщения всем клиентам или клиентам в комнате"""
        try:
            if room and room in self.rooms:
                # Отправка в конкретную комнату
                connections = self.rooms[room].copy()
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
            
            logger.info(f"Message broadcasted to {len(connections)} clients")
            
        except Exception as e:
            logger.error(f"Failed to broadcast message: {e}")
            self.stats["errors"] += 1
    
    async def join_room(self, websocket: WebSocket, room: str):
        """Добавление клиента в комнату"""
        try:
            if websocket in self.active_connections:
                self.rooms[room].add(websocket)
                
                # Отправка уведомления о присоединении к комнате
                await self.send_message(websocket, {
                    "type": "room_joined",
                    "room": room,
                    "message": f"Вы присоединились к комнате {room}"
                })
                
                logger.info(f"WebSocket client joined room: {room}")
                
        except Exception as e:
            logger.error(f"Failed to join room: {e}")
            self.stats["errors"] += 1
    
    async def leave_room(self, websocket: WebSocket, room: str):
        """Удаление клиента из комнаты"""
        try:
            if room in self.rooms and websocket in self.rooms[room]:
                self.rooms[room].discard(websocket)
                
                # Отправка уведомления о выходе из комнаты
                await self.send_message(websocket, {
                    "type": "room_left",
                    "room": room,
                    "message": f"Вы покинули комнату {room}"
                })
                
                # Удаление пустой комнаты
                if not self.rooms[room]:
                    del self.rooms[room]
                
                logger.info(f"WebSocket client left room: {room}")
                
        except Exception as e:
            logger.error(f"Failed to leave room: {e}")
            self.stats["errors"] += 1
    
    async def handle_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Обработка входящего сообщения"""
        try:
            # Обновление статистики
            self.stats["messages_received"] += 1
            
            # Обновление информации о соединении
            if websocket in self.connection_info:
                self.connection_info[websocket]["last_activity"] = asyncio.get_event_loop().time()
                self.connection_info[websocket]["message_count"] += 1
            
            message_type = message.get("type")
            
            # Обработка различных типов сообщений
            if message_type == "join_room":
                room = message.get("room")
                if room:
                    await self.join_room(websocket, room)
            
            elif message_type == "leave_room":
                room = message.get("room")
                if room:
                    await self.leave_room(websocket, room)
            
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
            
            else:
                # Передача сообщения в очередь для обработки
                if websocket in self.message_queues:
                    await self.message_queues[websocket].put(message)
            
            logger.debug(f"Message handled: {message_type}")
            
        except Exception as e:
            logger.error(f"Failed to handle message: {e}")
            self.stats["errors"] += 1
    
    async def get_message(self, websocket: WebSocket) -> Dict[str, Any]:
        """Получение сообщения из очереди"""
        try:
            if websocket in self.message_queues:
                return await self.message_queues[websocket].get()
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get message: {e}")
            return None
    
    def get_connection_info(self, websocket: WebSocket) -> Dict[str, Any]:
        """Получение информации о соединении"""
        return self.connection_info.get(websocket, {})
    
    def get_room_info(self, room: str) -> Dict[str, Any]:
        """Получение информации о комнате"""
        if room in self.rooms:
            return {
                "name": room,
                "connections": len(self.rooms[room]),
                "active": True
            }
        else:
            return {
                "name": room,
                "connections": 0,
                "active": False
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики"""
        return {
            **self.stats,
            "rooms": len(self.rooms),
            "room_list": list(self.rooms.keys())
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
                logger.info("Removing inactive WebSocket connection")
                await self.disconnect(websocket)
            
            if inactive_connections:
                logger.info(f"Cleaned up {len(inactive_connections)} inactive connections")
                
        except Exception as e:
            logger.error(f"Failed to cleanup inactive connections: {e}")
    
    async def start_cleanup_task(self, interval: int = 60):
        """Запуск задачи очистки неактивных соединений"""
        while True:
            try:
                await asyncio.sleep(interval)
                await self.cleanup_inactive_connections()
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
                await asyncio.sleep(interval)