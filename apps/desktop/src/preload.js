const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("picos", {
  getServiceStatus: () => ipcRenderer.invoke("get-service-status"),
  restartService: (name) => ipcRenderer.invoke("restart-service", name),
  restartAll: () => ipcRenderer.invoke("restart-all"),
  markFirstRunComplete: () => ipcRenderer.invoke("mark-first-run-complete"),
  getHealingLog: () => ipcRenderer.invoke("get-healing-log"),
  checkFullDiskAccess: () => ipcRenderer.invoke("check-full-disk-access"),
  docker: {
    status: () => ipcRenderer.invoke("docker-status"),
    startAgentZero: () => ipcRenderer.invoke("docker-start-agent-zero"),
    stopAgentZero: () => ipcRenderer.invoke("docker-stop-agent-zero"),
    health: () => ipcRenderer.invoke("docker-health"),
  },
  onStatusUpdate: (callback) => {
    ipcRenderer.on("service-status-update", (_, data) => callback(data));
    return () => ipcRenderer.removeAllListeners("service-status-update");
  },
});
