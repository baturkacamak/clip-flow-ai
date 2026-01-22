import React, { useState, useEffect, useRef } from 'react';
import {
  Box, Drawer, AppBar, Toolbar, List, Typography, Divider, ListItem,
  ListItemButton, ListItemIcon, ListItemText, TextField, Button,
      Accordion, AccordionSummary, AccordionDetails, Select, MenuItem,
      FormControl, InputLabel, Slider, Switch, FormControlLabel, Paper,
      CircularProgress, Chip, Stepper, Step, StepLabel
    } from '@mui/material';
    import {
      MovieCreation, AutoFixHigh, VideoLibrary, Settings,
      ExpandMore, FolderOpen, PlayArrow
    } from '@mui/icons-material';
    import { Snackbar, Alert } from '@mui/material';
    import axios from 'axios';

    // TypeScript definition for Electron API
    declare global {
      interface Window {
        electronAPI: {
          selectFile: () => Promise<string | null>;
        };
      }
    }

    const drawerWidth = 240;
    const STEPS = ['Ingestion', 'Transcription', 'Intelligence', 'Retrieval', 'Editing'];

    export default function App() {
      // --- State Management ---
      const [activeTab, setActiveTab] = useState('Viral Generator');
      const [logs, setLogs] = useState<string[]>([]);
      const [error, setError] = useState<string | null>(null);
      const [isProcessing, setIsProcessing] = useState(false);
      const [activeStep, setActiveStep] = useState(0);
      const logEndRef = useRef<HTMLDivElement>(null);

      // Configuration State
      const [config, setConfig] = useState({
        mode: 'viral',
        url: '',
        audio_path: '',
        script: '',
        llm_provider: 'openai',
        topic: 'General',
        music_vol: 0.1,
        blur: 20,
        face_track: true,
        platform: 'youtube',
        dry_run: false
      });

      // --- WebSocket Connection ---
      useEffect(() => {
        let ws: WebSocket;
        let reconnectTimer: any;
        let healthCheckTimer: any;

        const connect = () => {
          ws = new WebSocket('ws://127.0.0.1:8000/ws/logs');

          ws.onopen = () => {
            console.log('Connected to Log Stream');
            setLogs((prev) => [...prev, '--- Connected to Backend ---']);
            setError(null);
          };

          ws.onmessage = (event) => {
            const msg = event.data;
            setLogs((prev) => [...prev, msg]);

            // Smart Log Parsing for Stepper
            if (msg.includes('Initiating download') || msg.includes('found in history')) setActiveStep(0);
            if (msg.includes('Transcription') || msg.includes('Loading cached transcript')) setActiveStep(1);
            if (msg.includes('Curating') || msg.includes('Curation')) setActiveStep(2);
            if (msg.includes('Retrieval') || msg.includes('Indexing')) setActiveStep(3);
            if (msg.includes('Compositing') || msg.includes('Packaging')) setActiveStep(4);

            // Completion & Error Handling
            if (msg.includes('Successfully processed') || msg.includes('Story Mode finished')) {
                 setIsProcessing(false);
                 setActiveStep(5); // Complete
            }
            if (msg.includes('ERROR') || msg.includes('PIPELINE ERROR') || msg.includes('No clips found')) {
                 setIsProcessing(false);
                 // Optional: Set error state if we want a popup, but logs usually suffice
                 // setError('Pipeline Error. Check logs.');
            }
          };

          ws.onclose = () => {
            // setError('Log stream disconnected. Reconnecting...');
            reconnectTimer = setTimeout(waitForBackend, 3000);
          };

          ws.onerror = (err) => {
            console.error('WebSocket Error:', err);
            ws.close();
          };
        };

        const waitForBackend = async () => {
          try {
            await axios.get('http://127.0.0.1:8000/health');
            connect();
          } catch (err) {
            console.log('Backend not ready. Retrying in 1s...');
            healthCheckTimer = setTimeout(waitForBackend, 1000);
          }
        };

        waitForBackend();

        return () => {
          if (ws) ws.close();
          if (reconnectTimer) clearTimeout(reconnectTimer);
          if (healthCheckTimer) clearTimeout(healthCheckTimer);
        };
      }, []);

      // Auto-scroll logs
      useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, [logs]);

      // --- Handlers ---
      const handleConfigChange = (key: string, value: any) => {
        setConfig(prev => ({ ...prev, [key]: value }));
      };

      const handleSelectFile = async () => {
        const path = await window.electronAPI.selectFile();
        if (path) handleConfigChange('audio_path', path);
      };

      const handleStartJob = async () => {
        if (isProcessing) return;
        setIsProcessing(true);
        setActiveStep(0);
        setLogs([]); // Clear previous logs
        try {
          const mode = activeTab === 'Viral Generator' ? 'viral' : 'story';
          const payload = { ...config, mode };
          await axios.post('http://127.0.0.1:8000/start-job', payload);
          setLogs(prev => [...prev, `--- Sending Job (${mode}) ---`]);
        } catch (err: any) {
          console.error(err);
          const msg = err.response?.data?.detail || 'Could not contact backend.';
          setError(`ERROR: ${msg}`);
          setLogs(prev => [...prev, `ERROR: ${msg}`]);
          setIsProcessing(false);
        }
      };

      const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
          handleStartJob();
        }
      };

      return (
        <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
          {/* Sidebar */}
          <Drawer
            sx={{
              width: drawerWidth,
              flexShrink: 0,
              '& .MuiDrawer-paper': {
                width: drawerWidth,
                boxSizing: 'border-box',
                bgcolor: '#1e1e1e',
                color: '#fff'
              },
            }}
            variant="permanent"
            anchor="left"
          >
            <Toolbar>
              <Typography variant="h6" noWrap component="div" sx={{ color: '#90caf9', fontWeight: 'bold' }}>
                AutoReel AI
              </Typography>
            </Toolbar>
            <Divider sx={{ borderColor: '#444' }} />
            <List>
              {['Viral Generator', 'Story Mode', 'Library', 'Settings'].map((text) => (
                <ListItem key={text} disablePadding>
                  <ListItemButton
                    selected={activeTab === text}
                    onClick={() => setActiveTab(text)}
                    sx={{ '&.Mui-selected': { bgcolor: '#333' } }}
                  >
                    <ListItemIcon sx={{ color: '#ccc' }}>
                      {text === 'Viral Generator' ? <AutoFixHigh /> : text === 'Story Mode' ? <MovieCreation /> : text === 'Library' ? <VideoLibrary /> : <Settings />}
                    </ListItemIcon>
                    <ListItemText primary={text} />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </Drawer>

          {/* Main Content */}
          <Box component="main" sx={{ flexGrow: 1, bgcolor: '#121212', color: '#fff', p: 3, display: 'flex', flexDirection: 'column' }}>

            {/* Global Settings (Accordions) */}
            <Box sx={{ mb: 2 }}>
              <Accordion sx={{ bgcolor: '#2e2e2e', color: '#fff' }}>
                <AccordionSummary expandIcon={<ExpandMore sx={{ color: '#fff' }} />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', justifyContent: 'space-between', pr: 2 }}>
                    <Typography>⚙️ Global Configuration</Typography>
                    <Chip
                      label={isProcessing ? "Processing..." : "Idle"}
                      color={isProcessing ? "warning" : "success"}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  {/* Row 1: AI */}
                  <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                    <FormControl fullWidth size="small">
                      <InputLabel sx={{ color: '#aaa' }}>LLM Provider</InputLabel>
                      <Select
                        value={config.llm_provider}
                        label="LLM Provider"
                        onChange={(e) => handleConfigChange('llm_provider', e.target.value)}
                        sx={{ color: '#fff', '.MuiOutlinedInput-notchedOutline': { borderColor: '#555' } }}
                      >
                        <MenuItem value="openai">OpenAI (GPT-4)</MenuItem>
                        <MenuItem value="anthropic">Anthropic (Claude)</MenuItem>
                      </Select>
                    </FormControl>
                    <TextField
                      fullWidth size="small" label="Focus Topic" variant="outlined"
                      value={config.topic} onChange={(e) => handleConfigChange('topic', e.target.value)}
                      InputLabelProps={{ style: { color: '#aaa' } }}
                      InputProps={{ style: { color: '#fff', borderColor: '#555' } }}
                      sx={{ '.MuiOutlinedInput-notchedOutline': { borderColor: '#555' } }}
                    />
                  </Box>

                  {/* Row 2: Video & Audio */}
                  <Box sx={{ display: 'flex', gap: 4, mb: 2, alignItems: 'center' }}>
                    <Box sx={{ width: '30%' }}>
                      <Typography gutterBottom>Background Blur</Typography>
                      <Slider value={config.blur} onChange={(_, v) => handleConfigChange('blur', v)} />
                    </Box>
                    <Box sx={{ width: '30%' }}>
                      <Typography gutterBottom>Music Volume</Typography>
                      <Slider value={config.music_vol} max={1.0} step={0.1} onChange={(_, v) => handleConfigChange('music_vol', v)} />
                    </Box>
                    <FormControlLabel
                      control={<Switch checked={config.face_track} onChange={(e) => handleConfigChange('face_track', e.target.checked)} />}
                      label="Face Tracking"
                    />
                  </Box>

                  {/* Row 3: Distribution */}
                  <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                    <FormControl size="small" sx={{ width: 200 }}>
                      <InputLabel sx={{ color: '#aaa' }}>Platform</InputLabel>
                      <Select
                        value={config.platform}
                        label="Platform"
                        onChange={(e) => handleConfigChange('platform', e.target.value)}
                        sx={{ color: '#fff', '.MuiOutlinedInput-notchedOutline': { borderColor: '#555' } }}
                      >
                        <MenuItem value="youtube">YouTube Shorts</MenuItem>
                        <MenuItem value="tiktok">TikTok</MenuItem>
                      </Select>
                    </FormControl>
                    <FormControlLabel
                      control={<Switch checked={config.dry_run} onChange={(e) => handleConfigChange('dry_run', e.target.checked)} />}
                      label="Dry Run (No Upload)"
                    />
                  </Box>
                </AccordionDetails>
              </Accordion>
            </Box>

            {/* Stepper for Progress */}
            <Box sx={{ width: '100%', mb: 3 }}>
              <Stepper activeStep={activeStep} alternativeLabel>
                {STEPS.map((label) => (
                  <Step key={label}>
                    <StepLabel sx={{ '& .MuiStepLabel-label': { color: '#bbb' } }}>{label}</StepLabel>
                  </Step>
                ))}
              </Stepper>
            </Box>

            {/* Tab Specific Content */}
            <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>

              {activeTab === 'Viral Generator' && (              <Paper sx={{ p: 3, bgcolor: '#1e1e1e', mb: 2 }}>
                <Typography variant="h5" sx={{ mb: 2 }}>Paste YouTube URL</Typography>
                <TextField
                  fullWidth label="https://www.youtube.com/watch?v=..." variant="outlined"
                  value={config.url}
                  onChange={(e) => handleConfigChange('url', e.target.value)}
                  onKeyDown={handleKeyDown}
                  InputLabelProps={{ style: { color: '#aaa' } }}
                  InputProps={{ style: { color: '#fff', fontSize: '1.2rem' } }}
                  sx={{ '.MuiOutlinedInput-notchedOutline': { borderColor: '#555' } }}
                />
              </Paper>
            )}

            {activeTab === 'Story Mode' && (
              <Paper sx={{ p: 3, bgcolor: '#1e1e1e', mb: 2 }}>
                <Typography variant="h5" sx={{ mb: 2 }}>Select Voiceover</Typography>
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  <Button variant="contained" onClick={handleSelectFile} startIcon={<FolderOpen />}>
                    Choose Audio
                  </Button>
                  <TextField
                    fullWidth disabled value={config.audio_path} label="File Path"
                    InputLabelProps={{ style: { color: '#aaa' } }}
                    InputProps={{ style: { color: '#fff' } }}
                  />
                </Box>
                <TextField
                  fullWidth multiline rows={2} label="Optional Script (Context)"
                  value={config.script} onChange={(e) => handleConfigChange('script', e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleStartJob(); } }}
                  InputLabelProps={{ style: { color: '#aaa' } }}
                  InputProps={{ style: { color: '#fff' } }}
                  sx={{ '.MuiOutlinedInput-notchedOutline': { borderColor: '#555' } }}
                />
              </Paper>
            )}

            {/* Action Button */}
            {(activeTab === 'Viral Generator' || activeTab === 'Story Mode') && (
              <Button
                variant="contained"
                color="primary"
                size="large"
                startIcon={isProcessing ? <CircularProgress size={24} color="inherit" /> : <PlayArrow />}
                onClick={handleStartJob}
                disabled={isProcessing}
                sx={{ py: 2, fontSize: '1.1rem', fontWeight: 'bold' }}
              >
                {isProcessing ? 'PROCESSING...' : 'START PIPELINE'}
              </Button>
            )}
          </Box>

          {/* Console Log */}
          <Box sx={{ height: 200, bgcolor: '#000', borderRadius: 1, p: 2, overflowY: 'auto', fontFamily: 'monospace', border: '1px solid #333' }}>
            <Typography variant="caption" sx={{ color: '#666', display: 'block', mb: 1 }}>CONSOLE OUTPUT</Typography>
            {logs.length === 0 && <Typography variant="body2" sx={{ color: '#444' }}>Waiting for jobs...</Typography>}
            {logs.map((log, i) => (
              <div key={i} style={{ color: log.includes('ERROR') ? '#ff5252' : log.includes('SUCCESS') ? '#4caf50' : log.includes('WARNING') ? '#ff9800' : '#e0e0e0', marginBottom: 4 }}>
                {log}
              </div>
            ))}
            <div ref={logEndRef} />
          </Box>

          {/* Error Snackbar */}
          <Snackbar open={!!error} autoHideDuration={6000} onClose={() => setError(null)}>
            <Alert onClose={() => setError(null)} severity="error" sx={{ width: '100%' }}>
              {error}
            </Alert>
          </Snackbar>

        </Box>
      </Box>
    );
  }
