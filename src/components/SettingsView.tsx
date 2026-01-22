import { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Tabs, Tab, TextField, Switch, FormControlLabel,
  Button, CircularProgress, Snackbar, Alert, Slider, Divider, Grid, MenuItem
} from '@mui/material';
import axios from 'axios';

interface ConfigState {
  paths: any;
  downloader: any;
  transcription: any;
  intelligence: any;
  vision: any;
  retrieval: any;
  editing: any;
  overlay: any;
  packaging: any;
  distribution: any;
  pipeline: any;
}

const SECTIONS = [
  'General', 'Downloader', 'Transcription', 'Intelligence',
  'Vision', 'Retrieval', 'Editing', 'Overlay', 'Packaging', 'Distribution'
];

export default function SettingsView() {
  const [config, setConfig] = useState<ConfigState | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const res = await axios.get('http://127.0.0.1:8000/settings');
      setConfig(res.data);
      setLoading(false);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to load settings' });
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!config) return;
    try {
      setSaving(true);
      await axios.post('http://127.0.0.1:8000/settings', config);
      setMessage({ type: 'success', text: 'Settings saved successfully' });
      setSaving(false);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Save failed' });
      setSaving(false);
    }
  };

  const updateField = (section: keyof ConfigState, field: string, value: any) => {
    setConfig(prev => {
      if (!prev) return null;
      return {
        ...prev,
        [section]: {
          ...prev[section],
          [field]: value
        }
      };
    });
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
        <CircularProgress />
      </Box>
    );
  }

  const renderTextField = (section: keyof ConfigState, field: string, label: string, type: string = 'text') => (
    <TextField
      fullWidth
      label={label}
      type={type}
      value={config?.[section]?.[field] ?? ''}
      onChange={(e) => updateField(section, field, type === 'number' ? Number(e.target.value) : e.target.value)}
      variant="outlined"
      size="small"
      sx={{ mb: 2, '& .MuiInputBase-root': { color: '#fff' }, '& .MuiInputLabel-root': { color: '#aaa' }, '& .MuiOutlinedInput-notchedOutline': { borderColor: '#555' } }}
    />
  );

  const renderSwitch = (section: keyof ConfigState, field: string, label: string) => (
    <FormControlLabel
      control={
        <Switch
          checked={!!config?.[section]?.[field]}
          onChange={(e) => updateField(section, field, e.target.checked)}
        />
      }
      label={label}
      sx={{ mb: 2, display: 'block' }}
    />
  );

    const renderSlider = (section: keyof ConfigState, field: string, label: string, min: number, max: number, step: number = 1) => (
      <Box sx={{ mb: 2 }}>
        <Typography gutterBottom variant="caption" sx={{ color: '#aaa' }}>{label}: {config?.[section]?.[field]}</Typography>
        <Slider
          value={Number(config?.[section]?.[field] ?? 0)}
          min={min}
          max={max}
          step={step}
          onChange={(_, val) => updateField(section, field, val)}
          valueLabelDisplay="auto"
        />
      </Box>
    );

    const renderSelect = (section: keyof ConfigState, field: string, label: string, options: string[]) => (
      <TextField
        select
        fullWidth
        label={label}
        value={config?.[section]?.[field] ?? ''}
        onChange={(e) => updateField(section, field, e.target.value)}
        variant="outlined"
        size="small"
        sx={{ mb: 2, '& .MuiInputBase-root': { color: '#fff' }, '& .MuiInputLabel-root': { color: '#aaa' }, '& .MuiOutlinedInput-notchedOutline': { borderColor: '#555' }, '& .MuiSelect-icon': { color: '#fff' } }}
      >
        {options.map((option) => (
          <MenuItem key={option} value={option}>
            {option}
          </MenuItem>
        ))}
      </TextField>
    );

    const renderColorPicker = (section: keyof ConfigState, field: string, label: string) => (
        <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2, border: '1px solid #555', borderRadius: 1, p: 1 }}>
           <Typography sx={{ color: '#aaa', flexGrow: 1 }}>{label}</Typography>
           <input
              type="color"
              value={config?.[section]?.[field] ?? '#000000'}
              onChange={(e) => updateField(section, field, e.target.value)}
              style={{ width: 40, height: 40, border: 'none', padding: 0, backgroundColor: 'transparent', cursor: 'pointer' }}
              aria-label={label}
           />
           <Typography sx={{ minWidth: 60, textAlign: 'right' }}>{config?.[section]?.[field]}</Typography>
        </Box>
    );

    return (
      <Paper sx={{ p: 0, bgcolor: '#1e1e1e', color: '#fff', height: '100%', display: 'flex', flexDirection: 'column' }}>
         {config ? (
          <>
              <Box sx={{ borderBottom: 1, borderColor: '#333' }}>
                  <Tabs
                      value={activeTab}
                      onChange={(_, v) => setActiveTab(v)}
                      variant="scrollable"
                      scrollButtons="auto"
                      textColor="inherit"
                      indicatorColor="primary"
                  >
                  {SECTIONS.map((label, idx) => (
                      <Tab key={idx} label={label} />
                  ))}
                  </Tabs>
              </Box>

              <Box sx={{ p: 3, flexGrow: 1, overflowY: 'auto' }}>
                  {/* General / Paths */}
                  {activeTab === 0 && (
                  <Grid container spacing={2}>
                      <Grid item xs={12}><Typography variant="h6" sx={{ mb: 2 }}>Paths & Storage</Typography></Grid>
                      <Grid item xs={12}>{renderTextField('paths', 'workspace_dir', 'Workspace Directory')}</Grid>
                      <Grid item xs={12}>{renderTextField('paths', 'output_dir', 'Output Directory')}</Grid>
                      <Grid item xs={12}>{renderTextField('paths', 'log_dir', 'Log Directory')}</Grid>
                      <Grid item xs={12}><Divider sx={{ my: 2, bgcolor: '#333' }} /></Grid>
                      <Grid item xs={12}><Typography variant="h6" sx={{ mb: 2 }}>Pipeline</Typography></Grid>
                      <Grid item xs={12}>{renderSelect('pipeline', 'target_aspect_ratio', 'Target Aspect Ratio', ['9:16', '16:9', '1:1', '4:3', '3:4'])}</Grid>
                  </Grid>
                  )}

                  {/* Downloader */}
                  {activeTab === 1 && (
                  <Grid container spacing={2}>
                      <Grid item xs={6}>{renderSelect('downloader', 'resolution', 'Resolution', ['2160', '1440', '1080', '720', '480', '360'])}</Grid>
                      <Grid item xs={6}>{renderSelect('downloader', 'min_resolution', 'Min Resolution', ['1080', '720', '480', '360'])}</Grid>
                      <Grid item xs={6}>{renderSelect('downloader', 'video_format', 'Video Format', ['mp4', 'webm', 'mov', 'mkv'])}</Grid>
                      <Grid item xs={6}>{renderSelect('downloader', 'audio_format', 'Audio Format', ['wav', 'mp3', 'aac', 'm4a'])}</Grid>
                      <Grid item xs={12}>{renderSwitch('downloader', 'separate_audio', 'Separate Audio')}</Grid>
                      <Grid item xs={12}>{renderSwitch('downloader', 'check_duplicates', 'Check Duplicates')}</Grid>
                      <Grid item xs={12}>{renderTextField('downloader', 'retries', 'Retries', 'number')}</Grid>
                  </Grid>
                  )}

                  {/* Transcription */}
                  {activeTab === 2 && (
                      <Grid container spacing={2}>
                          <Grid item xs={6}>{renderSelect('transcription', 'model_size', 'Whisper Model Size', ['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3'])}</Grid>
                          <Grid item xs={6}>{renderSelect('transcription', 'compute_type', 'Compute Type', ['float16', 'float32', 'int8', 'int8_float16'])}</Grid>
                          <Grid item xs={6}>{renderSelect('transcription', 'device', 'Device', ['auto', 'cpu', 'cuda'])}</Grid>
                          <Grid item xs={6}>{renderTextField('transcription', 'language', 'Language Code')}</Grid>
                          <Grid item xs={12}>{renderSwitch('transcription', 'vad_filter', 'VAD Filter')}</Grid>
                          <Grid item xs={12}>{renderSwitch('transcription', 'enable_diarization', 'Enable Diarization')}</Grid>
                      </Grid>
                  )}

                  {/* Intelligence */}
                  {activeTab === 3 && (
                      <Grid container spacing={2}>
                          <Grid item xs={12}>{renderSelect('intelligence', 'llm_provider', 'LLM Provider', ['openai', 'anthropic', 'google', 'local'])}</Grid>
                          <Grid item xs={12}>{renderTextField('intelligence', 'model_name', 'Model Name')}</Grid>
                          <Grid item xs={12}>{renderTextField('intelligence', 'openai_api_key', 'OpenAI API Key', 'password')}</Grid>
                          <Grid item xs={12}>{renderTextField('intelligence', 'anthropic_api_key', 'Anthropic API Key', 'password')}</Grid>
                          <Grid item xs={12}>{renderSlider('intelligence', 'virality_threshold', 'Virality Threshold', 0, 100)}</Grid>
                          <Grid item xs={12}>{renderSlider('intelligence', 'chunk_duration_minutes', 'Chunk Duration (Minutes)', 1, 60)}</Grid>
                      </Grid>
                  )}

                  {/* Vision */}
                  {activeTab === 4 && (
                      <Grid container spacing={2}>
                          <Grid item xs={12}>{renderSlider('vision', 'face_detection_confidence', 'Face Detection Confidence', 0, 1, 0.05)}</Grid>
                          <Grid item xs={12}>{renderSlider('vision', 'stabilization_factor', 'Stabilization Factor', 0, 1, 0.05)}</Grid>
                          <Grid item xs={12}>{renderTextField('vision', 'vertical_crop_ratio', 'Vertical Crop Ratio', 'number')}</Grid>
                          <Grid item xs={12}>{renderSwitch('vision', 'debug_preview', 'Debug Preview Mode')}</Grid>
                      </Grid>
                  )}

                  {/* Retrieval */}
                  {activeTab === 5 && (
                      <Grid container spacing={2}>
                          <Grid item xs={12}>{renderTextField('retrieval', 'b_roll_library_path', 'B-Roll Library Path')}</Grid>
                          <Grid item xs={12}>{renderTextField('retrieval', 'clip_model_name', 'CLIP Model Name')}</Grid>
                          <Grid item xs={12}>{renderSlider('retrieval', 'similarity_threshold', 'Similarity Threshold', 0, 1, 0.05)}</Grid>
                      </Grid>
                  )}

                  {/* Editing */}
                  {activeTab === 6 && (
                      <Grid container spacing={2}>
                   <Grid item xs={12}>{renderSlider('editing', 'blur_radius', 'Blur Radius', 0, 100)}</Grid>
                   <Grid item xs={12}>{renderSlider('editing', 'music_volume', 'Music Volume', 0, 1, 0.1)}</Grid>
                   <Grid item xs={12}>{renderSlider('editing', 'fade_in_duration', 'Fade In (sec)', 0, 5, 0.1)}</Grid>
                   <Grid item xs={12}>{renderSlider('editing', 'transition_duration', 'Transition (sec)', 0, 2, 0.1)}</Grid>
              </Grid>
          )}

          {/* Overlay */}
          {activeTab === 7 && (
              <Grid container spacing={2}>
                  <Grid item xs={12}>{renderTextField('overlay', 'font_path', 'Font Path')}</Grid>
                  <Grid item xs={6}>{renderTextField('overlay', 'font_size', 'Font Size', 'number')}</Grid>
                  <Grid item xs={6}>{renderTextField('overlay', 'stroke_width', 'Stroke Width', 'number')}</Grid>
                  <Grid item xs={6}>{renderColorPicker('overlay', 'text_color', 'Text Color')}</Grid>
                  <Grid item xs={6}>{renderColorPicker('overlay', 'highlight_color', 'Highlight Color')}</Grid>
                  <Grid item xs={12}>{renderSlider('overlay', 'vertical_position', 'Vertical Position', 0, 1, 0.05)}</Grid>
              </Grid>
          )}

           {/* Packaging */}
           {activeTab === 8 && (
              <Grid container spacing={2}>
                  <Grid item xs={12}>{renderTextField('packaging', 'thumbnail_font_path', 'Thumbnail Font Path')}</Grid>
                  <Grid item xs={12}>{renderTextField('packaging', 'max_title_length', 'Max Title Length', 'number')}</Grid>
                  <Grid item xs={12}>{renderTextField('packaging', 'hashtags_count', 'Hashtags Count', 'number')}</Grid>
              </Grid>
          )}

          {/* Distribution */}
          {activeTab === 9 && (
              <Grid container spacing={2}>
                  <Grid item xs={12}>{renderTextField('distribution', 'youtube_client_secrets_path', 'YouTube Secrets Path')}</Grid>
                  <Grid item xs={12}>{renderTextField('distribution', 'tiktok_cookies_path', 'TikTok Cookies Path')}</Grid>
                  <Grid item xs={12}>{renderTextField('distribution', 'schedule_offset_hours', 'Schedule Offset (Hours)', 'number')}</Grid>
              </Grid>
          )}

        </Box>

        <Box sx={{ p: 2, borderTop: 1, borderColor: '#333', display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
          <Button variant="contained" color="primary" onClick={handleSave} disabled={saving}>
             {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </Box>
          </>
         ) : (           <Box sx={{ p: 4, textAlign: 'center' }}>
               <Typography color="error">Failed to load configuration.</Typography>
           </Box>
       )}

      <Snackbar open={!!message} autoHideDuration={6000} onClose={() => setMessage(null)}>
        <Alert onClose={() => setMessage(null)} severity={message?.type || 'info'} sx={{ width: '100%' }}>
          {message?.text}
        </Alert>
      </Snackbar>
    </Paper>
  );
}
