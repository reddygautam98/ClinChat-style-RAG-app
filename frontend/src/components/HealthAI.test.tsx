import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import HealthAI from './HealthAI';

// Mock axios to prevent actual API calls in tests
jest.mock('axios');

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
    mutations: {
      retry: false,
    },
  },
});

const renderWithQueryClient = (component: React.ReactElement) => {
  const testQueryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={testQueryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe('HealthAI Component', () => {
  test('renders HealthAI component without crashing', () => {
    renderWithQueryClient(<HealthAI />);
    
    // Check if the component renders the main heading
    expect(screen.getByText('HealthAI Assistant')).toBeInTheDocument();
  });

  test('renders chat interface elements', () => {
    renderWithQueryClient(<HealthAI />);
    
    // Look for input field or send button
    const textInputs = screen.getAllByRole('textbox');
    expect(textInputs.length).toBeGreaterThan(0);
  });
});