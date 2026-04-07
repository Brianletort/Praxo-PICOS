const { app, BrowserWindow, Tray, Menu, nativeImage, ipcMain } = require("electron");
const path = require("path");
const { ServiceSupervisor } = require("./supervisor");
const { SelfHealingEngine } = require("./self-healing");

const WEB_URL = process.env.PICOS_WEB_URL || "http://127.0.0.1:3777";
const IS_DEV = process.env.NODE_ENV === "development" || !app.isPackaged;

let mainWindow = null;
let tray = null;
let supervisor = null;
let healingEngine = null;

function createWindow() {
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

  if (IS_DEV) {
    mainWindow.loadURL("http://127.0.0.1:3100");
  } else {
    mainWindow.loadURL(WEB_URL);
  }

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
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
    { label: "Open Dashboard", click: () => mainWindow?.show() || createWindow() },
    { type: "separator" },
    { label: "System Status", sublabel: "All services running", enabled: false },
    { type: "separator" },
    { label: "Health Center", click: () => { if (mainWindow) mainWindow.loadURL(`${IS_DEV ? "http://127.0.0.1:3100" : WEB_URL}/health`); } },
    { label: "Settings", click: () => { if (mainWindow) mainWindow.loadURL(`${IS_DEV ? "http://127.0.0.1:3100" : WEB_URL}/settings`); } },
    { type: "separator" },
    { label: "Restart Services", click: () => supervisor?.restartAll() },
    { label: "Quit Praxo-PICOS", click: () => app.quit() },
  ]);

  tray.setContextMenu(contextMenu);
}

function isFirstRun() {
  const configPath = path.join(
    app.getPath("userData"),
    "first-run-complete"
  );
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

  createWindow();
  createTray();

  if (isFirstRun()) {
    const baseUrl = IS_DEV ? "http://127.0.0.1:3100" : WEB_URL;
    mainWindow.loadURL(`${baseUrl}/onboarding`);
  }

  if (!IS_DEV) {
    await supervisor.startAll();
    healingEngine.start();
  }

  ipcMain.handle("get-service-status", () => supervisor.getStatus());
  ipcMain.handle("restart-service", (_, name) => supervisor.restart(name));
  ipcMain.handle("restart-all", () => supervisor.restartAll());
  ipcMain.handle("mark-first-run-complete", () => markFirstRunComplete());
  ipcMain.handle("get-healing-log", () => healingEngine.getLog());
});

app.on("before-quit", async () => {
  healingEngine?.stop();
  await supervisor?.stopAll();
});

app.on("window-all-closed", () => {
  // Keep running in tray on macOS
});

app.on("activate", () => {
  if (mainWindow === null) createWindow();
});
