import React from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MessageCircle, 
  CheckSquare, 
  BarChart3, 
  Settings, 
  X,
  Home,
  Mic,
  MicOff,
  Volume2,
  VolumeX
} from 'lucide-react';
import { useVoice } from '../context/VoiceContext';

const SidebarContainer = styled(motion.aside)`
  position: fixed;
  top: 0;
  left: 0;
  width: 250px;
  height: 100vh;
  background: rgba(0, 0, 0, 0.9);
  backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 1000;
  display: flex;
  flex-direction: column;
`;

const SidebarHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
`;

const SidebarTitle = styled.h2`
  color: white;
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
`;

const CloseButton = styled(motion.button)`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border: none;
  border-radius: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: rgba(255, 255, 255, 0.2);
  }
`;

const Navigation = styled.nav`
  flex: 1;
  padding: 1rem 0;
`;

const NavItem = styled(motion.button)`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.75rem 1.5rem;
  border: none;
  background: ${props => props.active ? 'rgba(255, 255, 255, 0.1)' : 'transparent'};
  color: ${props => props.active ? 'white' : 'rgba(255, 255, 255, 0.7)'};
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
  font-size: 0.875rem;
  font-weight: 500;

  &:hover {
    background: rgba(255, 255, 255, 0.1);
    color: white;
  }
`;

const NavIcon = styled.div`
  width: 1.25rem;
  height: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const VoiceSection = styled.div`
  padding: 1rem 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
`;

const VoiceTitle = styled.h3`
  color: white;
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
  opacity: 0.8;
`;

const VoiceControls = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
`;

const VoiceButton = styled(motion.button)`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: 0.5rem;
  background: ${props => {
    if (props.recording) return 'rgba(239, 68, 68, 0.2)';
    if (props.speaking) return 'rgba(34, 197, 94, 0.2)';
    return 'rgba(255, 255, 255, 0.1)';
  }};
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
  font-weight: 500;

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

const VoiceStatus = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  border-radius: 0.5rem;
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.75rem;
`;

const StatusIndicator = styled.div`
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: ${props => {
    if (props.recording) return '#ef4444';
    if (props.speaking) return '#22c55e';
    if (props.processing) return '#fbbf24';
    return '#6b7280';
  }};
  animation: ${props => props.recording ? 'pulse 1s infinite' : 'none'};

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
`;

const Overlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
`;

const Sidebar = ({ isOpen, onClose, currentPage, onPageChange }) => {
  const { 
    isRecording, 
    isSpeaking, 
    isProcessing, 
    startRecording, 
    stopRecording, 
    synthesizeSpeech,
    recognizedText 
  } = useVoice();

  const navItems = [
    { id: 'chat', label: 'Чат', icon: MessageCircle },
    { id: 'tasks', label: 'Задачи', icon: CheckSquare },
    { id: 'dashboard', label: 'Панель', icon: BarChart3 },
    { id: 'settings', label: 'Настройки', icon: Settings },
  ];

  const handleVoiceToggle = async () => {
    if (isRecording) {
      stopRecording();
    } else {
      await startRecording();
    }
  };

  const handleTestVoice = async () => {
    await synthesizeSpeech('Привет! Я Jarvis, ваш AI-ассистент.');
  };

  const getVoiceStatus = () => {
    if (isRecording) return 'Запись...';
    if (isSpeaking) return 'Воспроизведение...';
    if (isProcessing) return 'Обработка...';
    return 'Готов к работе';
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <Overlay
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          
          <SidebarContainer
            initial={{ x: -250 }}
            animate={{ x: 0 }}
            exit={{ x: -250 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          >
            <SidebarHeader>
              <SidebarTitle>Jarvis AI</SidebarTitle>
              <CloseButton
                onClick={onClose}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <X size={18} />
              </CloseButton>
            </SidebarHeader>

            <Navigation>
              {navItems.map((item) => (
                <NavItem
                  key={item.id}
                  active={currentPage === item.id}
                  onClick={() => onPageChange(item.id)}
                  whileHover={{ x: 5 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <NavIcon>
                    <item.icon size={18} />
                  </NavIcon>
                  {item.label}
                </NavItem>
              ))}
            </Navigation>

            <VoiceSection>
              <VoiceTitle>Голосовое управление</VoiceTitle>
              
              <VoiceControls>
                <VoiceButton
                  recording={isRecording}
                  speaking={isSpeaking}
                  processing={isProcessing}
                  onClick={handleVoiceToggle}
                  disabled={isSpeaking || isProcessing}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  {isRecording ? <MicOff size={16} /> : <Mic size={16} />}
                  {isRecording ? 'Остановить запись' : 'Начать запись'}
                </VoiceButton>

                <VoiceButton
                  onClick={handleTestVoice}
                  disabled={isRecording || isSpeaking || isProcessing}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  {isSpeaking ? <VolumeX size={16} /> : <Volume2 size={16} />}
                  Тест голоса
                </VoiceButton>

                <VoiceStatus>
                  <StatusIndicator 
                    recording={isRecording}
                    speaking={isSpeaking}
                    processing={isProcessing}
                  />
                  {getVoiceStatus()}
                </VoiceStatus>

                {recognizedText && (
                  <VoiceStatus>
                    <span>Распознано: {recognizedText}</span>
                  </VoiceStatus>
                )}
              </VoiceControls>
            </VoiceSection>
          </SidebarContainer>
        </>
      )}
    </AnimatePresence>
  );
};

export default Sidebar;