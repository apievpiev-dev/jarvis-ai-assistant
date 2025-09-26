#!/usr/bin/env python3
"""
Simple API Service - Упрощенный API сервис
Автор: Jarvis AI Assistant
Версия: 1.0.0
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional
from datetime import datetime

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Модели данных
class Message(BaseModel):
    text: str
    user_id: Optional[str] = "anonymous"
    timestamp: Optional[datetime] = None

class Response(BaseModel):
    message: str
    status: str = "success"
    data: Optional[Dict] = None

# Создание FastAPI приложения
app = FastAPI(
    title="Jarvis Simple API",
    description="Упрощенный API сервис для Jarvis AI Assistant",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилище сообщений
messages = []
active_connections = []

@app.get("/")
async def root():
    """Главная страница"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Jarvis AI Assistant</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f0f0f0; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; color: #333; margin-bottom: 30px; }
            .chat { border: 1px solid #ddd; height: 400px; overflow-y: auto; padding: 10px; margin-bottom: 20px; background: #fafafa; }
            .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
            .user { background: #007bff; color: white; text-align: right; }
            .jarvis { background: #28a745; color: white; }
            .input-area { display: flex; gap: 10px; }
            input[type="text"] { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .status { text-align: center; color: #666; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Jarvis AI Assistant</h1>
                <p>Ваш умный помощник готов к работе!</p>
            </div>
            
            <div id="chat" class="chat"></div>
            
            <div class="input-area">
                <input type="text" id="messageInput" placeholder="Введите ваше сообщение..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()">Отправить</button>
            </div>
            
            <div class="status">
                <p>Статус: <span id="status">Подключение...</span></p>
            </div>
        </div>

        <script>
            let ws;
            let isConnected = false;

            function connect() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
                
                ws.onopen = function(event) {
                    isConnected = true;
                    document.getElementById('status').textContent = 'Подключено';
                    addMessage('Jarvis', 'Привет! Я готов помочь вам. Чем могу быть полезен?', 'jarvis');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    addMessage('Jarvis', data.message, 'jarvis');
                };
                
                ws.onclose = function(event) {
                    isConnected = false;
                    document.getElementById('status').textContent = 'Отключено';
                    setTimeout(connect, 3000);
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                    document.getElementById('status').textContent = 'Ошибка подключения';
                };
            }

            function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                
                if (message && isConnected) {
                    addMessage('Вы', message, 'user');
                    ws.send(JSON.stringify({text: message, user_id: 'user'}));
                    input.value = '';
                }
            }

            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }

            function addMessage(sender, text, type) {
                const chat = document.getElementById('chat');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}`;
                messageDiv.innerHTML = `<strong>${sender}:</strong> ${text}`;
                chat.appendChild(messageDiv);
                chat.scrollTop = chat.scrollHeight;
            }

            // Подключение при загрузке страницы
            connect();
        </script>
    </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "simple-api",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/status")
async def get_status():
    """Получение статуса сервиса"""
    return {
        "status": "running",
        "active_connections": len(active_connections),
        "total_messages": len(messages),
        "uptime": "running"
    }

@app.get("/messages")
async def get_messages():
    """Получение всех сообщений"""
    return {"messages": messages}

@app.post("/message", response_model=Response)
async def send_message(message: Message):
    """Отправка сообщения"""
    try:
        if not message.timestamp:
            message.timestamp = datetime.now()
        
        # Сохранение сообщения
        messages.append(message.dict())
        
        # Простая обработка сообщения
        response_text = await process_message(message.text)
        
        # Отправка ответа всем подключенным клиентам
        response_data = {
            "message": response_text,
            "timestamp": datetime.now().isoformat()
        }
        
        for connection in active_connections:
            try:
                await connection.send_json(response_data)
            except:
                active_connections.remove(connection)
        
        return Response(
            message="Сообщение отправлено",
            data={"response": response_text}
        )
        
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_message(text: str) -> str:
    """Простая обработка сообщения"""
    text_lower = text.lower()
    
    # Простые ответы на русском языке
    if any(word in text_lower for word in ["привет", "здравствуй", "добрый день"]):
        return "Привет! Рад вас видеть! Как дела?"
    
    elif any(word in text_lower for word in ["как дела", "как ты", "что нового"]):
        return "У меня всё отлично! Готов помочь вам с любыми задачами. Что вас интересует?"
    
    elif any(word in text_lower for word in ["время", "который час"]):
        current_time = datetime.now().strftime("%H:%M")
        return f"Сейчас {current_time}. Время летит незаметно!"
    
    elif any(word in text_lower for word in ["погода", "дождь", "солнце"]):
        return "К сожалению, я не могу проверить погоду в реальном времени, но рекомендую посмотреть в окно! 😊"
    
    elif any(word in text_lower for word in ["помощь", "help", "что ты умеешь"]):
        return """Я умею:
        • Отвечать на вопросы
        • Поддерживать беседу
        • Помогать с различными задачами
        • Работать в режиме реального времени
        
        Просто напишите мне, и я постараюсь помочь!"""
    
    elif any(word in text_lower for word in ["спасибо", "благодарю"]):
        return "Пожалуйста! Всегда рад помочь! 😊"
    
    elif any(word in text_lower for word in ["пока", "до свидания", "увидимся"]):
        return "До свидания! Было приятно пообщаться. Возвращайтесь скорее!"
    
    else:
        return f"Интересно! Вы написали: '{text}'. Расскажите больше об этом, я внимательно слушаю!"

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint для реального времени"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Получение сообщения от клиента
            data = await websocket.receive_json()
            
            # Обработка сообщения
            response_text = await process_message(data.get("text", ""))
            
            # Отправка ответа
            await websocket.send_json({
                "message": response_text,
                "timestamp": datetime.now().isoformat()
            })
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        logger.error(f"Ошибка WebSocket: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

if __name__ == "__main__":
    logger.info("Запуск Simple API Service...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )