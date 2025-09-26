import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { Menu, Wifi, WifiOff, Settings, Bell } from 'lucide-react';
import { useWebSocket } from '../context/WebSocketContext';

const HeaderContainer = styled(motion.header)`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  position: relative;
  z-index: 100;
`;

const LeftSection = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const MenuButton = styled(motion.button)`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border: none;
  border-radius: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: scale(1.05);
  }
`;

const Title = styled(motion.h1)`
  font-size: 1.5rem;
  font-weight: 600;
  background: linear-gradient(135deg, #ffffff 0%, #e0e7ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
`;

const RightSection = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const StatusIndicator = styled(motion.div)`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 2rem;
  background: ${props => {
    switch (props.status) {
      case 'connected': return 'rgba(34, 197, 94, 0.2)';
      case 'connecting': return 'rgba(251, 191, 36, 0.2)';
      case 'disconnected': return 'rgba(239, 68, 68, 0.2)';
      default: return 'rgba(107, 114, 128, 0.2)';
    }
  }};
  border: 1px solid ${props => {
    switch (props.status) {
      case 'connected': return 'rgba(34, 197, 94, 0.3)';
      case 'connecting': return 'rgba(251, 191, 36, 0.3)';
      case 'disconnected': return 'rgba(239, 68, 68, 0.3)';
      default: return 'rgba(107, 114, 128, 0.3)';
    }
  }};
  color: white;
  font-size: 0.875rem;
  font-weight: 500;
`;

const StatusIcon = styled(motion.div)`
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: ${props => {
    switch (props.status) {
      case 'connected': return '#22c55e';
      case 'connecting': return '#fbbf24';
      case 'disconnected': return '#ef4444';
      default: return '#6b7280';
    }
  }};
`;

const ActionButton = styled(motion.button)`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border: none;
  border-radius: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;

  &:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: scale(1.05);
  }
`;

const NotificationBadge = styled(motion.div)`
  position: absolute;
  top: -0.25rem;
  right: -0.25rem;
  width: 1rem;
  height: 1rem;
  border-radius: 50%;
  background: #ef4444;
  color: white;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
`;

const PageTitle = styled(motion.span)`
  font-size: 1rem;
  opacity: 0.8;
  margin-left: 0.5rem;
`;

const Header = ({ onMenuClick, currentPage }) => {
  const { isConnected, connectionStatus, lastMessage } = useWebSocket();
  
  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Подключено';
      case 'connecting': return 'Подключение...';
      case 'reconnecting': return 'Переподключение...';
      case 'disconnected': return 'Отключено';
      case 'error': return 'Ошибка';
      default: return 'Неизвестно';
    }
  };

  const getPageTitle = () => {
    switch (currentPage) {
      case 'chat': return 'Чат';
      case 'tasks': return 'Задачи';
      case 'dashboard': return 'Панель управления';
      case 'settings': return 'Настройки';
      default: return '';
    }
  };

  return (
    <HeaderContainer
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
    >
      <LeftSection>
        <MenuButton
          onClick={onMenuClick}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Menu size={20} />
        </MenuButton>
        
        <Title
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          Jarvis AI
        </Title>
        
        <PageTitle
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          {getPageTitle()}
        </PageTitle>
      </LeftSection>

      <RightSection>
        <StatusIndicator
          status={connectionStatus}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
        >
          <StatusIcon
            status={connectionStatus}
            animate={{
              scale: connectionStatus === 'connecting' ? [1, 1.2, 1] : 1,
            }}
            transition={{
              duration: 1,
              repeat: connectionStatus === 'connecting' ? Infinity : 0,
            }}
          />
          {getStatusText()}
        </StatusIndicator>

        <ActionButton
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Bell size={20} />
          {lastMessage && (
            <NotificationBadge
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 500, damping: 30 }}
            >
              1
            </NotificationBadge>
          )}
        </ActionButton>

        <ActionButton
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Settings size={20} />
        </ActionButton>
      </RightSection>
    </HeaderContainer>
  );
};

export default Header;