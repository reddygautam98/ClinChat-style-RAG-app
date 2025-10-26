import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  TextField,
  Card,
  CardContent,
  Chip,
  Alert,
  CircularProgress,
  Divider,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Send as SendIcon,
  MedicalServices as MedicalIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckIcon,
  Psychology as AIIcon,
} from '@mui/icons-material';
import { useMutation } from 'react-query';
import axios from 'axios';

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    responseTime?: number;
    model?: string;
    confidence?: number;
    securityCheck?: string;
  };
}

interface SecurityValidation {
  isValid: boolean;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  violations: string[];
  redactedQuery?: string;
}

const HealthAI: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      type: 'system',
      content: 'Welcome to HealthAI - Your HIPAA-compliant medical information assistant. I can help you with medical questions while maintaining the highest privacy and security standards.',
      timestamp: new Date(),
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when new messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initialize session
  useEffect(() => {
    const initSession = async () => {
      try {
        const response = await axios.post('/api/session/start', {
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString()
        });
        setSessionId(response.data.sessionId);
      } catch (error) {
        console.error('Failed to initialize session:', error);
      }
    };
    initSession();
  }, []);

  // Validate query security
  const validateQuery = async (query: string): Promise<SecurityValidation> => {
    try {
      const response = await axios.post('/api/validate', {
        query,
        sessionId
      });
      return response.data;
    } catch (error) {
      console.error('Query validation failed:', error);
      return {
        isValid: false,
        riskLevel: 'HIGH',
        violations: ['Security validation unavailable']
      };
    }
  };

  // Send chat message
  const sendMessage = useMutation(
    async (query: string) => {
      // First validate the query
      const validation = await validateQuery(query);
      
      if (!validation.isValid) {
        throw new Error(`Security violation: ${validation.violations.join(', ')}`);
      }

      // Send to chat API
      const response = await axios.post('/api/chat', {
        query: validation.redactedQuery || query,
        sessionId,
        metadata: {
          originalQuery: query,
          securityValidation: validation
        }
      });

      return {
        ...response.data,
        securityValidation: validation
      };
    },
    {
      onSuccess: (data) => {
        // Add user message
        const userMessage: ChatMessage = {
          id: `user-${Date.now()}`,
          type: 'user',
          content: inputQuery,
          timestamp: new Date(),
        };

        // Add AI response
        const aiMessage: ChatMessage = {
          id: `ai-${Date.now()}`,
          type: 'assistant',
          content: data.response,
          timestamp: new Date(),
          metadata: {
            responseTime: data.responseTime,
            model: data.model,
            confidence: data.confidence,
            securityCheck: data.securityValidation.riskLevel
          }
        };

        setMessages(prev => [...prev, userMessage, aiMessage]);
        setInputQuery('');
        setIsLoading(false);
      },
      onError: (error: Error) => {
        const errorMessage: ChatMessage = {
          id: `error-${Date.now()}`,
          type: 'system',
          content: `Security Alert: ${error.message}. Your query has been blocked for your protection.`,
          timestamp: new Date(),
        };

        setMessages(prev => [...prev, errorMessage]);
        setInputQuery('');
        setIsLoading(false);
      }
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || isLoading) return;

    setIsLoading(true);
    sendMessage.mutate(inputQuery);
  };

  const getRiskColor = (risk?: string): 'default' | 'success' | 'warning' | 'error' => {
    switch (risk) {
      case 'LOW': return 'success';
      case 'MEDIUM': return 'warning';
      case 'HIGH': return 'error';
      case 'CRITICAL': return 'error';
      default: return 'default';
    }
  };

  const getMessageBackgroundColor = (messageType: string) => {
    if (messageType === 'user') return 'primary.light';
    if (messageType === 'system') return 'grey.100';
    return 'white';
  };

  return (
    <Box sx={{ bgcolor: '#f5f5f5', minHeight: '100vh', py: 2 }}>
      <Container maxWidth="lg">
        {/* Header */}
        <Paper elevation={2} sx={{ p: 3, mb: 3, bgcolor: 'primary.main', color: 'white' }}>
          <Box display="flex" alignItems="center" gap={2}>
            <MedicalIcon fontSize="large" />
            <Box>
              <Typography variant="h4" component="h1" fontWeight="bold">
                HealthAI Assistant
              </Typography>
              <Typography variant="subtitle1" sx={{ opacity: 0.9 }}>
                HIPAA-compliant medical information with advanced security
              </Typography>
            </Box>
          </Box>
          
          {/* Security Features Bar */}
          <Box display="flex" gap={2} mt={2} flexWrap="wrap">
            <Chip
              icon={<SecurityIcon />}
              label="HIPAA Compliant"
              size="small"
              sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
            />
            <Chip
              icon={<AIIcon />}
              label="AI-Powered"
              size="small"
              sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
            />
            <Chip
              icon={<SpeedIcon />}
              label="Real-time Analysis"
              size="small"
              sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
            />
            <Chip
              icon={<CheckIcon />}
              label="PII Protected"
              size="small"
              sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
            />
          </Box>
        </Paper>

        {/* Chat Interface */}
        <Paper elevation={2} sx={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
          {/* Messages Area */}
          <Box sx={{ flex: 1, overflow: 'auto', p: 2, bgcolor: '#fafafa' }}>
            {messages.map((message) => (
              <Box key={message.id} sx={{ mb: 2 }}>
                <Card 
                  elevation={1}
                  sx={{
                    bgcolor: getMessageBackgroundColor(message.type),
                    color: message.type === 'user' ? 'white' : 'text.primary',
                    ml: message.type === 'user' ? 4 : 0,
                    mr: message.type === 'user' ? 0 : 4
                  }}
                >
                  <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                    <Typography variant="body1" paragraph={!!message.content}>
                      {message.content}
                    </Typography>
                    
                    {/* Message Metadata */}
                    {message.metadata && (
                      <Box display="flex" gap={1} mt={1} flexWrap="wrap">
                        {message.metadata.responseTime && (
                          <Chip
                            size="small"
                            label={`${message.metadata.responseTime}ms`}
                            variant="outlined"
                          />
                        )}
                        {message.metadata.model && (
                          <Chip
                            size="small"
                            label={message.metadata.model}
                            variant="outlined"
                          />
                        )}
                        {message.metadata.confidence && (
                          <Chip
                            size="small"
                            label={`${(message.metadata.confidence * 100).toFixed(1)}% confidence`}
                            variant="outlined"
                          />
                        )}
                        {message.metadata.securityCheck && (
                          <Chip
                            size="small"
                            label={`Security: ${message.metadata.securityCheck}`}
                            color={getRiskColor(message.metadata.securityCheck)}
                            variant="outlined"
                          />
                        )}
                      </Box>
                    )}
                    
                    <Typography variant="caption" sx={{ opacity: 0.7, mt: 1, display: 'block' }}>
                      {message.timestamp.toLocaleTimeString()}
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
            ))}
            <div ref={messagesEndRef} />
          </Box>

          <Divider />

          {/* Input Area */}
          <Box sx={{ p: 3 }}>
            <form onSubmit={handleSubmit}>
              <Box display="flex" gap={2} alignItems="flex-end">
                <TextField
                  fullWidth
                  multiline
                  maxRows={4}
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  placeholder="Ask me any medical question... (PII will be automatically detected and protected)"
                  disabled={isLoading}
                  sx={{ flex: 1 }}
                />
                <Tooltip title="Send Message">
                  <span>
                    <IconButton
                      type="submit"
                      color="primary"
                      disabled={!inputQuery.trim() || isLoading}
                      sx={{ 
                        bgcolor: 'primary.main',
                        color: 'white',
                        '&:hover': { bgcolor: 'primary.dark' },
                        '&:disabled': { bgcolor: 'grey.300' }
                      }}
                    >
                      {isLoading ? <CircularProgress size={24} /> : <SendIcon />}
                    </IconButton>
                  </span>
                </Tooltip>
              </Box>
            </form>

            {/* Security Notice */}
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                🔒 Your queries are automatically scanned for PII and security threats. 
                All interactions are HIPAA-compliant and encrypted.
              </Typography>
            </Alert>
          </Box>
        </Paper>

        {/* Footer with Usage Guidelines */}
        <Paper elevation={1} sx={{ mt: 3, p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Usage Guidelines
          </Typography>
          <Box display="grid" gridTemplateColumns="repeat(auto-fit, minmax(300px, 1fr))" gap={2}>
            <Box>
              <Typography variant="subtitle2" color="success.main" gutterBottom>
                ✅ Recommended Queries:
              </Typography>
              <Typography variant="body2" component="ul" sx={{ pl: 2 }}>
                <li>General medical information</li>
                <li>Symptom descriptions</li>
                <li>Medication information</li>
                <li>Health condition explanations</li>
              </Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2" color="error.main" gutterBottom>
                ❌ Avoid Including:
              </Typography>
              <Typography variant="body2" component="ul" sx={{ pl: 2 }}>
                <li>Personal identifiable information</li>
                <li>Social security numbers</li>
                <li>Phone numbers or addresses</li>
                <li>Patient names or IDs</li>
              </Typography>
            </Box>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
};

export default HealthAI;