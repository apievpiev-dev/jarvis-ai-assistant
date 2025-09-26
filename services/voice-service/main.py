"""
Voice Service для Jarvis AI Assistant
Обработка речи: распознавание (Whisper) и синтез (TTS)
"""
import asyncio
import sys
import os
from pathlib import Path

# Добавление пути к shared модулям
sys.path.append(str(Path(__file__).parent.parent.parent / "shared"))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import json
import io
import base64
from typing import Dict, List, Optional
import logging

from utils.config import get_config
from utils.logger import get_logger, get_metrics_logger, get_performance_logger
from utils.database import DatabaseManager, CommandLogger
from voice_processor import VoiceProcessor
from websocket_manager import WebSocketManager

# Инициализация
config = get_config()
logger = get_logger("voice-service", config.service.log_level)
metrics_logger = get_metrics_logger("voice-service")
performance_logger = get_performance_logger("voice-service")

# Создание FastAPI приложения
app = FastAPI(
    title="Jarvis Voice Service",
    description="Сервис обработки речи для Jarvis AI Assistant",
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
voice_processor: Optional[VoiceProcessor] = None
websocket_manager: Optional[WebSocketManager] = None

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    global db_manager, command_logger, voice_processor, websocket_manager
    
    try:
        # Инициализация базы данных
        db_manager = DatabaseManager(
            config.database.postgres_url,
            config.database.redis_url
        )
        await db_manager.initialize()
        command_logger = CommandLogger(db_manager)
        
        # Инициализация обработчика речи
        voice_processor = VoiceProcessor(config.model)
        await voice_processor.initialize()
        
        # Инициализация WebSocket менеджера
        websocket_manager = WebSocketManager()
        
        logger.info("Voice service initialized successfully")
        metrics_logger.increment_counter("service_startup")
        
    except Exception as e:
        logger.error(f"Failed to initialize voice service: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при завершении"""
    global db_manager, voice_processor
    
    try:
        if voice_processor:
            await voice_processor.cleanup()
        
        if db_manager:
            await db_manager.close()
        
        logger.info("Voice service shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "voice-service",
        "version": "1.0.0"
    }

@app.get("/metrics")
async def get_metrics():
    """Получение метрик сервиса"""
    return metrics_logger.get_metrics()

@app.post("/recognize")
async def recognize_speech(audio_file: UploadFile = File(...)):
    """Распознавание речи из аудио файла"""
    if not voice_processor:
        raise HTTPException(status_code=503, detail="Voice processor not initialized")
    
    try:
        # Чтение аудио файла
        audio_data = await audio_file.read()
        
        # Распознавание речи
        async with performance_logger.time_operation("speech_recognition"):
            result = await voice_processor.recognize_speech(audio_data)
        
        metrics_logger.increment_counter("speech_recognition_requests")
        
        return {
            "text": result["text"],
            "confidence": result["confidence"],
            "language": result["language"],
            "duration": result["duration"]
        }
        
    except Exception as e:
        logger.error(f"Speech recognition failed: {e}")
        metrics_logger.increment_counter("speech_recognition_errors")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/synthesize")
async def synthesize_speech(text: str, voice: str = "default"):
    """Синтез речи из текста"""
    if not voice_processor:
        raise HTTPException(status_code=503, detail="Voice processor not initialized")
    
    try:
        # Синтез речи
        async with performance_logger.time_operation("speech_synthesis"):
            audio_data = await voice_processor.synthesize_speech(text, voice)
        
        metrics_logger.increment_counter("speech_synthesis_requests")
        
        # Возврат аудио потока
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=speech.wav"}
        )
        
    except Exception as e:
        logger.error(f"Speech synthesis failed: {e}")
        metrics_logger.increment_counter("speech_synthesis_errors")
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
            if message["type"] == "audio_data":
                # Обработка аудио данных
                audio_data = base64.b64decode(message["data"])
                
                # Распознавание речи
                result = await voice_processor.recognize_speech(audio_data)
                
                # Отправка результата
                await websocket_manager.send_message(websocket, {
                    "type": "recognition_result",
                    "text": result["text"],
                    "confidence": result["confidence"]
                })
                
            elif message["type"] == "synthesize_request":
                # Синтез речи
                text = message["text"]
                voice = message.get("voice", "default")
                
                audio_data = await voice_processor.synthesize_speech(text, voice)
                audio_b64 = base64.b64encode(audio_data).decode()
                
                # Отправка аудио
                await websocket_manager.send_message(websocket, {
                    "type": "synthesis_result",
                    "audio_data": audio_b64
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

@app.get("/voices")
async def get_available_voices():
    """Получение списка доступных голосов"""
    if not voice_processor:
        raise HTTPException(status_code=503, detail="Voice processor not initialized")
    
    try:
        voices = await voice_processor.get_available_voices()
        return {"voices": voices}
        
    except Exception as e:
        logger.error(f"Failed to get voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process_command")
async def process_voice_command(audio_file: UploadFile = File(...)):
    """Обработка голосовой команды"""
    if not voice_processor or not command_logger:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    try:
        # Чтение аудио
        audio_data = await audio_file.read()
        
        # Распознавание речи
        recognition_result = await voice_processor.recognize_speech(audio_data)
        
        # Логирование команды
        command_id = await command_logger.log_command(
            user_id="default_user",
            session_id="default_session",
            command_text=recognition_result["text"],
            command_type="voice"
        )
        
        # Обновление статуса
        await command_logger.update_command_status(
            command_id,
            "completed",
            {
                "recognition_result": recognition_result,
                "processing_time": recognition_result.get("duration", 0)
            }
        )
        
        metrics_logger.increment_counter("voice_commands_processed")
        
        return {
            "command_id": command_id,
            "recognized_text": recognition_result["text"],
            "confidence": recognition_result["confidence"],
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Voice command processing failed: {e}")
        metrics_logger.increment_counter("voice_commands_errors")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.service.host,
        port=config.service.port,
        log_level=config.service.log_level.lower(),
        reload=config.service.debug
    )