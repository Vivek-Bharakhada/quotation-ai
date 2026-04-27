const fs = require('fs');
const { app, BrowserWindow, shell } = require('electron');
const path = require('path');
const os = require('os');
const { spawn } = require('child_process');

const LAUNCH_LOG = path.join(os.tmpdir(), 'quotation-ai-launch.log');
function logLine(message) {
  try {
    fs.appendFileSync(LAUNCH_LOG, `[${new Date().toISOString()}] ${message}\n`, 'utf8');
  } catch (error) {
    // Ignore logging failures; they should not break app startup.
  }
}

let sidecarProcess = null;
let mainWindow = null;
let sidecarRestartCount = 0;
let shutdownWatcherStarted = false;
let shutdownTimer = null;
const MAX_RESTARTS = 3;
const DEV_URL = process.env.ELECTRON_START_URL;
const ENABLE_BUILD_RESTART_WATCHER = process.env.ENABLE_APP_RESTART_WATCHER === '1';
const DEV_LOAD_RETRY_MS = 1500;
const MAX_DEV_LOAD_ATTEMPTS = 20;

logLine('main.js loaded');
process.on('uncaughtException', (error) => logLine(`uncaughtException: ${error?.stack || error}`));
process.on('unhandledRejection', (error) => logLine(`unhandledRejection: ${error?.stack || error}`));

function resolveSidecarPath() {
  if (!app.isPackaged) {
    return path.join(app.getAppPath(), '..', 'backend', 'dist', 'backend_sidecar', 'backend_sidecar.exe');
  }

  return path.join(process.resourcesPath, 'backend_sidecar', 'backend_sidecar.exe');
}

function startSidecar() {
  logLine('startSidecar called');
  if (DEV_URL) {
    console.log('Live desktop dev mode detected; using the local backend on http://localhost:8000.');
    return;
  }

  const sidecarPath = resolveSidecarPath();
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
  const preferredDirs = ['build_app', 'build'];
  for (const dirName of preferredDirs) {
    const indexPath = path.join(baseDir, dirName, 'index.html');
    if (fs.existsSync(indexPath)) {
      console.log('Using renderer build directory:', dirName);
      return indexPath;
    }
  }

  return path.join(baseDir, 'build', 'index.html');
}

function requestAppShutdown(reason) {
  if (shutdownTimer) {
    return;
  }

  console.log(`Detected build change (${reason}). Restarting the app with the fresh build.`);

  shutdownTimer = setTimeout(() => {
    shutdownTimer = null;
    try {
      app.relaunch();
    } catch (error) {
      console.warn('Failed to queue app relaunch', error);
    }
    app.exit(0);
  }, 1000);
}

function watchPathForChanges(targetPath, label) {
  if (!fs.existsSync(targetPath)) {
    console.log(`Skipping watcher for missing path: ${targetPath}`);
    return null;
  }

  try {
    return fs.watch(
      targetPath,
      { persistent: true },
      (_eventType, filename) => {
        const changedName = filename ? String(filename) : '';
        if (changedName && changedName.startsWith('.')) {
          return;
        }

        requestAppShutdown(label);
      }
    );
  } catch (error) {
    console.warn(`Failed to watch ${targetPath}`, error);
    return null;
  }
}

function startShutdownWatchers() {
  if (shutdownWatcherStarted || DEV_URL || !ENABLE_BUILD_RESTART_WATCHER) {
    if (!DEV_URL && !ENABLE_BUILD_RESTART_WATCHER) {
      console.log('Build-change auto-restart is disabled. Set ENABLE_APP_RESTART_WATCHER=1 to enable it.');
    }
    return;
  }

  shutdownWatcherStarted = true;

  const rendererIndexPath = resolveRendererIndexPath();
  const rendererBuildDir = path.dirname(rendererIndexPath);
  const sidecarPath = resolveSidecarPath();
  const sidecarDir = path.dirname(sidecarPath);
  const sidecarFile = path.join(sidecarDir, 'backend_sidecar.exe');

  console.log('Watching build folders for changes:');
  console.log(' - renderer:', rendererBuildDir);
  console.log(' - backend:', sidecarDir);

  const watchers = [
    watchPathForChanges(rendererBuildDir, 'renderer build'),
    watchPathForChanges(sidecarDir, 'backend sidecar bundle'),
    watchPathForChanges(sidecarFile, 'backend executable'),
  ].filter(Boolean);

  app.on('before-quit', () => {
    watchers.forEach((watcher) => {
      try {
        watcher.close();
      } catch (error) {
        console.warn('Failed to close a file watcher', error);
      }
    });

    if (shutdownTimer) {
      clearTimeout(shutdownTimer);
      shutdownTimer = null;
    }
  });
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
  logLine('createWindow called');
  mainWindow = new BrowserWindow({
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

  mainWindow.on('closed', () => {
    logLine('mainWindow closed');
    mainWindow = null;
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  loadRenderer(mainWindow);
}

app.whenReady().then(() => {
  logLine('app.whenReady resolved');
  startSidecar();
  startShutdownWatchers();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  logLine('window-all-closed');
  if (sidecarProcess) {
    sidecarProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('quit', () => {
  logLine('quit event');
  if (sidecarProcess) {
    sidecarProcess.kill();
  }
});
