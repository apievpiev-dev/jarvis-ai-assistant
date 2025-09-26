import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Volume2, VolumeX, X } from 'lucide-react';
import { useVoice } from '../context/VoiceContext';
import { useWebSocket } from '../context/WebSocketContext';

const VoiceInterfaceContainer = styled(motion.div)`
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 1000;
`;

const VoiceButton = styled(motion.button)`
  width: 4rem;
  height: 4rem;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  position: relative;
  overflow: hidden;

  ${props => {
    if (props.recording) {
      return `
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        animation: pulse 1s infinite;
        
        @keyframes pulse {
          0% { transform: scale(1); }
          50% { transform: scale(1.05); }
          100% { transform: scale(1); }
        }
      `;
    } else if (props.speaking) {
      return `
        background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
        color: white;
      `;
    } else {
      return `
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        
        &:hover {
          transform: scale(1.05);
          box-shadow: 0 6px 25px rgba(0, 0, 0, 0.4);
        }
      `;
    }
  }}
`;

const AudioLevelIndicator = styled(motion.div)`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.3);
  pointer-events: none;
`;

const VoicePanel = styled(motion.div)`
  position: absolute;
  bottom: 5rem;
  right: 0;
  width: 20rem;
  background: rgba(0, 0, 0, 0.9);
  backdrop-filter: blur(20px);
  border-radius: 1rem;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
`;

const PanelHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
`;

const PanelTitle = styled.h3`
  color: white;
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
`;

const CloseButton = styled(motion.button)`
  width: 2rem;
  height: 2rem;
  border: none;
  border-radius: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;

  &:hover {
    background: rgba(255, 255, 255, 0.2);
  }
`;

const StatusSection = styled.div`
  margin-bottom: 1rem;
`;

const StatusItem = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.875rem;
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

const ControlsSection = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
`;

const ControlButton = styled(motion.button)`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
  font-weight: 500;

  &:hover {
    background: rgba(255, 255, 255, 0.2);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const AudioVisualizer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  height: 2rem;
  margin: 1rem 0;
`;

const AudioBar = styled(motion.div)`
  width: 0.25rem;
  background: linear-gradient(to top, #667eea, #764ba2);
  border-radius: 0.125rem;
`;

const RecognizedText = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 0.5rem;
  padding: 0.75rem;
  margin: 1rem 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.875rem;
  line-height: 1.4;
  min-height: 2rem;
  display: flex;
  align-items: center;
`;

const VoiceInterface = () => {
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [audioBars, setAudioBars] = useState([]);
  
  const { 
    isRecording, 
    isSpeaking, 
    isProcessing, 
    audioLevel,
    recognizedText,
    startRecording, 
    stopRecording, 
    synthesizeSpeech,
    setRecognizedText
  } = useVoice();

  const { isConnected } = useWebSocket();

  // Анимация аудио визуализатора
  useEffect(() => {
    if (isRecording) {
      const interval = setInterval(() => {
        const bars = Array.from({ length: 12 }, () => Math.random() * 100);
        setAudioBars(bars);
      }, 100);
      
      return () => clearInterval(interval);
    } else {
      setAudioBars([]);
    }
  }, [isRecording]);

  const handleVoiceToggle = async () => {
    if (isRecording) {
      stopRecording();
    } else {
      await startRecording();
    }
  };

  const handleTestVoice = async () => {
    await synthesizeSpeech('Привет! Я Jarvis, ваш AI-ассистент. Как дела?');
  };

  const handleClearText = () => {
    setRecognizedText('');
  };

  const getButtonIcon = () => {
    if (isRecording) return MicOff;
    if (isSpeaking) return VolumeX;
    return Mic;
  };

  const getButtonText = () => {
    if (isRecording) return 'Остановить';
    if (isSpeaking) return 'Говорит...';
    if (isProcessing) return 'Обработка...';
    return 'Говорить';
  };

  const ButtonIcon = getButtonIcon();

  return (
    <VoiceInterfaceContainer>
      <AnimatePresence>
        {isPanelOpen && (
          <VoicePanel
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.9 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          >
            <PanelHeader>
              <PanelTitle>Голосовое управление</PanelTitle>
              <CloseButton
                onClick={() => setIsPanelOpen(false)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <X size={16} />
              </CloseButton>
            </PanelHeader>

            <StatusSection>
              <StatusItem>
                <StatusIndicator 
                  recording={isRecording}
                  speaking={isSpeaking}
                  processing={isProcessing}
                />
                <span>
                  {isRecording ? 'Запись...' : 
                   isSpeaking ? 'Воспроизведение...' : 
                   isProcessing ? 'Обработка...' : 
                   'Готов к работе'}
                </span>
              </StatusItem>
              
              <StatusItem>
                <StatusIndicator />
                <span>Соединение: {isConnected ? 'Активно' : 'Отключено'}</span>
              </StatusItem>
            </StatusSection>

            {isRecording && (
              <AudioVisualizer>
                {audioBars.map((height, index) => (
                  <AudioBar
                    key={index}
                    style={{ height: `${height}%` }}
                    animate={{ height: `${height}%` }}
                    transition={{ duration: 0.1 }}
                  />
                ))}
              </AudioVisualizer>
            )}

            {recognizedText && (
              <RecognizedText>
                <span>{recognizedText}</span>
                <motion.button
                  onClick={handleClearText}
                  style={{
                    marginLeft: 'auto',
                    background: 'none',
                    border: 'none',
                    color: 'rgba(255, 255, 255, 0.5)',
                    cursor: 'pointer',
                    padding: '0.25rem'
                  }}
                  whileHover={{ scale: 1.1 }}
                >
                  <X size={14} />
                </motion.button>
              </RecognizedText>
            )}

            <ControlsSection>
              <ControlButton
                onClick={handleVoiceToggle}
                disabled={!isConnected || isSpeaking || isProcessing}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <ButtonIcon size={16} />
                {getButtonText()}
              </ControlButton>

              <ControlButton
                onClick={handleTestVoice}
                disabled={!isConnected || isRecording || isSpeaking || isProcessing}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Volume2 size={16} />
                Тест голоса
              </ControlButton>
            </ControlsSection>
          </VoicePanel>
        )}
      </AnimatePresence>

      <VoiceButton
        recording={isRecording}
        speaking={isSpeaking}
        processing={isProcessing}
        onClick={() => setIsPanelOpen(!isPanelOpen)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        disabled={!isConnected}
      >
        <ButtonIcon size={24} />
        
        {isRecording && (
          <AudioLevelIndicator
            style={{
              width: `${100 + audioLevel * 50}%`,
              height: `${100 + audioLevel * 50}%`,
            }}
            animate={{
              scale: [1, 1.1, 1],
            }}
            transition={{
              duration: 0.5,
              repeat: Infinity,
            }}
          />
        )}
      </VoiceButton>
    </VoiceInterfaceContainer>
  );
};

export default VoiceInterface;