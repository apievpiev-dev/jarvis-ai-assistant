import React, { createContext, useContext, useState, useRef, useCallback } from 'react';
import { useWebSocket } from './WebSocketContext';
import toast from 'react-hot-toast';

const VoiceContext = createContext();

export const useVoice = () => {
  const context = useContext(VoiceContext);
  if (!context) {
    throw new Error('useVoice must be used within a VoiceProvider');
  }
  return context;
};

export const VoiceProvider = ({ children }) => {
  const { sendVoiceData, requestSynthesis, isConnected } = useWebSocket();
  
  // Состояние голосового интерфейса
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [recognizedText, setRecognizedText] = useState('');
  const [availableVoices, setAvailableVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState('default');
  
  // Рефы для аудио
  const mediaRecorderRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioElementRef = useRef(null);

  // Инициализация аудио контекста
  const initializeAudio = useCallback(async () => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      }
      return true;
    } catch (error) {
      console.error('Failed to initialize audio context:', error);
      toast.error('Ошибка инициализации аудио');
      return false;
    }
  }, []);

  // Получение доступа к микрофону
  const getMicrophoneAccess = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000
        } 
      });
      return stream;
    } catch (error) {
      console.error('Failed to get microphone access:', error);
      toast.error('Не удалось получить доступ к микрофону');
      return null;
    }
  }, []);

  // Настройка анализатора аудио
  const setupAudioAnalyzer = useCallback((stream) => {
    if (!audioContextRef.current) return;

    const source = audioContextRef.current.createMediaStreamSource(stream);
    analyserRef.current = audioContextRef.current.createAnalyser();
    analyserRef.current.fftSize = 256;
    analyserRef.current.smoothingTimeConstant = 0.8;
    
    source.connect(analyserRef.current);
    
    // Функция для обновления уровня аудио
    const updateAudioLevel = () => {
      if (!analyserRef.current || !isRecording) return;
      
      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      analyserRef.current.getByteFrequencyData(dataArray);
      
      const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
      setAudioLevel(average / 255);
      
      animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
    };
    
    updateAudioLevel();
  }, [isRecording]);

  // Начало записи
  const startRecording = useCallback(async () => {
    if (!isConnected) {
      toast.error('Нет соединения с Jarvis');
      return false;
    }

    try {
      // Инициализация аудио
      const audioInitialized = await initializeAudio();
      if (!audioInitialized) return false;

      // Получение доступа к микрофону
      const stream = await getMicrophoneAccess();
      if (!stream) return false;

      // Настройка MediaRecorder
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      audioChunksRef.current = [];

      // Обработчики событий MediaRecorder
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const arrayBuffer = await audioBlob.arrayBuffer();
        const base64Audio = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));
        
        // Отправка аудио данных
        const success = sendVoiceData(base64Audio);
        if (success) {
          setIsProcessing(true);
          setRecognizedText('');
        }
      };

      // Настройка анализатора аудио
      setupAudioAnalyzer(stream);

      // Начало записи
      mediaRecorderRef.current.start(100); // Запись чанками по 100мс
      setIsRecording(true);
      
      toast.success('Запись начата');
      return true;

    } catch (error) {
      console.error('Failed to start recording:', error);
      toast.error('Ошибка начала записи');
      return false;
    }
  }, [isConnected, initializeAudio, getMicrophoneAccess, setupAudioAnalyzer, sendVoiceData]);

  // Остановка записи
  const stopRecording = useCallback(() => {
    if (!mediaRecorderRef.current || !isRecording) return;

    try {
      mediaRecorderRef.current.stop();
      
      // Остановка всех треков
      if (mediaRecorderRef.current.stream) {
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      }
      
      // Остановка анимации уровня аудио
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      
      setIsRecording(false);
      setAudioLevel(0);
      
      toast.success('Запись остановлена');
      
    } catch (error) {
      console.error('Failed to stop recording:', error);
      toast.error('Ошибка остановки записи');
    }
  }, [isRecording]);

  // Воспроизведение аудио
  const playAudio = useCallback((audioData) => {
    try {
      if (audioElementRef.current) {
        audioElementRef.current.pause();
        audioElementRef.current.currentTime = 0;
      }

      const audioBlob = new Blob([Uint8Array.from(atob(audioData), c => c.charCodeAt(0))], { 
        type: 'audio/wav' 
      });
      const audioUrl = URL.createObjectURL(audioBlob);
      
      audioElementRef.current = new Audio(audioUrl);
      audioElementRef.current.onplay = () => setIsSpeaking(true);
      audioElementRef.current.onended = () => {
        setIsSpeaking(false);
        URL.revokeObjectURL(audioUrl);
      };
      audioElementRef.current.onerror = () => {
        setIsSpeaking(false);
        URL.revokeObjectURL(audioUrl);
        toast.error('Ошибка воспроизведения аудио');
      };
      
      audioElementRef.current.play();
      
    } catch (error) {
      console.error('Failed to play audio:', error);
      toast.error('Ошибка воспроизведения аудио');
    }
  }, []);

  // Синтез речи
  const synthesizeSpeech = useCallback(async (text, voice = selectedVoice) => {
    if (!isConnected) {
      toast.error('Нет соединения с Jarvis');
      return false;
    }

    if (!text.trim()) {
      toast.error('Введите текст для синтеза');
      return false;
    }

    try {
      setIsSpeaking(true);
      const success = requestSynthesis(text, voice);
      
      if (!success) {
        setIsSpeaking(false);
        return false;
      }
      
      return true;
      
    } catch (error) {
      console.error('Failed to synthesize speech:', error);
      toast.error('Ошибка синтеза речи');
      setIsSpeaking(false);
      return false;
    }
  }, [isConnected, selectedVoice, requestSynthesis]);

  // Получение доступных голосов
  const fetchAvailableVoices = useCallback(async () => {
    try {
      const response = await fetch('/api/voices');
      if (response.ok) {
        const data = await response.json();
        setAvailableVoices(data.voices || []);
      }
    } catch (error) {
      console.error('Failed to fetch voices:', error);
    }
  }, []);

  // Обработка результатов распознавания речи
  const handleRecognitionResult = useCallback((result) => {
    setIsProcessing(false);
    if (result.text) {
      setRecognizedText(result.text);
      toast.success(`Распознано: ${result.text}`);
    }
  }, []);

  // Обработка результатов синтеза речи
  const handleSynthesisResult = useCallback((result) => {
    if (result.audio_data) {
      playAudio(result.audio_data);
    }
  }, [playAudio]);

  // Очистка ресурсов
  const cleanup = useCallback(() => {
    if (isRecording) {
      stopRecording();
    }
    
    if (audioElementRef.current) {
      audioElementRef.current.pause();
      audioElementRef.current = null;
    }
    
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    setIsSpeaking(false);
    setIsProcessing(false);
    setAudioLevel(0);
  }, [isRecording, stopRecording]);

  // Очистка при размонтировании
  React.useEffect(() => {
    return cleanup;
  }, [cleanup]);

  // Загрузка доступных голосов при монтировании
  React.useEffect(() => {
    fetchAvailableVoices();
  }, [fetchAvailableVoices]);

  const value = {
    // Состояние
    isRecording,
    isProcessing,
    isSpeaking,
    audioLevel,
    recognizedText,
    availableVoices,
    selectedVoice,
    
    // Методы
    startRecording,
    stopRecording,
    synthesizeSpeech,
    playAudio,
    setSelectedVoice,
    setRecognizedText,
    handleRecognitionResult,
    handleSynthesisResult,
    cleanup
  };

  return (
    <VoiceContext.Provider value={value}>
      {children}
    </VoiceContext.Provider>
  );
};