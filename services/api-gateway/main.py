"""
API Gateway для Jarvis AI Assistant
Маршрутизация запросов между микросервисами
"""
import asyncio
import sys
import os
from pathlib import Path

# Добавление пути к shared модулям
sys.path.append(str(Path(__file__).parent.parent.parent / "shared"))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import json
import time
from typing import Dict, List, Optional, Any
import logging
import httpx
from contextlib import asynccontextmanager

from utils.config import get_config
from utils.logger import get_logger, get_metrics_logger, get_performance_logger
from utils.database import DatabaseManager
from service_registry import ServiceRegistry
from load_balancer import LoadBalancer
from websocket_manager import WebSocketManager
from auth_middleware import AuthMiddleware
from rate_limiter import RateLimiter

# Инициализация
config = get_config()
logger = get_logger("api-gateway", config.service.log_level)
metrics_logger = get_metrics_logger("api-gateway")
performance_logger = get_performance_logger("api-gateway")

# Создание FastAPI приложения
app = FastAPI(
    title="Jarvis API Gateway",
    description="API Gateway для Jarvis AI Assistant",
    version="1.0.0"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.security.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Глобальные переменные
db_manager: Optional[DatabaseManager] = None
service_registry: Optional[ServiceRegistry] = None
load_balancer: Optional[LoadBalancer] = None
websocket_manager: Optional[WebSocketManager] = None
auth_middleware: Optional[AuthMiddleware] = None
rate_limiter: Optional[RateLimiter] = None

# HTTP клиент для проксирования запросов
http_client: Optional[httpx.AsyncClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global db_manager, service_registry, load_balancer, websocket_manager, auth_middleware, rate_limiter, http_client
    
    try:
        # Инициализация базы данных
        db_manager = DatabaseManager(
            config.database.postgres_url,
            config.database.redis_url
        )
        await db_manager.initialize()
        
        # Инициализация компонентов
        service_registry = ServiceRegistry()
        load_balancer = LoadBalancer(service_registry)
        websocket_manager = WebSocketManager()
        auth_middleware = AuthMiddleware(config.security)
        rate_limiter = RateLimiter(config.security.rate_limit_per_minute)
        
        # Инициализация HTTP клиента
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        
        # Регистрация сервисов
        await service_registry.register_service("voice-service", "http://voice-service:8001")
        await service_registry.register_service("brain-service", "http://brain-service:8002")
        await service_registry.register_service("task-service", "http://task-service:8003")
        await service_registry.register_service("web-service", "http://web-service:3000")
        await service_registry.register_service("code-service", "http://code-service:8004")
        await service_registry.register_service("learning-service", "http://learning-service:8005")
        
        logger.info("API Gateway initialized successfully")
        metrics_logger.increment_counter("gateway_startup")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize API Gateway: {e}")
        raise
    finally:
        # Очистка ресурсов
        if http_client:
            await http_client.aclose()
        
        if db_manager:
            await db_manager.close()
        
        logger.info("API Gateway shutdown completed")

app.router.lifespan_context = lifespan

# Middleware для аутентификации и rate limiting
@app.middleware("http")
async def auth_and_rate_limit_middleware(request: Request, call_next):
    """Middleware для аутентификации и ограничения скорости"""
    try:
        # Rate limiting
        client_ip = request.client.host
        if not await rate_limiter.is_allowed(client_ip):
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded"}
            )
        
        # Аутентификация (для защищенных эндпоинтов)
        if request.url.path.startswith("/api/protected/"):
            auth_result = await auth_middleware.authenticate_request(request)
            if not auth_result["authenticated"]:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Authentication required"}
                )
            request.state.user = auth_result["user"]
        
        # Логирование запроса
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Обновление метрик
        metrics_logger.increment_counter("http_requests", labels={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code
        })
        metrics_logger.record_histogram("request_duration", process_time)
        
        return response
        
    except Exception as e:
        logger.error(f"Middleware error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )

@app.get("/health")
async def health_check():
    """Проверка здоровья API Gateway"""
    services_status = {}
    
    if service_registry:
        for service_name in service_registry.get_registered_services():
            services_status[service_name] = await service_registry.is_service_healthy(service_name)
    
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "1.0.0",
        "services": services_status,
        "timestamp": time.time()
    }

@app.get("/metrics")
async def get_metrics():
    """Получение метрик API Gateway"""
    return metrics_logger.get_metrics()

@app.get("/services")
async def get_services():
    """Получение списка зарегистрированных сервисов"""
    if not service_registry:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    services = service_registry.get_all_services()
    return {"services": services}

# Проксирование запросов к сервисам
@app.api_route("/api/voice/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_voice_service(request: Request, path: str):
    """Проксирование запросов к Voice Service"""
    return await proxy_request("voice-service", request, path)

@app.api_route("/api/brain/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_brain_service(request: Request, path: str):
    """Проксирование запросов к Brain Service"""
    return await proxy_request("brain-service", request, path)

@app.api_route("/api/tasks/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_task_service(request: Request, path: str):
    """Проксирование запросов к Task Service"""
    return await proxy_request("task-service", request, path)

@app.api_route("/api/code/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_code_service(request: Request, path: str):
    """Проксирование запросов к Code Service"""
    return await proxy_request("code-service", request, path)

@app.api_route("/api/learning/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_learning_service(request: Request, path: str):
    """Проксирование запросов к Learning Service"""
    return await proxy_request("learning-service", request, path)

async def proxy_request(service_name: str, request: Request, path: str):
    """Проксирование HTTP запроса к сервису"""
    if not service_registry or not http_client:
        raise HTTPException(status_code=503, detail="Service registry or HTTP client not initialized")
    
    try:
        # Получение URL сервиса
        service_url = await load_balancer.get_service_url(service_name)
        if not service_url:
            raise HTTPException(status_code=503, detail=f"Service {service_name} not available")
        
        # Подготовка URL
        target_url = f"{service_url}/{path}"
        if request.query_params:
            target_url += f"?{request.query_params}"
        
        # Подготовка заголовков
        headers = dict(request.headers)
        headers.pop("host", None)  # Удаляем host заголовок
        
        # Подготовка тела запроса
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        # Выполнение запроса
        async with performance_logger.time_operation(f"proxy_request_{service_name}"):
            response = await http_client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body
            )
        
        # Возврат ответа
        return JSONResponse(
            content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except httpx.TimeoutException:
        logger.error(f"Timeout when proxying request to {service_name}")
        raise HTTPException(status_code=504, detail="Service timeout")
    except httpx.ConnectError:
        logger.error(f"Connection error when proxying request to {service_name}")
        raise HTTPException(status_code=503, detail="Service unavailable")
    except Exception as e:
        logger.error(f"Error proxying request to {service_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# WebSocket проксирование
@app.websocket("/ws/voice")
async def websocket_voice_proxy(websocket: WebSocket):
    """WebSocket проксирование к Voice Service"""
    await websocket_proxy("voice-service", websocket, "/ws")

@app.websocket("/ws/brain")
async def websocket_brain_proxy(websocket: WebSocket):
    """WebSocket проксирование к Brain Service"""
    await websocket_proxy("brain-service", websocket, "/ws")

@app.websocket("/ws/tasks")
async def websocket_tasks_proxy(websocket: WebSocket):
    """WebSocket проксирование к Task Service"""
    await websocket_proxy("task-service", websocket, "/ws")

async def websocket_proxy(service_name: str, websocket: WebSocket, path: str):
    """Проксирование WebSocket соединения к сервису"""
    if not service_registry:
        await websocket.close(code=1011, reason="Service registry not initialized")
        return
    
    try:
        # Получение URL сервиса
        service_url = await load_balancer.get_service_url(service_name)
        if not service_url:
            await websocket.close(code=1011, reason=f"Service {service_name} not available")
            return
        
        # Подключение к сервису
        target_url = service_url.replace("http://", "ws://").replace("https://", "wss://") + path
        
        async with httpx.AsyncClient() as client:
            async with client.websocket_connect(target_url) as target_websocket:
                # Принятие входящего соединения
                await websocket.accept()
                
                # Создание задач для двунаправленной передачи данных
                async def forward_to_target():
                    try:
                        while True:
                            data = await websocket.receive_text()
                            await target_websocket.send_text(data)
                    except WebSocketDisconnect:
                        pass
                
                async def forward_to_client():
                    try:
                        while True:
                            data = await target_websocket.receive_text()
                            await websocket.send_text(data)
                    except WebSocketDisconnect:
                        pass
                
                # Запуск задач
                await asyncio.gather(
                    forward_to_target(),
                    forward_to_client(),
                    return_exceptions=True
                )
                
    except Exception as e:
        logger.error(f"WebSocket proxy error for {service_name}: {e}")
        await websocket.close(code=1011, reason="Internal server error")

# Универсальный WebSocket endpoint
@app.websocket("/ws")
async def universal_websocket(websocket: WebSocket):
    """Универсальный WebSocket endpoint для всех сервисов"""
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Получение сообщения
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Маршрутизация сообщения к соответствующему сервису
            service_name = message.get("service")
            if not service_name:
                await websocket_manager.send_message(websocket, {
                    "type": "error",
                    "message": "Service name required"
                })
                continue
            
            # Получение URL сервиса
            service_url = await load_balancer.get_service_url(service_name)
            if not service_url:
                await websocket_manager.send_message(websocket, {
                    "type": "error",
                    "message": f"Service {service_name} not available"
                })
                continue
            
            # Отправка сообщения к сервису
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{service_url}/ws/message",
                        json=message,
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        await websocket_manager.send_message(websocket, result)
                    else:
                        await websocket_manager.send_message(websocket, {
                            "type": "error",
                            "message": f"Service error: {response.status_code}"
                        })
                        
            except Exception as e:
                logger.error(f"Error forwarding message to {service_name}: {e}")
                await websocket_manager.send_message(websocket, {
                    "type": "error",
                    "message": "Service communication error"
                })
                
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket_manager.disconnect(websocket)

# Аутентификация
@app.post("/api/auth/login")
async def login(request: Request):
    """Аутентификация пользователя"""
    if not auth_middleware:
        raise HTTPException(status_code=503, detail="Auth middleware not initialized")
    
    try:
        body = await request.json()
        result = await auth_middleware.authenticate_user(
            body.get("username"),
            body.get("password")
        )
        
        if result["success"]:
            return {
                "access_token": result["access_token"],
                "token_type": "bearer",
                "expires_in": config.security.jwt_expire_hours * 3600
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Authentication error")

@app.post("/api/auth/refresh")
async def refresh_token(request: Request):
    """Обновление токена"""
    if not auth_middleware:
        raise HTTPException(status_code=503, detail="Auth middleware not initialized")
    
    try:
        body = await request.json()
        result = await auth_middleware.refresh_token(body.get("refresh_token"))
        
        if result["success"]:
            return {
                "access_token": result["access_token"],
                "token_type": "bearer",
                "expires_in": config.security.jwt_expire_hours * 3600
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
            
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh error")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.service.host,
        port=config.service.port,
        log_level=config.service.log_level.lower(),
        reload=config.service.debug
    )