export default {
  post: jest.fn(() => Promise.resolve({ 
    data: { 
      sessionId: 'test-session-123',
      message: 'Test response',
      response: 'Test AI response',
      responseTime: 100,
      model: 'test-model',
      confidence: 0.95,
      securityCheck: 'LOW'
    } 
  })),
  get: jest.fn(() => Promise.resolve({ data: {} })),
  put: jest.fn(() => Promise.resolve({ data: {} })),
  delete: jest.fn(() => Promise.resolve({ data: {} })),
  create: jest.fn(() => ({
    post: jest.fn(() => Promise.resolve({ 
      data: { 
        sessionId: 'test-session-123',
        message: 'Test response',
        response: 'Test AI response',
        responseTime: 100,
        model: 'test-model',
        confidence: 0.95,
        securityCheck: 'LOW'
      } 
    })),
    get: jest.fn(() => Promise.resolve({ data: {} })),
    put: jest.fn(() => Promise.resolve({ data: {} })),
    delete: jest.fn(() => Promise.resolve({ data: {} })),
  })),
  defaults: {
    adapter: {},
  },
  interceptors: {
    request: {
      use: jest.fn(),
      eject: jest.fn(),
    },
    response: {
      use: jest.fn(),
      eject: jest.fn(),
    },
  },
};