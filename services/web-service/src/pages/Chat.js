import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Mic, MicOff, Volume2, VolumeX, Bot, User } from 'lucide-react';
import { useWebSocket } from '../context/WebSocketContext';
import { useVoice } from '../context/VoiceContext';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import toast from 'react-hot-toast';

const ChatContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
  max-width: 800px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 1rem;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  overflow: hidden;
`;

const ChatHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background: rgba(255, 255, 255, 0.1);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
`;

const ChatTitle = styled.h2`
  color: white;
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
`;

const VoiceControls = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const VoiceButton = styled(motion.button)`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border: none;
  border-radius: 50%;
  background: ${props => {
    if (props.recording) return 'rgba(239, 68, 68, 0.2)';
    if (props.speaking) return 'rgba(34, 197, 94, 0.2)';
    return 'rgba(255, 255, 255, 0.1)';
  }};
  color: white;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: ${props => {
      if (props.recording) return 'rgba(239, 68, 68, 0.3)';
      if (props.speaking) return 'rgba(34, 197, 94, 0.3)';
      return 'rgba(255, 255, 255, 0.2)';
    }};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const MessagesContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const Message = styled(motion.div)`
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  ${props => props.isUser && 'flex-direction: row-reverse;'}
`;

const MessageAvatar = styled.div`
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: ${props => props.isUser ? 
    'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)' : 
    'linear-gradient(135deg, #764ba2 0%, #667eea 100%)'
  };
  color: white;
  font-weight: bold;
  flex-shrink: 0;
`;

const MessageBubble = styled(motion.div)`
  max-width: 70%;
  padding: 0.75rem 1rem;
  border-radius: 1rem;
  background: ${props => props.isUser ? 
    'rgba(37, 99, 235, 0.2)' : 
    'rgba(255, 255, 255, 0.1)'
  };
  color: white;
  word-wrap: break-word;
  border: 1px solid ${props => props.isUser ? 
    'rgba(37, 99, 235, 0.3)' : 
    'rgba(255, 255, 255, 0.1)'
  };
  backdrop-filter: blur(10px);
`;

const MessageContent = styled.div`
  line-height: 1.5;
  
  p {
    margin: 0 0 0.5rem 0;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  pre {
    background: rgba(0, 0, 0, 0.3);
    border-radius: 0.5rem;
    padding: 1rem;
    overflow-x: auto;
    margin: 0.5rem 0;
  }
  
  code {
    background: rgba(0, 0, 0, 0.3);
    padding: 0.125rem 0.25rem;
    border-radius: 0.25rem;
    font-family: 'Courier New', monospace;
    font-size: 0.875rem;
  }
  
  ul, ol {
    margin: 0.5rem 0;
    padding-left: 1.5rem;
  }
  
  li {
    margin: 0.25rem 0;
  }
`;

const MessageTime = styled.div`
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 0.25rem;
  text-align: ${props => props.isUser ? 'right' : 'left'};
`;

const InputContainer = styled.div`
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  background: rgba(255, 255, 255, 0.05);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
`;

const InputWrapper = styled.div`
  flex: 1;
  position: relative;
`;

const MessageInput = styled.textarea`
  width: 100%;
  min-height: 2.5rem;
  max-height: 8rem;
  padding: 0.75rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 0.875rem;
  resize: none;
  outline: none;
  backdrop-filter: blur(10px);
  transition: all 0.2s;

  &::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }

  &:focus {
    border-color: rgba(37, 99, 235, 0.5);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
  }
`;

const SendButton = styled(motion.button)`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border: none;
  border-radius: 50%;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: white;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const TypingIndicator = styled(motion.div)`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.875rem;
  font-style: italic;
`;

const TypingDots = styled.div`
  display: flex;
  gap: 0.25rem;
`;

const TypingDot = styled(motion.div)`
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.5);
`;

const Chat = () => {
  const [messages, setMessages] = useState([
    {
      id: '1',
      text: 'Привет! Я Jarvis, ваш AI-ассистент. Чем могу помочь?',
      isUser: false,
      timestamp: new Date(),
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const { sendCommand, isConnected, lastMessage } = useWebSocket();
  const { 
    isRecording, 
    isSpeaking, 
    startRecording, 
    stopRecording, 
    recognizedText,
    setRecognizedText 
  } = useVoice();

  // Автопрокрутка к последнему сообщению
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Обработка входящих сообщений
  useEffect(() => {
    if (lastMessage) {
      if (lastMessage.type === 'command_result') {
        setIsTyping(false);
        const newMessage = {
          id: Date.now().toString(),
          text: lastMessage.response?.response || 'Команда выполнена',
          isUser: false,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, newMessage]);
      } else if (lastMessage.type === 'recognition_result') {
        setRecognizedText(lastMessage.text);
        setInputText(lastMessage.text);
      }
    }
  }, [lastMessage, setRecognizedText]);

  // Обработка распознанного текста
  useEffect(() => {
    if (recognizedText) {
      setInputText(recognizedText);
      inputRef.current?.focus();
    }
  }, [recognizedText]);

  const handleSendMessage = async () => {
    if (!inputText.trim() || !isConnected) return;

    const userMessage = {
      id: Date.now().toString(),
      text: inputText,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsTyping(true);

    // Отправка команды
    const success = sendCommand(inputText);
    if (!success) {
      setIsTyping(false);
      toast.error('Ошибка отправки сообщения');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleVoiceToggle = async () => {
    if (isRecording) {
      stopRecording();
    } else {
      await startRecording();
    }
  };

  const handleTestVoice = async () => {
    // Тест синтеза речи
    toast.success('Тест голоса запущен');
  };

  return (
    <ChatContainer>
      <ChatHeader>
        <ChatTitle>Чат с Jarvis</ChatTitle>
        <VoiceControls>
          <VoiceButton
            recording={isRecording}
            speaking={isSpeaking}
            onClick={handleVoiceToggle}
            disabled={!isConnected || isSpeaking}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            {isRecording ? <MicOff size={16} /> : <Mic size={16} />}
          </VoiceButton>
          
          <VoiceButton
            onClick={handleTestVoice}
            disabled={!isConnected || isRecording}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            {isSpeaking ? <VolumeX size={16} /> : <Volume2 size={16} />}
          </VoiceButton>
        </VoiceControls>
      </ChatHeader>

      <MessagesContainer>
        <AnimatePresence>
          {messages.map((message) => (
            <Message
              key={message.id}
              isUser={message.isUser}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <MessageAvatar isUser={message.isUser}>
                {message.isUser ? <User size={16} /> : <Bot size={16} />}
              </MessageAvatar>
              
              <MessageBubble isUser={message.isUser}>
                <MessageContent>
                  <ReactMarkdown
                    components={{
                      code({ node, inline, className, children, ...props }) {
                        const match = /language-(\w+)/.exec(className || '');
                        return !inline && match ? (
                          <SyntaxHighlighter
                            style={tomorrow}
                            language={match[1]}
                            PreTag="div"
                            {...props}
                          >
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        ) : (
                          <code className={className} {...props}>
                            {children}
                          </code>
                        );
                      },
                    }}
                  >
                    {message.text}
                  </ReactMarkdown>
                </MessageContent>
                
                <MessageTime isUser={message.isUser}>
                  {message.timestamp.toLocaleTimeString()}
                </MessageTime>
              </MessageBubble>
            </Message>
          ))}
        </AnimatePresence>

        {isTyping && (
          <TypingIndicator
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <Bot size={16} />
            Jarvis печатает
            <TypingDots>
              <TypingDot
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1, repeat: Infinity, delay: 0 }}
              />
              <TypingDot
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
              />
              <TypingDot
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
              />
            </TypingDots>
          </TypingIndicator>
        )}

        <div ref={messagesEndRef} />
      </MessagesContainer>

      <InputContainer>
        <InputWrapper>
          <MessageInput
            ref={inputRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isConnected ? "Введите сообщение..." : "Нет соединения с Jarvis"}
            disabled={!isConnected}
            rows={1}
          />
        </InputWrapper>
        
        <SendButton
          onClick={handleSendMessage}
          disabled={!inputText.trim() || !isConnected}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Send size={16} />
        </SendButton>
      </InputContainer>
    </ChatContainer>
  );
};

export default Chat;