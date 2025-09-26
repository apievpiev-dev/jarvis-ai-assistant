"""
Brain Service для Jarvis AI Assistant
AI обработка команд с помощью Phi-2 и других моделей
"""
import asyncio
import sys
import os
from pathlib import Path

# Добавление пути к shared модулям
sys.path.append(str(Path(__file__).parent.parent.parent / "shared"))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from typing import Dict, List, Optional, Any
import logging

from utils.config import get_config
from utils.logger import get_logger, get_metrics_logger, get_performance_logger
from utils.database import DatabaseManager, CommandLogger, LearningDataManager
from brain_processor import BrainProcessor
from command_analyzer import CommandAnalyzer
from websocket_manager import WebSocketManager

# Инициализация
config = get_config()
logger = get_logger("brain-service", config.service.log_level)
metrics_logger = get_metrics_logger("brain-service")
performance_logger = get_performance_logger("brain-service")

# Создание FastAPI приложения
app = FastAPI(
    title="Jarvis Brain Service",
    description="AI обработка команд для Jarvis AI Assistant",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.security.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальные переменные
db_manager: Optional[DatabaseManager] = None
command_logger: Optional[CommandLogger] = None
learning_manager: Optional[LearningDataManager] = None
brain_processor: Optional[BrainProcessor] = None
command_analyzer: Optional[CommandAnalyzer] = None
websocket_manager: Optional[WebSocketManager] = None

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    global db_manager, command_logger, learning_manager, brain_processor, command_analyzer, websocket_manager
    
    try:
        # Инициализация базы данных
        db_manager = DatabaseManager(
            config.database.postgres_url,
            config.database.redis_url
        )
        await db_manager.initialize()
        command_logger = CommandLogger(db_manager)
        learning_manager = LearningDataManager(db_manager)
        
        # Инициализация AI процессора
        brain_processor = BrainProcessor(config.model)
        await brain_processor.initialize()
        
        # Инициализация анализатора команд
        command_analyzer = CommandAnalyzer(brain_processor, learning_manager)
        
        # Инициализация WebSocket менеджера
        websocket_manager = WebSocketManager()
        
        logger.info("Brain service initialized successfully")
        metrics_logger.increment_counter("service_startup")
        
    except Exception as e:
        logger.error(f"Failed to initialize brain service: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при завершении"""
    global db_manager, brain_processor
    
    try:
        if brain_processor:
            await brain_processor.cleanup()
        
        if db_manager:
            await db_manager.close()
        
        logger.info("Brain service shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "brain-service",
        "version": "1.0.0"
    }

@app.get("/metrics")
async def get_metrics():
    """Получение метрик сервиса"""
    return metrics_logger.get_metrics()

@app.post("/process_command")
async def process_command(request: Dict[str, Any]):
    """Обработка команды пользователя"""
    if not brain_processor or not command_analyzer:
        raise HTTPException(status_code=503, detail="Brain processor not initialized")
    
    try:
        command_text = request.get("text", "")
        user_id = request.get("user_id", "default_user")
        session_id = request.get("session_id", "default_session")
        context = request.get("context", {})
        
        if not command_text:
            raise HTTPException(status_code=400, detail="Command text is required")
        
        # Логирование команды
        command_id = await command_logger.log_command(
            user_id=user_id,
            session_id=session_id,
            command_text=command_text,
            command_type="text"
        )
        
        # Анализ команды
        async with performance_logger.time_operation("command_analysis"):
            analysis_result = await command_analyzer.analyze_command(command_text, context)
        
        # Обработка команды
        async with performance_logger.time_operation("command_processing"):
            processing_result = await brain_processor.process_command(
                command_text, 
                analysis_result, 
                context
            )
        
        # Сохранение данных обучения
        await learning_manager.store_interaction(
            interaction_type="command",
            input_data={
                "command": command_text,
                "context": context,
                "analysis": analysis_result
            },
            output_data=processing_result
        )
        
        # Обновление статуса команды
        await command_logger.update_command_status(
            command_id,
            "completed",
            {
                "analysis": analysis_result,
                "processing": processing_result,
                "processing_time": processing_result.get("processing_time", 0)
            }
        )
        
        metrics_logger.increment_counter("commands_processed")
        
        return {
            "command_id": command_id,
            "analysis": analysis_result,
            "response": processing_result,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Command processing failed: {e}")
        metrics_logger.increment_counter("command_processing_errors")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_intent")
async def analyze_intent(request: Dict[str, Any]):
    """Анализ намерения пользователя"""
    if not command_analyzer:
        raise HTTPException(status_code=503, detail="Command analyzer not initialized")
    
    try:
        text = request.get("text", "")
        context = request.get("context", {})
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        # Анализ намерения
        intent_result = await command_analyzer.analyze_intent(text, context)
        
        metrics_logger.increment_counter("intent_analysis_requests")
        
        return intent_result
        
    except Exception as e:
        logger.error(f"Intent analysis failed: {e}")
        metrics_logger.increment_counter("intent_analysis_errors")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_response")
async def generate_response(request: Dict[str, Any]):
    """Генерация ответа на основе контекста"""
    if not brain_processor:
        raise HTTPException(status_code=503, detail="Brain processor not initialized")
    
    try:
        prompt = request.get("prompt", "")
        context = request.get("context", {})
        max_tokens = request.get("max_tokens", config.model.max_tokens)
        temperature = request.get("temperature", config.model.temperature)
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Генерация ответа
        async with performance_logger.time_operation("response_generation"):
            response = await brain_processor.generate_response(
                prompt, 
                context, 
                max_tokens=max_tokens,
                temperature=temperature
            )
        
        metrics_logger.increment_counter("response_generation_requests")
        
        return {
            "response": response["text"],
            "tokens_used": response.get("tokens_used", 0),
            "generation_time": response.get("generation_time", 0)
        }
        
    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        metrics_logger.increment_counter("response_generation_errors")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/learn_from_feedback")
async def learn_from_feedback(request: Dict[str, Any]):
    """Обучение на основе обратной связи"""
    if not learning_manager:
        raise HTTPException(status_code=503, detail="Learning manager not initialized")
    
    try:
        interaction_id = request.get("interaction_id")
        feedback_score = request.get("feedback_score", 3)
        feedback_text = request.get("feedback_text", "")
        
        if not interaction_id:
            raise HTTPException(status_code=400, detail="Interaction ID is required")
        
        # Сохранение обратной связи
        await learning_manager.store_interaction(
            interaction_type="feedback",
            input_data={
                "interaction_id": interaction_id,
                "feedback_text": feedback_text
            },
            output_data={"feedback_score": feedback_score},
            feedback_score=feedback_score
        )
        
        metrics_logger.increment_counter("feedback_received")
        
        return {
            "status": "feedback_recorded",
            "interaction_id": interaction_id,
            "feedback_score": feedback_score
        }
        
    except Exception as e:
        logger.error(f"Feedback learning failed: {e}")
        metrics_logger.increment_counter("feedback_learning_errors")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint для реального времени"""
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Получение сообщения
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Обработка различных типов сообщений
            if message["type"] == "process_command":
                # Обработка команды
                command_text = message.get("text", "")
                context = message.get("context", {})
                
                if command_text:
                    # Анализ команды
                    analysis = await command_analyzer.analyze_command(command_text, context)
                    
                    # Обработка команды
                    result = await brain_processor.process_command(command_text, analysis, context)
                    
                    # Отправка результата
                    await websocket_manager.send_message(websocket, {
                        "type": "command_result",
                        "analysis": analysis,
                        "response": result
                    })
            
            elif message["type"] == "generate_response":
                # Генерация ответа
                prompt = message.get("prompt", "")
                context = message.get("context", {})
                
                if prompt:
                    response = await brain_processor.generate_response(prompt, context)
                    
                    await websocket_manager.send_message(websocket, {
                        "type": "response_generated",
                        "response": response
                    })
            
            elif message["type"] == "ping":
                # Ответ на ping
                await websocket_manager.send_message(websocket, {
                    "type": "pong"
                })
                
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket_manager.disconnect(websocket)

@app.get("/memory")
async def get_memory(memory_type: Optional[str] = None, limit: int = 100):
    """Получение памяти агента"""
    if not learning_manager:
        raise HTTPException(status_code=503, detail="Learning manager not initialized")
    
    try:
        memory_data = await learning_manager.get_memory(memory_type)
        
        return {
            "memory": memory_data[:limit],
            "total_count": len(memory_data)
        }
        
    except Exception as e:
        logger.error(f"Failed to get memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/store_memory")
async def store_memory(request: Dict[str, Any]):
    """Сохранение в память агента"""
    if not learning_manager:
        raise HTTPException(status_code=503, detail="Learning manager not initialized")
    
    try:
        memory_type = request.get("type", "fact")
        content = request.get("content", "")
        importance = request.get("importance", 0.5)
        expires_at = request.get("expires_at")
        
        if not content:
            raise HTTPException(status_code=400, detail="Content is required")
        
        await learning_manager.store_memory(memory_type, content, importance, expires_at)
        
        return {
            "status": "memory_stored",
            "type": memory_type,
            "content": content
        }
        
    except Exception as e:
        logger.error(f"Failed to store memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/model_info")
async def get_model_info():
    """Получение информации о моделях"""
    if not brain_processor:
        raise HTTPException(status_code=503, detail="Brain processor not initialized")
    
    try:
        model_info = brain_processor.get_model_info()
        return model_info
        
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.service.host,
        port=config.service.port,
        log_level=config.service.log_level.lower(),
        reload=config.service.debug
    )