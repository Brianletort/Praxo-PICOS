const { spawn } = require("child_process");
const http = require("http");

const SERVICE_GRAPH = [
  {
    name: "qdrant",
    command: null,
    healthUrl: "http://127.0.0.1:6733/healthz",
    healthInterval: 10000,
    dependsOn: [],
    managed: false,
  },
  {
    name: "api",
    command: null,
    healthUrl: "http://127.0.0.1:8865/health",
    healthInterval: 10000,
    dependsOn: ["qdrant"],
    managed: true,
  },
  {
    name: "workers",
    command: null,
    healthUrl: null,
    healthInterval: 30000,
    dependsOn: ["api", "qdrant"],
    managed: true,
  },
  {
    name: "web",
    command: null,
    healthUrl: "http://127.0.0.1:3777",
    healthInterval: 15000,
    dependsOn: ["api"],
    managed: true,
  },
  {
    name: "mcp",
    command: null,
    healthUrl: "http://127.0.0.1:8870/health",
    healthInterval: 15000,
    dependsOn: ["api"],
    managed: true,
  },
  {
    name: "agent-zero",
    command: null,
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
      for (const dep of svc.dependsOn) {
        resolve(dep);
      }
      resolved.push(name);
    };

    for (const name of this._services.keys()) {
      resolve(name);
    }
    return resolved;
  }

  async startAll() {
    const order = this.getStartOrder();
    for (const name of order) {
      const svc = this._services.get(name);
      if (svc && svc.managed) {
        await this.start(name);
      }
      this._startHealthPolling(name);
    }
  }

  async start(name) {
    const svc = this._services.get(name);
    if (!svc || !svc.command) {
      svc.status = "not_configured";
      return;
    }

    try {
      const proc = spawn(svc.command[0], svc.command.slice(1), {
        stdio: "pipe",
        detached: false,
      });
      this._processes.set(name, proc);
      svc.pid = proc.pid;
      svc.status = "starting";

      proc.on("exit", (code) => {
        svc.status = "stopped";
        svc.pid = null;
        this._processes.delete(name);
      });
    } catch (err) {
      svc.status = "error";
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
    if (svc) {
      svc.status = "stopped";
      svc.pid = null;
    }
  }

  async restart(name) {
    await this.stop(name);
    await this.start(name);
  }

  async restartAll() {
    const order = this.getStartOrder();
    for (const name of [...order].reverse()) {
      await this.stop(name);
    }
    await this.startAll();
  }

  async stopAll() {
    for (const timer of this._healthTimers.values()) {
      clearInterval(timer);
    }
    this._healthTimers.clear();

    const order = this.getStartOrder();
    for (const name of [...order].reverse()) {
      await this.stop(name);
    }
  }

  _startHealthPolling(name) {
    const svc = this._services.get(name);
    if (!svc || !svc.healthUrl) return;

    const timer = setInterval(async () => {
      try {
        const healthy = await this._checkHealth(svc.healthUrl);
        svc.lastHealthCheck = new Date().toISOString();
        svc.status = healthy ? "running" : "unhealthy";
      } catch {
        svc.status = "unreachable";
      }
    }, svc.healthInterval);

    this._healthTimers.set(name, timer);
  }

  _checkHealth(url) {
    return new Promise((resolve) => {
      const req = http.get(url, { timeout: 3000 }, (res) => {
        resolve(res.statusCode >= 200 && res.statusCode < 400);
      });
      req.on("error", () => resolve(false));
      req.on("timeout", () => {
        req.destroy();
        resolve(false);
      });
    });
  }
}

module.exports = { ServiceSupervisor, SERVICE_GRAPH };
