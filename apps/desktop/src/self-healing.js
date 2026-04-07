const { exec } = require("child_process");

const MAX_RESTART_ATTEMPTS = 5;
const BACKOFF_BASE_MS = 1000;
const BACKOFF_MAX_MS = 16000;
const HEALTH_CHECK_INTERVAL_MS = 15000;

class SelfHealingEngine {
  constructor(supervisor) {
    this._supervisor = supervisor;
    this._running = false;
    this._timer = null;
    this._log = [];
    this._restartAttempts = new Map();
  }

  start() {
    this._running = true;
    this._timer = setInterval(() => this._healingLoop(), HEALTH_CHECK_INTERVAL_MS);
    this._logAction("Self-healing engine started");
  }

  stop() {
    this._running = false;
    if (this._timer) {
      clearInterval(this._timer);
      this._timer = null;
    }
    this._logAction("Self-healing engine stopped");
  }

  getLog() {
    return [...this._log];
  }

  async _healingLoop() {
    if (!this._running) return;

    const status = this._supervisor.getStatus();
    for (const [name, svc] of Object.entries(status)) {
      if (svc.status === "unhealthy" || svc.status === "unreachable") {
        await this._handleUnhealthy(name, svc);
      } else if (svc.status === "running") {
        this._restartAttempts.set(name, 0);
      }
    }
  }

  async _handleUnhealthy(name, svc) {
    const attempts = this._restartAttempts.get(name) || 0;

    if (attempts >= MAX_RESTART_ATTEMPTS) {
      this._logAction(`${name}: max restart attempts (${MAX_RESTART_ATTEMPTS}) reached — needs attention`);
      return;
    }

    const portConflict = await this._checkPortConflict(name);
    if (portConflict) {
      this._logAction(`${name}: port conflict detected — ${portConflict}`);
      return;
    }

    const backoff = Math.min(BACKOFF_BASE_MS * Math.pow(2, attempts), BACKOFF_MAX_MS);
    this._logAction(`${name}: unhealthy, restarting (attempt ${attempts + 1}/${MAX_RESTART_ATTEMPTS}, backoff ${backoff}ms)`);

    await new Promise((r) => setTimeout(r, backoff));

    try {
      await this._supervisor.restart(name);
      this._restartAttempts.set(name, attempts + 1);
    } catch (err) {
      this._logAction(`${name}: restart failed — ${err.message}`);
      this._restartAttempts.set(name, attempts + 1);
    }
  }

  _checkPortConflict(name) {
    const portMap = {
      api: 8865,
      web: 3777,
      mcp: 8870,
      qdrant: 6733,
    };

    const port = portMap[name];
    if (!port) return Promise.resolve(null);

    return new Promise((resolve) => {
      exec(`lsof -i :${port} -t`, (err, stdout) => {
        if (err || !stdout.trim()) {
          resolve(null);
          return;
        }
        const pids = stdout.trim().split("\n");
        resolve(`Port ${port} in use by PID(s): ${pids.join(", ")}`);
      });
    });
  }

  async checkPermissions() {
    const results = {
      fullDiskAccess: "unknown",
      accessibility: "unknown",
      screenRecording: "unknown",
    };

    try {
      const { execSync } = require("child_process");
      const fdaCheck = execSync(
        'sqlite3 "/Library/Application Support/com.apple.TCC/TCC.db" "SELECT client FROM access WHERE service=\'kTCCServiceSystemPolicyAllFiles\'" 2>/dev/null',
        { encoding: "utf8", timeout: 3000 }
      ).trim();
      results.fullDiskAccess = fdaCheck ? "granted" : "not_granted";
    } catch {
      results.fullDiskAccess = "unknown";
    }

    return results;
  }

  openPermissionSettings(type) {
    const urls = {
      fullDiskAccess: "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles",
      accessibility: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
      screenRecording: "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture",
    };

    const url = urls[type];
    if (url) {
      require("electron").shell.openExternal(url);
    }
  }

  _logAction(message) {
    const entry = {
      timestamp: new Date().toISOString(),
      message,
    };
    this._log.push(entry);
    if (this._log.length > 500) {
      this._log = this._log.slice(-250);
    }
  }
}

module.exports = { SelfHealingEngine };
