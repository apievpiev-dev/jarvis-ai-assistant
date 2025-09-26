import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import { io } from 'socket.io-client';
import toast from 'react-hot-toast';

const WebSocketContext = createContext();

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

export const WebSocketProvider = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [lastMessage, setLastMessage] = useState(null);
  const [messageHistory, setMessageHistory] = useState([]);
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = () => {
    if (socketRef.current?.connected) {
      return;
    }

    try {
      // Подключение к API Gateway
      const socket = io(process.env.REACT_APP_API_URL || 'http://localhost:8000', {
        transports: ['websocket', 'polling'],
        timeout: 10000,
        reconnection: true,
        reconnectionAttempts: maxReconnectAttempts,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
      });

      socketRef.current = socket;

      // Обработчики событий
      socket.on('connect', () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionStatus('connected');
        reconnectAttempts.current = 0;
        toast.success('Подключение к Jarvis установлено');
      });

      socket.on('disconnect', (reason) => {
        console.log('WebSocket disconnected:', reason);
        setIsConnected(false);
        setConnectionStatus('disconnected');
        toast.error('Соединение с Jarvis потеряно');
      });

      socket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
        setConnectionStatus('error');
        toast.error('Ошибка подключения к Jarvis');
      });

      socket.on('reconnect', (attemptNumber) => {
        console.log('WebSocket reconnected after', attemptNumber, 'attempts');
        setIsConnected(true);
        setConnectionStatus('connected');
        toast.success('Соединение с Jarvis восстановлено');
      });

      socket.on('reconnect_attempt', (attemptNumber) => {
        console.log('WebSocket reconnection attempt:', attemptNumber);
        setConnectionStatus('reconnecting');
        reconnectAttempts.current = attemptNumber;
      });

      socket.on('reconnect_failed', () => {
        console.error('WebSocket reconnection failed');
        setConnectionStatus('failed');
        toast.error('Не удалось восстановить соединение с Jarvis');
      });

      // Обработка сообщений от сервисов
      socket.on('message', (data) => {
        console.log('Received message:', data);
        setLastMessage(data);
        setMessageHistory(prev => [...prev, { ...data, timestamp: Date.now() }]);
      });

      // Обработка ответов от Brain Service
      socket.on('command_result', (data) => {
        console.log('Command result:', data);
        setLastMessage(data);
        setMessageHistory(prev => [...prev, { ...data, timestamp: Date.now() }]);
      });

      // Обработка результатов от Task Service
      socket.on('task_result', (data) => {
        console.log('Task result:', data);
        setLastMessage(data);
        setMessageHistory(prev => [...prev, { ...data, timestamp: Date.now() }]);
      });

      // Обработка результатов распознавания речи
      socket.on('recognition_result', (data) => {
        console.log('Speech recognition result:', data);
        setLastMessage(data);
        setMessageHistory(prev => [...prev, { ...data, timestamp: Date.now() }]);
      });

      // Обработка результатов синтеза речи
      socket.on('synthesis_result', (data) => {
        console.log('Speech synthesis result:', data);
        setLastMessage(data);
        setMessageHistory(prev => [...prev, { ...data, timestamp: Date.now() }]);
      });

      // Обработка ошибок
      socket.on('error', (error) => {
        console.error('WebSocket error:', error);
        toast.error(`Ошибка: ${error.message || 'Неизвестная ошибка'}`);
      });

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionStatus('error');
      toast.error('Ошибка создания соединения с Jarvis');
    }
  };

  const disconnect = () => {
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }
    setIsConnected(false);
    setConnectionStatus('disconnected');
  };

  const sendMessage = (type, data) => {
    if (!socketRef.current?.connected) {
      toast.error('Нет соединения с Jarvis');
      return false;
    }

    try {
      const message = {
        type,
        data,
        timestamp: Date.now(),
        id: Math.random().toString(36).substr(2, 9)
      };

      socketRef.current.emit('message', message);
      console.log('Sent message:', message);
      return true;
    } catch (error) {
      console.error('Failed to send message:', error);
      toast.error('Ошибка отправки сообщения');
      return false;
    }
  };

  const sendCommand = (command, context = {}) => {
    return sendMessage('process_command', {
      text: command,
      context,
      user_id: 'web_user',
      session_id: 'web_session'
    });
  };

  const sendTask = (taskType, taskData) => {
    return sendMessage('execute_task', {
      type: taskType,
      data: taskData,
      user_id: 'web_user',
      session_id: 'web_session'
    });
  };

  const sendVoiceData = (audioData) => {
    return sendMessage('audio_data', {
      data: audioData
    });
  };

  const requestSynthesis = (text, voice = 'default') => {
    return sendMessage('synthesize_request', {
      text,
      voice
    });
  };

  const ping = () => {
    return sendMessage('ping', {});
  };

  const clearHistory = () => {
    setMessageHistory([]);
  };

  const getConnectionInfo = () => {
    if (!socketRef.current) {
      return null;
    }

    return {
      connected: socketRef.current.connected,
      id: socketRef.current.id,
      transport: socketRef.current.io.engine.transport.name,
      reconnectionAttempts: reconnectAttempts.current
    };
  };

  // Автоматическое подключение при монтировании
  useEffect(() => {
    connect();

    return () => {
      disconnect();
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  // Обработка изменений состояния соединения
  useEffect(() => {
    if (!isConnected && connectionStatus !== 'reconnecting') {
      const timeout = setTimeout(() => {
        if (reconnectAttempts.current < maxReconnectAttempts) {
          connect();
        }
      }, 5000);

      reconnectTimeoutRef.current = timeout;

      return () => clearTimeout(timeout);
    }
  }, [isConnected, connectionStatus]);

  const value = {
    isConnected,
    connectionStatus,
    lastMessage,
    messageHistory,
    connect,
    disconnect,
    sendMessage,
    sendCommand,
    sendTask,
    sendVoiceData,
    requestSynthesis,
    ping,
    clearHistory,
    getConnectionInfo
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};