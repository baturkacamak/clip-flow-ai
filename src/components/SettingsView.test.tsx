import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SettingsView from './SettingsView';
import axios from 'axios';

// Mock Axios
vi.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

const mockConfig = {
  paths: {
    base_dir: '.',
    workspace_dir: 'assets/workspace',
    output_dir: 'outputs',
    log_dir: 'logs',
    cookies_file: 'config/cookies.txt',
    history_file: 'assets/workspace/download_history.json'
  },
  downloader: {
    resolution: '1080',
    min_resolution: '720',
    video_format: 'mp4',
    separate_audio: true,
    audio_format: 'wav',
    check_duplicates: true,
    retries: 3
  },
  transcription: {
    model_size: 'large-v2',
    compute_type: 'float16',
    device: 'auto',
    language: 'en',
    beam_size: 5,
    vad_filter: true,
    min_silence_duration_ms: 500,
    enable_diarization: false
  },
  intelligence: {
    llm_provider: 'openai',
    model_name: 'gpt-4-0125-preview',
    virality_threshold: 75,
    chunk_duration_minutes: 10,
    focus_topic: null,
    openai_api_key: 'sk-test-key',
    anthropic_api_key: ''
  },
  vision: {
    face_detection_confidence: 0.7,
    stabilization_factor: 0.1,
    vertical_crop_ratio: 0.5625,
    debug_preview: true
  },
  retrieval: {
    b_roll_library_path: 'assets/b_roll',
    clip_model_name: 'clip-ViT-B-32',
    similarity_threshold: 0.25,
    deduplication_window: 5
  },
  editing: {
    output_resolution: [1080, 1920],
    blur_radius: 21,
    music_volume: 0.1,
    fade_in_duration: 0.5,
    transition_duration: 0.2
  },
  overlay: {
    font_path: 'assets/fonts/TheBoldFont.ttf',
    font_size: 70,
    highlight_color: '#FFFF00',
    text_color: '#FFFFFF',
    stroke_width: 4,
    max_words_per_line: 3,
    vertical_position: 0.7
  },
  packaging: {
    thumbnail_font_path: 'assets/fonts/TheBoldFont.ttf',
    max_title_length: 50,
    hashtags_count: 5
  },
  distribution: {
    youtube_client_secrets_path: 'config/client_secrets.json',
    tiktok_cookies_path: 'assets/auth/tiktok_cookies.json',
    schedule_offset_hours: 2
  },
  pipeline: {
    target_aspect_ratio: '9:16'
  }
};

describe('SettingsView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue({ data: mockConfig });
    mockedAxios.post.mockResolvedValue({ data: { status: 'updated', config: mockConfig } });
  });

  it('loads and displays settings on mount', async () => {
    render(<SettingsView />);

    // Check loading state
    expect(screen.getByRole('progressbar')).toBeInTheDocument();

    // Check loaded state
    await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    // Check for "General" tab values (default active)
    expect(screen.getByDisplayValue('assets/workspace')).toBeInTheDocument();

    // Switch to Intelligence tab to check for model name
    fireEvent.click(screen.getByText('Intelligence'));
    expect(screen.getByDisplayValue('gpt-4-0125-preview')).toBeInTheDocument();
    expect(screen.getByDisplayValue('75')).toBeInTheDocument(); // virality_threshold
  });

  it('displays error if loading settings fails', async () => {
    mockedAxios.get.mockRejectedValue(new Error('Failed to load'));
    render(<SettingsView />);

    const errorMessages = await screen.findAllByText(/Failed to load/i);
    expect(errorMessages.length).toBeGreaterThan(0);
  });

  it('allows updating a simple text field', async () => {
    render(<SettingsView />);
    await waitFor(() => expect(screen.queryByRole('progressbar')).not.toBeInTheDocument());

    // Switch to Intelligence tab
    fireEvent.click(screen.getByText('Intelligence'));

    const modelInput = screen.getByDisplayValue('gpt-4-0125-preview');
    fireEvent.change(modelInput, { target: { value: 'gpt-3.5-turbo' } });

    expect(modelInput).toHaveValue('gpt-3.5-turbo');
  });

  it('allows updating a nested number field', async () => {
    render(<SettingsView />);
    await waitFor(() => expect(screen.queryByRole('progressbar')).not.toBeInTheDocument());

    // Switch to Intelligence tab
    fireEvent.click(screen.getByText('Intelligence'));

    const thresholdInput = screen.getByDisplayValue('75');
    fireEvent.change(thresholdInput, { target: { value: '80' } });

    expect(thresholdInput).toHaveValue('80');
  });

  it('saves settings when Save button is clicked', async () => {
    render(<SettingsView />);
    await waitFor(() => expect(screen.queryByRole('progressbar')).not.toBeInTheDocument());

    // Switch to Intelligence tab
    fireEvent.click(screen.getByText('Intelligence'));

    // Change a value
    const modelInput = screen.getByDisplayValue('gpt-4-0125-preview');
    fireEvent.change(modelInput, { target: { value: 'gpt-4-turbo' } });

    // Click Save
    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);

    await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith('http://127.0.0.1:8000/settings', expect.objectContaining({
            intelligence: expect.objectContaining({
                model_name: 'gpt-4-turbo'
            })
        }));
    });

    // Check for success message
    expect(await screen.findByText('Settings saved successfully')).toBeInTheDocument();
  });

  it('displays error if saving settings fails', async () => {
    mockedAxios.post.mockRejectedValue(new Error('Save failed'));
    render(<SettingsView />);
    await waitFor(() => expect(screen.queryByRole('progressbar')).not.toBeInTheDocument());

    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);

    expect(await screen.findByText(/Save failed/i)).toBeInTheDocument();
  });

  it('organizes settings into tabs or sections', async () => {
      render(<SettingsView />);
      await waitFor(() => expect(screen.queryByRole('progressbar')).not.toBeInTheDocument());

      // Ensure we have some navigation or section headers
      expect(screen.getByText(/Intelligence/i)).toBeInTheDocument();
      expect(screen.getByText(/Downloader/i)).toBeInTheDocument();
  });

  it('renders select inputs for resolution', async () => {
    render(<SettingsView />);
    await waitFor(() => expect(screen.queryByRole('progressbar')).not.toBeInTheDocument());

    // Switch to Downloader tab
    fireEvent.click(screen.getByText('Downloader'));

    // Check if resolution is rendered (we will implement it as a Select)
    // For MUI Select, the input is hidden, but we can find the trigger by its value or label
    const resolutionInput = screen.getByLabelText('Resolution');
    expect(resolutionInput).toBeInTheDocument();

    // If it's a select, we should be able to change it
    fireEvent.mouseDown(resolutionInput); // Open dropdown
    const option720 = await screen.findByRole('option', { name: '720' });
    fireEvent.click(option720);

    // For MUI Select, the trigger div displays the text
    expect(resolutionInput).toHaveTextContent('720');
  });

  it('renders color pickers for overlay settings', async () => {
    render(<SettingsView />);
    await waitFor(() => expect(screen.queryByRole('progressbar')).not.toBeInTheDocument());

    // Switch to Overlay tab
    fireEvent.click(screen.getByText('Overlay'));

    // Text Color should be a color input
    // Note: customized color pickers might be complex, but <input type="color"> is accessible by label
    const colorInput = screen.getByLabelText('Text Color');
    // We expect it to be type color or similar.
    // If we use MUI MuiInputBase-input, it might just be text, but we want to change it to Color.
    // For now, let's assume we use a native color input or a text field that accepts hex.
    // The requirement is to "change them" to be "other types".

    // Let's assert it accepts color format or is type color
    // If native:
    expect(colorInput).toHaveAttribute('type', 'color');
    fireEvent.change(colorInput, { target: { value: '#000000' } });
    expect(colorInput).toHaveValue('#000000');
  });
});
