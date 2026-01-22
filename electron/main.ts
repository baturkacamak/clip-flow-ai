import { app, BrowserWindow, ipcMain, dialog } from 'electron';
import path from 'path';
import { spawn, ChildProcess } from 'child_process';

let mainWindow: BrowserWindow | null = null;
let pythonProcess: ChildProcess | null = null;

// --- Python Backend Management ---
const PY_SERVER_PATH = path.join(__dirname, '../backend/server.py');

function createPythonProcess() {
  console.log(`[Electron] Check SKIP_BACKEND: '${process.env.SKIP_BACKEND}'`);
  if (process.env.SKIP_BACKEND === 'true') {
    console.log('Skipping Python Backend spawn (managed externally)...');
    return;
  }

  console.log('Starting Python Backend...');
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';

  try {
    pythonProcess = spawn(pythonCmd, [PY_SERVER_PATH], {
      cwd: path.join(__dirname, '../'), // Run from root
    });

    pythonProcess.stdout?.on('data', (data) => {
      console.log(`[Python]: ${data}`);
    });

    pythonProcess.stderr?.on('data', (data) => {
      console.error(`[Python Err]: ${data}`);
    });

    pythonProcess.on('error', (err) => {
      console.error('Failed to start Python process:', err);
      dialog.showErrorBox('Backend Error', `Failed to start Python backend.\n${err.message}\n\nPlease ensure '${pythonCmd}' is installed and in your PATH, or start the backend manually.`);
    });
  } catch (err) {
    console.error('Exception spawning python:', err);
  }
}

function killPythonProcess() {
  if (pythonProcess) {
    console.log('Killing Python Backend...');
    pythonProcess.kill();
    pythonProcess = null;
  }
}

// --- Window Creation ---
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  // In Dev, load Vite server. In Prod, load index.html
  mainWindow.loadURL('http://localhost:5173');
  // mainWindow.loadFile(path.join(__dirname, '../dist/index.html')); // For Prod
}

// --- Lifecycle & IPC ---
app.whenReady().then(() => {
  createPythonProcess();
  createWindow();

  ipcMain.handle('dialog:openFile', async () => {
    const { canceled, filePaths } = await dialog.showOpenDialog({
      properties: ['openFile'],
      filters: [{ name: 'Audio', extensions: ['mp3', 'wav'] }],
    });
    if (canceled) return null;
    return filePaths[0];
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('will-quit', () => {
  killPythonProcess();
});
