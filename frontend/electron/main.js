const fs = require('fs');
const { app, BrowserWindow, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let sidecarProcess = null;
let sidecarRestartCount = 0;
const MAX_RESTARTS = 3;
const DEV_URL = process.env.ELECTRON_START_URL;
const DEV_LOAD_RETRY_MS = 1500;
const MAX_DEV_LOAD_ATTEMPTS = 20;

function startSidecar() {
  if (DEV_URL) {
    console.log('Live desktop dev mode detected; using the local backend on http://localhost:8000.');
    return;
  }

  const isDev = !app.isPackaged;
  const sidecarPath = isDev
    ? path.join(app.getAppPath(), '..', 'backend', 'dist', 'backend_sidecar', 'backend_sidecar.exe')
    : path.join(process.resourcesPath, 'backend_sidecar', 'backend_sidecar.exe');

  const sidecarDir = path.dirname(sidecarPath);

  console.log('Starting sidecar at:', sidecarPath);

  if (!fs.existsSync(sidecarPath)) {
    console.error('Backend sidecar was not found:', sidecarPath);
    return;
  }
  
  sidecarProcess = spawn(sidecarPath, [], {
    cwd: sidecarDir,
    env: { ...process.env, PORT: '8000' },
    shell: false
  });

  sidecarProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`);
  });

  sidecarProcess.stderr.on('data', (data) => {
    console.error(`Backend Error: ${data}`);
  });

  sidecarProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
    sidecarProcess = null;
    
    if (code !== 0 && sidecarRestartCount < MAX_RESTARTS) {
      sidecarRestartCount++;
      console.log(`Attempting restart ${sidecarRestartCount}/${MAX_RESTARTS}...`);
      setTimeout(startSidecar, 2000);
    }
  });
}

function resolveRendererIndexPath() {
  const baseDir = app.getAppPath();
  const candidateDirs = fs.readdirSync(baseDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .filter((dirName) => (
      dirName === 'build' ||
      dirName === 'build_app' ||
      dirName.startsWith('build_verify_suggestions') ||
      dirName.startsWith('build_verify_room_combobox')
    ));

  const candidates = candidateDirs
    .map((dirName) => ({
      dirName,
      indexPath: path.join(baseDir, dirName, 'index.html'),
    }))
    .filter(({ indexPath }) => fs.existsSync(indexPath))
    .sort((a, b) => fs.statSync(b.indexPath).mtimeMs - fs.statSync(a.indexPath).mtimeMs);

  if (candidates.length === 0) {
    return path.join(baseDir, 'build', 'index.html');
  }

  console.log('Using renderer build directory:', candidates[0].dirName);
  return candidates[0].indexPath;
}

function loadRenderer(win, attempt = 1) {
  if (DEV_URL) {
    win.loadURL(DEV_URL).catch((err) => {
      if (attempt >= MAX_DEV_LOAD_ATTEMPTS) {
        console.error(`Failed to load dev server after ${attempt} attempts:`, err);
        return;
      }

      console.log(
        `Dev server not ready yet (attempt ${attempt}/${MAX_DEV_LOAD_ATTEMPTS}). Retrying in ${DEV_LOAD_RETRY_MS}ms...`
      );
      setTimeout(() => loadRenderer(win, attempt + 1), DEV_LOAD_RETRY_MS);
    });
    return;
  }

  const indexPath = resolveRendererIndexPath();
  console.log('Loading production UI from:', indexPath);
  win.loadFile(indexPath).catch((err) => {
    console.error('Failed to load index.html:', err);
  });
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1100,
    minHeight: 760,
    autoHideMenuBar: true,
    backgroundColor: '#fafbfc',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: false, // Required for file:// to talk to http://localhost
    },
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  loadRenderer(win);
}

app.whenReady().then(() => {
  startSidecar();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (sidecarProcess) {
    sidecarProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('quit', () => {
  if (sidecarProcess) {
    sidecarProcess.kill();
  }
});
