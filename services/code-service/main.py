#!/usr/bin/env python3
"""
Code Service - Анализ и модификация кода
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
from code_analyzer import CodeAnalyzer
from code_modifier import CodeModifier
from websocket_manager import WebSocketManager

# Настройка логирования
logger = setup_logger(__name__)

# Конфигурация
config = get_config()

# Менеджер WebSocket соединений
websocket_manager = WebSocketManager()

# Инициализация компонентов
code_analyzer = CodeAnalyzer()
code_modifier = CodeModifier()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("Запуск Code Service...")
    
    # Инициализация компонентов
    await code_analyzer.initialize()
    await code_modifier.initialize()
    
    logger.info("Code Service запущен")
    
    yield
    
    logger.info("Остановка Code Service...")
    await code_analyzer.cleanup()
    await code_modifier.cleanup()
    logger.info("Code Service остановлен")

# Создание FastAPI приложения
app = FastAPI(
    title="Jarvis Code Service",
    description="Сервис анализа и модификации кода",
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
        "service": "code-service",
        "version": "1.0.0"
    }

@app.get("/status")
async def get_status():
    """Получение статуса сервиса"""
    return {
        "status": "running",
        "analyzer_ready": code_analyzer.is_ready(),
        "modifier_ready": code_modifier.is_ready(),
        "active_connections": len(websocket_manager.active_connections)
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint для обработки команд анализа кода"""
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Получение сообщения от клиента
            data = await websocket.receive_json()
            
            # Обработка команды
            response = await process_code_command(data)
            
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

async def process_code_command(data: Dict) -> Dict:
    """Обработка команды анализа кода"""
    try:
        command_type = data.get("type")
        command_data = data.get("data", {})
        
        if command_type == "analyze":
            return await handle_analyze_command(command_data)
        elif command_type == "modify":
            return await handle_modify_command(command_data)
        elif command_type == "suggest":
            return await handle_suggest_command(command_data)
        elif command_type == "refactor":
            return await handle_refactor_command(command_data)
        elif command_type == "test":
            return await handle_test_command(command_data)
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

async def handle_analyze_command(data: Dict) -> Dict:
    """Обработка команды анализа кода"""
    try:
        code = data.get("code", "")
        language = data.get("language", "python")
        analysis_type = data.get("analysis_type", "full")
        
        # Анализ кода
        result = await code_analyzer.analyze_code(
            code=code,
            language=language,
            analysis_type=analysis_type
        )
        
        return {
            "type": "analyze_result",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Ошибка анализа кода: {e}")
        return {
            "type": "error",
            "message": f"Ошибка анализа кода: {str(e)}"
        }

async def handle_modify_command(data: Dict) -> Dict:
    """Обработка команды модификации кода"""
    try:
        code = data.get("code", "")
        modifications = data.get("modifications", [])
        language = data.get("language", "python")
        
        # Модификация кода
        result = await code_modifier.modify_code(
            code=code,
            modifications=modifications,
            language=language
        )
        
        return {
            "type": "modify_result",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Ошибка модификации кода: {e}")
        return {
            "type": "error",
            "message": f"Ошибка модификации кода: {str(e)}"
        }

async def handle_suggest_command(data: Dict) -> Dict:
    """Обработка команды предложения улучшений"""
    try:
        code = data.get("code", "")
        language = data.get("language", "python")
        context = data.get("context", "")
        
        # Генерация предложений
        suggestions = await code_analyzer.suggest_improvements(
            code=code,
            language=language,
            context=context
        )
        
        return {
            "type": "suggest_result",
            "data": suggestions
        }
        
    except Exception as e:
        logger.error(f"Ошибка генерации предложений: {e}")
        return {
            "type": "error",
            "message": f"Ошибка генерации предложений: {str(e)}"
        }

async def handle_refactor_command(data: Dict) -> Dict:
    """Обработка команды рефакторинга"""
    try:
        code = data.get("code", "")
        refactor_type = data.get("refactor_type", "general")
        language = data.get("language", "python")
        
        # Рефакторинг кода
        result = await code_modifier.refactor_code(
            code=code,
            refactor_type=refactor_type,
            language=language
        )
        
        return {
            "type": "refactor_result",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Ошибка рефакторинга: {e}")
        return {
            "type": "error",
            "message": f"Ошибка рефакторинга: {str(e)}"
        }

async def handle_test_command(data: Dict) -> Dict:
    """Обработка команды тестирования кода"""
    try:
        code = data.get("code", "")
        test_type = data.get("test_type", "unit")
        language = data.get("language", "python")
        
        # Генерация тестов
        result = await code_analyzer.generate_tests(
            code=code,
            test_type=test_type,
            language=language
        )
        
        return {
            "type": "test_result",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Ошибка генерации тестов: {e}")
        return {
            "type": "error",
            "message": f"Ошибка генерации тестов: {str(e)}"
        }

if __name__ == "__main__":
    # Запуск сервера
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8006,
        reload=False,
        log_level="info"
    )