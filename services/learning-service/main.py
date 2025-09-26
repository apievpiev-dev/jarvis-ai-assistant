#!/usr/bin/env python3
"""
Learning Service - Сервис самообучения
Автор: Jarvis AI Assistant
Версия: 1.0.0
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Добавление пути к shared модулям
sys.path.append('/app/shared')

from utils.logger import setup_logger
from utils.config import get_config
from learning_engine import LearningEngine
from knowledge_base import KnowledgeBase
from adaptation_engine import AdaptationEngine
from websocket_manager import WebSocketManager

# Настройка логирования
logger = setup_logger(__name__)

# Конфигурация
config = get_config()

# Менеджер WebSocket соединений
websocket_manager = WebSocketManager()

# Инициализация компонентов
learning_engine = LearningEngine()
knowledge_base = KnowledgeBase()
adaptation_engine = AdaptationEngine()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("Запуск Learning Service...")
    
    # Инициализация компонентов
    await learning_engine.initialize()
    await knowledge_base.initialize()
    await adaptation_engine.initialize()
    
    logger.info("Learning Service запущен")
    
    yield
    
    logger.info("Остановка Learning Service...")
    await learning_engine.cleanup()
    await knowledge_base.cleanup()
    await adaptation_engine.cleanup()
    logger.info("Learning Service остановлен")

# Создание FastAPI приложения
app = FastAPI(
    title="Jarvis Learning Service",
    description="Сервис самообучения и адаптации",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "learning-service",
        "version": "1.0.0"
    }

@app.get("/status")
async def get_status():
    """Получение статуса сервиса"""
    return {
        "status": "running",
        "learning_engine_ready": learning_engine.is_ready(),
        "knowledge_base_ready": knowledge_base.is_ready(),
        "adaptation_engine_ready": adaptation_engine.is_ready(),
        "active_connections": len(websocket_manager.active_connections)
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint для обработки команд обучения"""
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Получение сообщения от клиента
            data = await websocket.receive_json()
            
            # Обработка команды
            response = await process_learning_command(data)
            
            # Отправка ответа
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Ошибка WebSocket: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })

async def process_learning_command(data: Dict) -> Dict:
    """Обработка команды обучения"""
    try:
        command_type = data.get("type")
        command_data = data.get("data", {})
        
        if command_type == "learn":
            return await handle_learn_command(command_data)
        elif command_type == "adapt":
            return await handle_adapt_command(command_data)
        elif command_type == "knowledge":
            return await handle_knowledge_command(command_data)
        elif command_type == "feedback":
            return await handle_feedback_command(command_data)
        elif command_type == "optimize":
            return await handle_optimize_command(command_data)
        else:
            return {
                "type": "error",
                "message": f"Неизвестная команда: {command_type}"
            }
            
    except Exception as e:
        logger.error(f"Ошибка обработки команды: {e}")
        return {
            "type": "error",
            "message": str(e)
        }

async def handle_learn_command(data: Dict) -> Dict:
    """Обработка команды обучения"""
    try:
        learning_data = data.get("data", {})
        learning_type = data.get("learning_type", "general")
        
        # Обучение
        result = await learning_engine.learn(
            data=learning_data,
            learning_type=learning_type
        )
        
        return {
            "type": "learn_result",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Ошибка обучения: {e}")
        return {
            "type": "error",
            "message": f"Ошибка обучения: {str(e)}"
        }

async def handle_adapt_command(data: Dict) -> Dict:
    """Обработка команды адаптации"""
    try:
        context = data.get("context", {})
        adaptation_type = data.get("adaptation_type", "general")
        
        # Адаптация
        result = await adaptation_engine.adapt(
            context=context,
            adaptation_type=adaptation_type
        )
        
        return {
            "type": "adapt_result",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Ошибка адаптации: {e}")
        return {
            "type": "error",
            "message": f"Ошибка адаптации: {str(e)}"
        }

async def handle_knowledge_command(data: Dict) -> Dict:
    """Обработка команды работы с базой знаний"""
    try:
        action = data.get("action", "get")
        knowledge_data = data.get("data", {})
        
        if action == "get":
            result = await knowledge_base.get_knowledge(knowledge_data)
        elif action == "store":
            result = await knowledge_base.store_knowledge(knowledge_data)
        elif action == "search":
            result = await knowledge_base.search_knowledge(knowledge_data)
        elif action == "update":
            result = await knowledge_base.update_knowledge(knowledge_data)
        elif action == "delete":
            result = await knowledge_base.delete_knowledge(knowledge_data)
        else:
            raise ValueError(f"Неизвестное действие: {action}")
        
        return {
            "type": "knowledge_result",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Ошибка работы с базой знаний: {e}")
        return {
            "type": "error",
            "message": f"Ошибка работы с базой знаний: {str(e)}"
        }

async def handle_feedback_command(data: Dict) -> Dict:
    """Обработка команды обратной связи"""
    try:
        feedback_data = data.get("data", {})
        feedback_type = data.get("feedback_type", "general")
        
        # Обработка обратной связи
        result = await learning_engine.process_feedback(
            feedback=feedback_data,
            feedback_type=feedback_type
        )
        
        return {
            "type": "feedback_result",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Ошибка обработки обратной связи: {e}")
        return {
            "type": "error",
            "message": f"Ошибка обработки обратной связи: {str(e)}"
        }

async def handle_optimize_command(data: Dict) -> Dict:
    """Обработка команды оптимизации"""
    try:
        optimization_data = data.get("data", {})
        optimization_type = data.get("optimization_type", "general")
        
        # Оптимизация
        result = await learning_engine.optimize(
            data=optimization_data,
            optimization_type=optimization_type
        )
        
        return {
            "type": "optimize_result",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Ошибка оптимизации: {e}")
        return {
            "type": "error",
            "message": f"Ошибка оптимизации: {str(e)}"
        }

if __name__ == "__main__":
    # Запуск сервера
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8007,
        reload=False,
        log_level="info"
    )