const { spawn, execSync } = require("child_process");
const http = require("http");
const path = require("path");
const fs = require("fs");
const os = require("os");

function getAppRoot() {
  try {
    const { app } = require("electron");
    if (app.isPackaged) {
      return path.join(process.resourcesPath, "app");
    }
  } catch {}
  return path.resolve(__dirname, "..", "..", "..");
}

function findPython() {
  const dataVenv = path.join(getDataDir(), "venv", "bin", "python3");
  if (fs.existsSync(dataVenv)) return dataVenv;
  const root = getAppRoot();
  const devVenv = path.join(root, ".venv", "bin", "python3");
  if (fs.existsSync(devVenv)) return devVenv;
  for (const cmd of ["python3.14", "python3.13", "python3.12", "python3"]) {
    try {
      const p = execSync(`which ${cmd}`, { encoding: "utf8", timeout: 3000 }).trim();
      if (p) return p;
    } catch {}
  }
  return "python3";
}

function findQdrant() {
  const root = getAppRoot();
  const bundled = path.join(root, "vendor", "qdrant");
  if (fs.existsSync(bundled)) return bundled;
  try {
    return execSync("which qdrant", { encoding: "utf8", timeout: 3000 }).trim();
  } catch {
    return null;
  }
}

function getDataDir() {
  return path.join(os.homedir(), "Library", "Application Support", "Praxo-PICOS");
}

const SERVICE_GRAPH = [
  {
    name: "qdrant",
    getCommand: () => {
      const binary = findQdrant();
      if (!binary) return null;
      const qdrantDir = path.join(getDataDir(), "qdrant");
      const configDir = path.join(qdrantDir, "config");
      const storageDir = path.join(qdrantDir, "storage");
      const snapshotsDir = path.join(qdrantDir, "snapshots");
      fs.mkdirSync(configDir, { recursive: true });
      fs.mkdirSync(storageDir, { recursive: true });
      fs.mkdirSync(snapshotsDir, { recursive: true });
      const configPath = path.join(configDir, "config.yaml");
      if (!fs.existsSync(configPath)) {
        fs.writeFileSync(configPath, [
          "service:",
          "  http_port: 6733",
          "  grpc_port: 6734",
          "storage:",
          `  storage_path: ${storageDir}`,
          `  snapshots_path: ${snapshotsDir}`,
          "telemetry_disabled: true",
          "",
        ].join("\n"));
      }
      return [binary, "--config-path", configPath, "--disable-telemetry"];
    },
    cwd: () => path.join(getDataDir(), "qdrant"),
    healthUrl: "http://127.0.0.1:6733/healthz",
    healthInterval: 10000,
    dependsOn: [],
    managed: true,
  },
  {
    name: "api",
    getCommand: () => {
      const py = findPython();
      return [
        py, "-m", "uvicorn",
        "services.api.src.praxo_picos_api.main:app",
        "--host", "127.0.0.1", "--port", "8865",
      ];
    },
    cwd: () => getAppRoot(),
    healthUrl: "http://127.0.0.1:8865/health",
    healthInterval: 10000,
    dependsOn: ["qdrant"],
    managed: true,
  },
  {
    name: "workers",
    getCommand: () => null,
    healthUrl: null,
    healthInterval: 30000,
    dependsOn: ["api"],
    managed: false,
  },
  {
    name: "web",
    getCommand: () => {
      const root = getAppRoot();
      const standaloneServer = path.join(root, "web-standalone", "apps", "web", "server.js");
      if (fs.existsSync(standaloneServer)) {
        try {
          return [process.execPath, standaloneServer];
        } catch {}
      }
      const nextBin = path.join(root, "apps", "web", "node_modules", ".bin", "next");
      if (fs.existsSync(nextBin)) {
        return [nextBin, "start", "-p", "3777"];
      }
      return null;
    },
    cwd: () => {
      const root = getAppRoot();
      const standalone = path.join(root, "web-standalone", "apps", "web");
      if (fs.existsSync(path.join(standalone, "server.js"))) return standalone;
      return path.join(root, "apps", "web");
    },
    env: () => ({ PORT: "3777", HOSTNAME: "127.0.0.1", PICOS_API_URL: "http://127.0.0.1:8865" }),
    healthUrl: "http://127.0.0.1:3777",
    healthInterval: 15000,
    dependsOn: ["api"],
    managed: true,
  },
  {
    name: "mcp",
    getCommand: () => {
      const py = findPython();
      return [py, "-m", "services.api.src.praxo_picos_api.mcp.runner", "--port", "8870"];
    },
    cwd: () => getAppRoot(),
    healthUrl: "http://127.0.0.1:8870/health",
    healthInterval: 15000,
    dependsOn: ["api"],
    managed: true,
  },
  {
    name: "agent-zero",
    getCommand: () => null,
    healthUrl: "http://127.0.0.1:50001",
    healthInterval: 30000,
    dependsOn: ["api", "mcp"],
    managed: false,
  },
];

class ServiceSupervisor {
  constructor() {
    this._services = new Map();
    this._processes = new Map();
    this._healthTimers = new Map();

    for (const svc of SERVICE_GRAPH) {
      this._services.set(svc.name, {
        ...svc,
        status: "stopped",
        pid: null,
        lastHealthCheck: null,
        restartCount: 0,
      });
    }
  }

  getStatus() {
    const result = {};
    for (const [name, svc] of this._services) {
      result[name] = {
        name: svc.name,
        status: svc.status,
        pid: svc.pid,
        lastHealthCheck: svc.lastHealthCheck,
        restartCount: svc.restartCount,
        managed: svc.managed,
      };
    }
    return result;
  }

  getStartOrder() {
    const resolved = [];
    const visited = new Set();
    const resolve = (name) => {
      if (visited.has(name)) return;
      visited.add(name);
      const svc = this._services.get(name);
      if (!svc) return;
      for (const dep of svc.dependsOn) resolve(dep);
      resolved.push(name);
    };
    for (const name of this._services.keys()) resolve(name);
    return resolved;
  }

  async startAll() {
    const order = this.getStartOrder();
    for (const name of order) {
      const svc = this._services.get(name);
      if (svc && svc.managed) {
        await this.start(name);
        await new Promise((r) => setTimeout(r, 2000));
      }
      this._startHealthPolling(name);
    }
  }

  async start(name) {
    const svc = this._services.get(name);
    if (!svc) return;

    const command = svc.getCommand ? svc.getCommand() : null;
    if (!command) {
      svc.status = "not_configured";
      return;
    }

    const cwd = svc.cwd ? svc.cwd() : getAppRoot();
    const extraEnv = svc.env ? svc.env() : {};

    try {
      const proc = spawn(command[0], command.slice(1), {
        stdio: ["pipe", "pipe", "pipe"],
        detached: false,
        cwd,
        env: { ...process.env, PYTHONPATH: getAppRoot(), ...extraEnv },
      });

      this._processes.set(name, proc);
      svc.pid = proc.pid;
      svc.status = "starting";

      proc.stdout?.on("data", (d) => {
        const line = d.toString().trim();
        if (line) console.log(`[${name}] ${line}`);
      });
      proc.stderr?.on("data", (d) => {
        const line = d.toString().trim();
        if (line) console.error(`[${name}] ${line}`);
      });
      proc.on("exit", (code) => {
        svc.status = code === 0 ? "stopped" : "crashed";
        svc.pid = null;
        this._processes.delete(name);
      });
      proc.on("error", (err) => {
        svc.status = "error";
        svc.pid = null;
        console.error(`[${name}] spawn error: ${err.message}`);
      });
    } catch (err) {
      svc.status = "error";
      console.error(`[${name}] failed to start: ${err.message}`);
    }
  }

  async stop(name) {
    const proc = this._processes.get(name);
    if (proc) {
      proc.kill("SIGTERM");
      await new Promise((r) => setTimeout(r, 2000));
      if (!proc.killed) proc.kill("SIGKILL");
      this._processes.delete(name);
    }
    const svc = this._services.get(name);
    if (svc) { svc.status = "stopped"; svc.pid = null; }
  }

  async restart(name) { await this.stop(name); await this.start(name); }

  async restartAll() {
    const order = this.getStartOrder();
    for (const name of [...order].reverse()) await this.stop(name);
    await this.startAll();
  }

  async stopAll() {
    for (const timer of this._healthTimers.values()) clearInterval(timer);
    this._healthTimers.clear();
    const order = this.getStartOrder();
    for (const name of [...order].reverse()) await this.stop(name);
  }

  _startHealthPolling(name) {
    const svc = this._services.get(name);
    if (!svc || !svc.healthUrl) return;
    const timer = setInterval(async () => {
      try {
        const healthy = await this._checkHealth(svc.healthUrl);
        svc.lastHealthCheck = new Date().toISOString();
        svc.status = healthy ? "running" : "unhealthy";
      } catch { svc.status = "unreachable"; }
    }, svc.healthInterval);
    this._healthTimers.set(name, timer);
  }

  _checkHealth(url) {
    return new Promise((resolve) => {
      const req = http.get(url, { timeout: 3000 }, (res) => {
        resolve(res.statusCode >= 200 && res.statusCode < 400);
      });
      req.on("error", () => resolve(false));
      req.on("timeout", () => { req.destroy(); resolve(false); });
    });
  }
}

module.exports = { ServiceSupervisor, SERVICE_GRAPH };
