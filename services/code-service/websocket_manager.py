#!/usr/bin/env python3
"""
WebSocket Manager для Code Service
Автор: Jarvis AI Assistant
Версия: 1.0.0
"""

import asyncio
import logging
from typing import Dict, List, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Менеджер WebSocket соединений"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_info: Dict[WebSocket, Dict] = {}
        
    async def connect(self, websocket: WebSocket):
        """Подключение нового клиента"""
        try:
            await websocket.accept()
            self.active_connections.add(websocket)
            self.connection_info[websocket] = {
                "connected_at": asyncio.get_event_loop().time(),
                "last_activity": asyncio.get_event_loop().time(),
                "message_count": 0
            }
            logger.info(f"Новое WebSocket соединение. Всего соединений: {len(self.active_connections)}")
        except Exception as e:
            logger.error(f"Ошибка подключения WebSocket: {e}")
            raise
    
    def disconnect(self, websocket: WebSocket):
        """Отключение клиента"""
        try:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                if websocket in self.connection_info:
                    del self.connection_info[websocket]
                logger.info(f"WebSocket соединение закрыто. Всего соединений: {len(self.active_connections)}")
        except Exception as e:
            logger.error(f"Ошибка отключения WebSocket: {e}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Отправка личного сообщения"""
        try:
            if websocket in self.active_connections:
                await websocket.send_text(message)
                self._update_activity(websocket)
        except Exception as e:
            logger.error(f"Ошибка отправки личного сообщения: {e}")
            self.disconnect(websocket)
    
    async def send_personal_json(self, data: Dict, websocket: WebSocket):
        """Отправка личного JSON сообщения"""
        try:
            if websocket in self.active_connections:
                await websocket.send_json(data)
                self._update_activity(websocket)
        except Exception as e:
            logger.error(f"Ошибка отправки личного JSON: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Рассылка сообщения всем клиентам"""
        try:
            disconnected = set()
            for websocket in self.active_connections.copy():
                try:
                    await websocket.send_text(message)
                    self._update_activity(websocket)
                except Exception as e:
                    logger.error(f"Ошибка рассылки: {e}")
                    disconnected.add(websocket)
            
            # Удаление отключенных соединений
            for websocket in disconnected:
                self.disconnect(websocket)
                
        except Exception as e:
            logger.error(f"Ошибка рассылки сообщений: {e}")
    
    async def broadcast_json(self, data: Dict):
        """Рассылка JSON сообщения всем клиентам"""
        try:
            disconnected = set()
            for websocket in self.active_connections.copy():
                try:
                    await websocket.send_json(data)
                    self._update_activity(websocket)
                except Exception as e:
                    logger.error(f"Ошибка рассылки JSON: {e}")
                    disconnected.add(websocket)
            
            # Удаление отключенных соединений
            for websocket in disconnected:
                self.disconnect(websocket)
                
        except Exception as e:
            logger.error(f"Ошибка рассылки JSON сообщений: {e}")
    
    def _update_activity(self, websocket: WebSocket):
        """Обновление активности соединения"""
        try:
            if websocket in self.connection_info:
                self.connection_info[websocket]["last_activity"] = asyncio.get_event_loop().time()
                self.connection_info[websocket]["message_count"] += 1
        except Exception as e:
            logger.error(f"Ошибка обновления активности: {e}")
    
    def get_connection_stats(self) -> Dict:
        """Получение статистики соединений"""
        try:
            current_time = asyncio.get_event_loop().time()
            stats = {
                "total_connections": len(self.active_connections),
                "connections": []
            }
            
            for websocket, info in self.connection_info.items():
                connection_time = current_time - info["connected_at"]
                last_activity = current_time - info["last_activity"]
                
                stats["connections"].append({
                    "connected_for": round(connection_time, 2),
                    "last_activity": round(last_activity, 2),
                    "message_count": info["message_count"]
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {"total_connections": 0, "connections": []}
    
    async def cleanup_inactive_connections(self, timeout: int = 300):
        """Очистка неактивных соединений"""
        try:
            current_time = asyncio.get_event_loop().time()
            inactive_connections = set()
            
            for websocket, info in self.connection_info.items():
                if current_time - info["last_activity"] > timeout:
                    inactive_connections.add(websocket)
            
            for websocket in inactive_connections:
                logger.info("Удаление неактивного соединения")
                self.disconnect(websocket)
                
        except Exception as e:
            logger.error(f"Ошибка очистки неактивных соединений: {e}")