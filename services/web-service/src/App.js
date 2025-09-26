import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';

// Компоненты
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Chat from './pages/Chat';
import Tasks from './pages/Tasks';
import Settings from './pages/Settings';
import Dashboard from './pages/Dashboard';
import VoiceInterface from './components/VoiceInterface';

// Контекст
import { WebSocketProvider } from './context/WebSocketContext';
import { VoiceProvider } from './context/VoiceContext';

// Стили
const AppContainer = styled.div`
  display: flex;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
`;

const MainContent = styled(motion.main)`
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const ContentArea = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
`;

const LoadingScreen = styled(motion.div)`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  color: white;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
`;

const LoadingText = styled.h1`
  font-size: 2rem;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #ffffff 0%, #e0e7ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
`;

const LoadingSpinner = styled.div`
  width: 3rem;
  height: 3rem;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top: 3px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState('chat');

  useEffect(() => {
    // Имитация загрузки приложения
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

  const handlePageChange = (page) => {
    setCurrentPage(page);
    setSidebarOpen(false);
  };

  if (isLoading) {
    return (
      <LoadingScreen
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <LoadingText>Jarvis AI Assistant</LoadingText>
        <LoadingSpinner />
        <p style={{ marginTop: '1rem', opacity: 0.8 }}>
          Инициализация системы...
        </p>
      </LoadingScreen>
    );
  }

  return (
    <WebSocketProvider>
      <VoiceProvider>
        <AppContainer>
          <Sidebar 
            isOpen={sidebarOpen}
            onClose={() => setSidebarOpen(false)}
            currentPage={currentPage}
            onPageChange={handlePageChange}
          />
          
          <MainContent
            initial={{ x: 0 }}
            animate={{ x: sidebarOpen ? 250 : 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          >
            <Header 
              onMenuClick={() => setSidebarOpen(!sidebarOpen)}
              currentPage={currentPage}
            />
            
            <ContentArea>
              <AnimatePresence mode="wait">
                <Routes>
                  <Route path="/" element={<Navigate to="/chat" replace />} />
                  <Route 
                    path="/chat" 
                    element={
                      <motion.div
                        key="chat"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.3 }}
                      >
                        <Chat />
                      </motion.div>
                    } 
                  />
                  <Route 
                    path="/tasks" 
                    element={
                      <motion.div
                        key="tasks"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.3 }}
                      >
                        <Tasks />
                      </motion.div>
                    } 
                  />
                  <Route 
                    path="/dashboard" 
                    element={
                      <motion.div
                        key="dashboard"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.3 }}
                      >
                        <Dashboard />
                      </motion.div>
                    } 
                  />
                  <Route 
                    path="/settings" 
                    element={
                      <motion.div
                        key="settings"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.3 }}
                      >
                        <Settings />
                      </motion.div>
                    } 
                  />
                </Routes>
              </AnimatePresence>
            </ContentArea>
            
            <VoiceInterface />
          </MainContent>
        </AppContainer>
      </VoiceProvider>
    </WebSocketProvider>
  );
}

export default App;