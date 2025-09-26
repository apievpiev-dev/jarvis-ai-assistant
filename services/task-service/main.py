"""
Task Service для Jarvis AI Assistant
Выполнение задач и команд пользователя
"""
import asyncio
import sys
import os
from pathlib import Path

# Добавление пути к shared модулям
sys.path.append(str(Path(__file__).parent.parent.parent / "shared"))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from typing import Dict, List, Optional, Any
import logging

from utils.config import get_config
from utils.logger import get_logger, get_metrics_logger, get_performance_logger
from utils.database import DatabaseManager, CommandLogger
from task_executor import TaskExecutor
from task_scheduler import TaskScheduler
from websocket_manager import WebSocketManager

# Инициализация
config = get_config()
logger = get_logger("task-service", config.service.log_level)
metrics_logger = get_metrics_logger("task-service")
performance_logger = get_performance_logger("task-service")

# Создание FastAPI приложения
app = FastAPI(
    title="Jarvis Task Service",
    description="Сервис выполнения задач для Jarvis AI Assistant",
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
task_executor: Optional[TaskExecutor] = None
task_scheduler: Optional[TaskScheduler] = None
websocket_manager: Optional[WebSocketManager] = None

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    global db_manager, command_logger, task_executor, task_scheduler, websocket_manager
    
    try:
        # Инициализация базы данных
        db_manager = DatabaseManager(
            config.database.postgres_url,
            config.database.redis_url
        )
        await db_manager.initialize()
        command_logger = CommandLogger(db_manager)
        
        # Инициализация исполнителя задач
        task_executor = TaskExecutor(config)
        await task_executor.initialize()
        
        # Инициализация планировщика задач
        task_scheduler = TaskScheduler(task_executor, command_logger)
        await task_scheduler.initialize()
        
        # Инициализация WebSocket менеджера
        websocket_manager = WebSocketManager()
        
        logger.info("Task service initialized successfully")
        metrics_logger.increment_counter("service_startup")
        
    except Exception as e:
        logger.error(f"Failed to initialize task service: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при завершении"""
    global db_manager, task_executor, task_scheduler
    
    try:
        if task_scheduler:
            await task_scheduler.cleanup()
        
        if task_executor:
            await task_executor.cleanup()
        
        if db_manager:
            await db_manager.close()
        
        logger.info("Task service shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "task-service",
        "version": "1.0.0"
    }

@app.get("/metrics")
async def get_metrics():
    """Получение метрик сервиса"""
    return metrics_logger.get_metrics()

@app.post("/execute_task")
async def execute_task(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """Выполнение задачи"""
    if not task_executor:
        raise HTTPException(status_code=503, detail="Task executor not initialized")
    
    try:
        task_type = request.get("type", "general")
        task_data = request.get("data", {})
        user_id = request.get("user_id", "default_user")
        session_id = request.get("session_id", "default_session")
        
        # Логирование задачи
        command_id = await command_logger.log_command(
            user_id=user_id,
            session_id=session_id,
            command_text=f"Execute task: {task_type}",
            command_type="task"
        )
        
        # Создание задачи
        task_id = await command_logger.log_task(
            command_id=command_id,
            task_type=task_type,
            task_data=task_data
        )
        
        # Выполнение задачи
        async with performance_logger.time_operation(f"task_execution_{task_type}"):
            result = await task_executor.execute_task(task_type, task_data)
        
        # Обновление статуса задачи
        await command_logger.update_task_status(
            task_id,
            "completed",
            result
        )
        
        # Обновление статуса команды
        await command_logger.update_command_status(
            command_id,
            "completed",
            {
                "task_id": task_id,
                "task_type": task_type,
                "result": result
            }
        )
        
        metrics_logger.increment_counter("tasks_executed", labels={"task_type": task_type})
        
        return {
            "task_id": task_id,
            "command_id": command_id,
            "task_type": task_type,
            "result": result,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        metrics_logger.increment_counter("task_execution_errors")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/schedule_task")
async def schedule_task(request: Dict[str, Any]):
    """Планирование задачи"""
    if not task_scheduler:
        raise HTTPException(status_code=503, detail="Task scheduler not initialized")
    
    try:
        task_type = request.get("type", "general")
        task_data = request.get("data", {})
        schedule_time = request.get("schedule_time")
        cron_expression = request.get("cron_expression")
        user_id = request.get("user_id", "default_user")
        
        # Планирование задачи
        scheduled_task_id = await task_scheduler.schedule_task(
            task_type=task_type,
            task_data=task_data,
            schedule_time=schedule_time,
            cron_expression=cron_expression,
            user_id=user_id
        )
        
        metrics_logger.increment_counter("tasks_scheduled")
        
        return {
            "scheduled_task_id": scheduled_task_id,
            "task_type": task_type,
            "schedule_time": schedule_time,
            "cron_expression": cron_expression,
            "status": "scheduled"
        }
        
    except Exception as e:
        logger.error(f"Task scheduling failed: {e}")
        metrics_logger.increment_counter("task_scheduling_errors")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scheduled_tasks")
async def get_scheduled_tasks():
    """Получение списка запланированных задач"""
    if not task_scheduler:
        raise HTTPException(status_code=503, detail="Task scheduler not initialized")
    
    try:
        tasks = await task_scheduler.get_scheduled_tasks()
        return {"scheduled_tasks": tasks}
        
    except Exception as e:
        logger.error(f"Failed to get scheduled tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/scheduled_tasks/{task_id}")
async def cancel_scheduled_task(task_id: str):
    """Отмена запланированной задачи"""
    if not task_scheduler:
        raise HTTPException(status_code=503, detail="Task scheduler not initialized")
    
    try:
        success = await task_scheduler.cancel_task(task_id)
        
        if success:
            metrics_logger.increment_counter("tasks_cancelled")
            return {"status": "cancelled", "task_id": task_id}
        else:
            raise HTTPException(status_code=404, detail="Task not found")
        
    except Exception as e:
        logger.error(f"Failed to cancel scheduled task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/task_history")
async def get_task_history(limit: int = 100, offset: int = 0):
    """Получение истории выполнения задач"""
    if not command_logger:
        raise HTTPException(status_code=503, detail="Command logger not initialized")
    
    try:
        # Получение истории задач из базы данных
        query = """
        SELECT t.*, c.command_text, c.created_at as command_created_at
        FROM tasks t
        JOIN commands c ON t.command_id = c.id
        ORDER BY t.created_at DESC
        LIMIT $1 OFFSET $2
        """
        
        tasks = await db_manager.execute_query(query, limit, offset)
        
        return {
            "tasks": tasks,
            "limit": limit,
            "offset": offset,
            "total_count": len(tasks)
        }
        
    except Exception as e:
        logger.error(f"Failed to get task history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/available_tasks")
async def get_available_tasks():
    """Получение списка доступных типов задач"""
    if not task_executor:
        raise HTTPException(status_code=503, detail="Task executor not initialized")
    
    try:
        available_tasks = task_executor.get_available_tasks()
        return {"available_tasks": available_tasks}
        
    except Exception as e:
        logger.error(f"Failed to get available tasks: {e}")
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
            if message["type"] == "execute_task":
                # Выполнение задачи
                task_type = message.get("type", "general")
                task_data = message.get("data", {})
                
                try:
                    result = await task_executor.execute_task(task_type, task_data)
                    
                    await websocket_manager.send_message(websocket, {
                        "type": "task_result",
                        "task_type": task_type,
                        "result": result,
                        "status": "completed"
                    })
                    
                except Exception as e:
                    await websocket_manager.send_message(websocket, {
                        "type": "task_error",
                        "task_type": task_type,
                        "error": str(e),
                        "status": "failed"
                    })
            
            elif message["type"] == "schedule_task":
                # Планирование задачи
                task_type = message.get("type", "general")
                task_data = message.get("data", {})
                schedule_time = message.get("schedule_time")
                cron_expression = message.get("cron_expression")
                
                try:
                    scheduled_task_id = await task_scheduler.schedule_task(
                        task_type=task_type,
                        task_data=task_data,
                        schedule_time=schedule_time,
                        cron_expression=cron_expression
                    )
                    
                    await websocket_manager.send_message(websocket, {
                        "type": "task_scheduled",
                        "scheduled_task_id": scheduled_task_id,
                        "task_type": task_type,
                        "status": "scheduled"
                    })
                    
                except Exception as e:
                    await websocket_manager.send_message(websocket, {
                        "type": "scheduling_error",
                        "error": str(e),
                        "status": "failed"
                    })
            
            elif message["type"] == "get_task_status":
                # Получение статуса задачи
                task_id = message.get("task_id")
                
                try:
                    status = await task_scheduler.get_task_status(task_id)
                    
                    await websocket_manager.send_message(websocket, {
                        "type": "task_status",
                        "task_id": task_id,
                        "status": status
                    })
                    
                except Exception as e:
                    await websocket_manager.send_message(websocket, {
                        "type": "status_error",
                        "task_id": task_id,
                        "error": str(e)
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

@app.get("/system_info")
async def get_system_info():
    """Получение информации о системе"""
    if not task_executor:
        raise HTTPException(status_code=503, detail="Task executor not initialized")
    
    try:
        system_info = await task_executor.get_system_info()
        return system_info
        
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/file_operation")
async def file_operation(request: Dict[str, Any]):
    """Выполнение операции с файлами"""
    if not task_executor:
        raise HTTPException(status_code=503, detail="Task executor not initialized")
    
    try:
        operation = request.get("operation")
        file_path = request.get("file_path")
        data = request.get("data", {})
        
        if not operation or not file_path:
            raise HTTPException(status_code=400, detail="Operation and file_path are required")
        
        # Выполнение операции с файлом
        result = await task_executor.execute_file_operation(operation, file_path, data)
        
        metrics_logger.increment_counter("file_operations", labels={"operation": operation})
        
        return {
            "operation": operation,
            "file_path": file_path,
            "result": result,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"File operation failed: {e}")
        metrics_logger.increment_counter("file_operation_errors")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.service.host,
        port=config.service.port,
        log_level=config.service.log_level.lower(),
        reload=config.service.debug
    )