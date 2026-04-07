const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("picos", {
  getServiceStatus: () => ipcRenderer.invoke("get-service-status"),
  restartService: (name) => ipcRenderer.invoke("restart-service", name),
  restartAll: () => ipcRenderer.invoke("restart-all"),
  markFirstRunComplete: () => ipcRenderer.invoke("mark-first-run-complete"),
  getHealingLog: () => ipcRenderer.invoke("get-healing-log"),
  onStatusUpdate: (callback) => {
    ipcRenderer.on("service-status-update", (_, data) => callback(data));
    return () => ipcRenderer.removeAllListeners("service-status-update");
  },
});
