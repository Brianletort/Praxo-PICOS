const { app, BrowserWindow, Tray, Menu, nativeImage, ipcMain } = require("electron");
const path = require("path");
const { ServiceSupervisor } = require("./supervisor");
const { SelfHealingEngine } = require("./self-healing");
const { DockerManager } = require("./docker-manager");
const { checkFullDiskAccess, requestFullDiskAccess } = require("./permissions");
const { runSetup, isSetupComplete } = require("./setup");
const { getInitialWindowUrl, startPackagedRuntime } = require("./runtime");

const DEV_URL = "http://127.0.0.1:3100";
const WEB_URL = process.env.PICOS_WEB_URL || "http://127.0.0.1:3777";
const IS_DEV = process.env.NODE_ENV === "development" || !app.isPackaged;

let mainWindow = null;
let tray = null;
let supervisor = null;
let healingEngine = null;
let dockerManager = null;

function createWindow(initialUrl) {
  const iconPath = path.join(__dirname, "..", "assets", "icon.png");
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: "Praxo-PICOS",
    titleBarStyle: "hiddenInset",
    icon: iconPath,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (initialUrl) {
    mainWindow.loadURL(initialUrl);
  }

  mainWindow.on("closed", () => { mainWindow = null; });
}

function ensureWindow(url) {
  if (!mainWindow) {
    createWindow(url);
    return;
  }
  if (url) {
    mainWindow.loadURL(url);
  }
  mainWindow.show();
}

function createTray() {
  const iconPath = path.join(__dirname, "..", "assets", "icon.png");
  let icon;
  try {
    icon = nativeImage.createFromPath(iconPath).resize({ width: 18, height: 18 });
  } catch {
    icon = nativeImage.createEmpty();
  }
  tray = new Tray(icon);
  tray.setToolTip("Praxo-PICOS");

  const contextMenu = Menu.buildFromTemplate([
    { label: "Open Dashboard", click: () => ensureWindow(getInitialWindowUrl({ isDev: IS_DEV, firstRun: false, devUrl: DEV_URL, packagedUrl: WEB_URL })) },
    { type: "separator" },
    { label: "System Status", sublabel: "All services running", enabled: false },
    { type: "separator" },
    { label: "Health Center", click: () => ensureWindow(`${IS_DEV ? DEV_URL : WEB_URL}/health`) },
    { label: "Settings", click: () => ensureWindow(`${IS_DEV ? DEV_URL : WEB_URL}/settings`) },
    { type: "separator" },
    { label: "Restart Services", click: () => supervisor?.restartAll() },
    { label: "Quit Praxo-PICOS", click: () => app.quit() },
  ]);
  tray.setContextMenu(contextMenu);
}

function isFirstRun() {
  const configPath = path.join(app.getPath("userData"), "first-run-complete");
  try {
    require("fs").accessSync(configPath);
    return false;
  } catch {
    return true;
  }
}

function markFirstRunComplete() {
  const configPath = path.join(app.getPath("userData"), "first-run-complete");
  require("fs").writeFileSync(configPath, new Date().toISOString());
}

app.whenReady().then(async () => {
  supervisor = new ServiceSupervisor();
  healingEngine = new SelfHealingEngine(supervisor);
  dockerManager = new DockerManager();

  const initialUrl = getInitialWindowUrl({
    isDev: IS_DEV,
    firstRun: isFirstRun(),
    devUrl: DEV_URL,
    packagedUrl: WEB_URL,
  });

  if (IS_DEV) {
    createWindow(initialUrl);
  } else {
    await startPackagedRuntime({
      isSetupComplete,
      runSetup,
      supervisor,
      healingEngine,
      createWindow,
      initialUrl,
      checkFullDiskAccess,
      requestFullDiskAccess: () => {
        if (mainWindow) {
          requestFullDiskAccess(mainWindow);
        }
      },
      log: (message) => console.log(message),
      error: (...args) => console.error(...args),
    });
  }

  createTray();

  ipcMain.handle("get-service-status", () => supervisor.getStatus());
  ipcMain.handle("restart-service", (_, name) => supervisor.restart(name));
  ipcMain.handle("restart-all", () => supervisor.restartAll());
  ipcMain.handle("mark-first-run-complete", () => markFirstRunComplete());
  ipcMain.handle("get-healing-log", () => healingEngine.getLog());

  ipcMain.handle("docker-status", () => dockerManager.getContainerStatus());
  ipcMain.handle("docker-start-agent-zero", () => dockerManager.start());
  ipcMain.handle("docker-stop-agent-zero", () => dockerManager.stop());
  ipcMain.handle("docker-health", () => dockerManager.healthCheck());
  ipcMain.handle("check-full-disk-access", () => checkFullDiskAccess());
});

app.on("before-quit", async () => {
  healingEngine?.stop();
  await supervisor?.stopAll();
});

app.on("window-all-closed", () => {});

app.on("activate", () => {
  if (mainWindow === null) createWindow();
});
