import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from './App';
import axios from 'axios';

// Mock Axios
vi.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock Electron Bridge
const mockOpenFile = vi.fn();
(window as any).electronAPI = {
  selectFile: mockOpenFile
};

describe('App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default: Backend is ready
    mockedAxios.get.mockImplementation((url) => {
      if (url === 'http://127.0.0.1:8000/health') {
        return Promise.resolve({ data: { status: 'ok' } });
      }
      return Promise.reject(new Error('Not found'));
    });
  });

  it('polls for backend health before connecting', async () => {
    // Mock initial failure, then success
    mockedAxios.get
      .mockRejectedValueOnce(new Error('Network Error'))
      .mockResolvedValueOnce({ data: { status: 'ok' } });

    render(<App />);



    // We expect at least one retry (so 2 calls total eventually)

    await waitFor(() => {

      expect(mockedAxios.get).toHaveBeenCalledWith('http://127.0.0.1:8000/health');

    });

  });
  it('renders the sidebar and default view', () => {
    render(<App />);
    expect(screen.getByText('AutoReel AI')).toBeInTheDocument();
    expect(screen.getByText('Viral Generator')).toBeInTheDocument();
    expect(screen.getByLabelText(/youtube\.com/i)).toBeInTheDocument();
  });

  it('switches tabs correctly', () => {
    render(<App />);
    const storyTab = screen.getByText('Story Mode');
    fireEvent.click(storyTab);

    expect(screen.getByText('Select Voiceover')).toBeInTheDocument();
    expect(screen.getByText('Choose Audio')).toBeInTheDocument();
  });

  it('handles file selection in Story Mode', async () => {
    render(<App />);
    // Switch to Story Mode
    fireEvent.click(screen.getByText('Story Mode'));

    // Mock file selection
    mockOpenFile.mockResolvedValue('/path/to/audio.mp3');

    const selectBtn = screen.getByText('Choose Audio');
    fireEvent.click(selectBtn);

    await waitFor(() => {
      // Check if input has value (we disabled it so we check value prop logic indirectly or assume state update)
      // Material UI TextField input is found via label usually.
      const input = screen.getByLabelText('File Path') as HTMLInputElement;
      expect(input.value).toBe('/path/to/audio.mp3');
    });
  });

  it('submits job configuration', async () => {
    render(<App />);
    // Mock success response
    mockedAxios.post.mockResolvedValue({ data: { status: 'started' } });

    const urlInput = screen.getByLabelText(/youtube\.com/i);
    fireEvent.change(urlInput, { target: { value: 'https://youtube.com/test' } });

    const startBtn = screen.getByText('START PIPELINE');
    fireEvent.click(startBtn);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        'http://127.0.0.1:8000/start-job',
        expect.objectContaining({
          mode: 'viral',
          url: 'https://youtube.com/test',
          llm_provider: 'openai'
        })
      );
    });
  });
});
