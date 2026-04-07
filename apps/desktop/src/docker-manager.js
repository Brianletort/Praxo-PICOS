const { exec, execSync } = require("child_process");
const path = require("path");
const os = require("os");

const AGENT_ZERO_IMAGE = "frdel/agent-zero-run:latest";
const CONTAINER_NAME = "praxo-picos-agent-zero";
const AGENT_ZERO_PORT = 50001;
const MCP_HOST_PORT = 8870;

class DockerManager {
  constructor(options = {}) {
    this._dataDir = options.dataDir || path.join(
      os.homedir(),
      "Library/Application Support/Praxo-PICOS/AgentZero"
    );
    this._log = [];
  }

  isDockerInstalled() {
    try {
      execSync("docker --version", { stdio: "pipe", timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  isDockerRunning() {
    try {
      execSync("docker info", { stdio: "pipe", timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  async getContainerStatus() {
    if (!this.isDockerInstalled()) {
      return { status: "docker_not_installed" };
    }
    if (!this.isDockerRunning()) {
      return { status: "docker_not_running" };
    }

    return new Promise((resolve) => {
      exec(
        `docker inspect --format='{{.State.Status}}' ${CONTAINER_NAME}`,
        { timeout: 5000 },
        (err, stdout) => {
          if (err) {
            resolve({ status: "not_created" });
            return;
          }
          const state = stdout.trim().replace(/'/g, "");
          resolve({ status: state, containerName: CONTAINER_NAME });
        }
      );
    });
  }

  async pullImage() {
    this._logAction("Pulling Agent Zero image...");
    return new Promise((resolve, reject) => {
      exec(`docker pull ${AGENT_ZERO_IMAGE}`, { timeout: 300000 }, (err, stdout) => {
        if (err) {
          this._logAction(`Pull failed: ${err.message}`);
          reject(err);
          return;
        }
        this._logAction("Image pulled successfully");
        resolve(stdout);
      });
    });
  }

  async createContainer() {
    const { mkdirSync } = require("fs");
    mkdirSync(this._dataDir, { recursive: true });

    const cmd = [
      "docker create",
      `--name ${CONTAINER_NAME}`,
      `-p ${AGENT_ZERO_PORT}:${AGENT_ZERO_PORT}`,
      `-v "${this._dataDir}/usr:/a0/usr"`,
      `--add-host=host.docker.internal:host-gateway`,
      AGENT_ZERO_IMAGE,
    ].join(" ");

    this._logAction("Creating Agent Zero container...");
    return new Promise((resolve, reject) => {
      exec(cmd, { timeout: 30000 }, (err, stdout) => {
        if (err) {
          this._logAction(`Create failed: ${err.message}`);
          reject(err);
          return;
        }
        this._logAction("Container created");
        resolve(stdout.trim());
      });
    });
  }

  async start() {
    const status = await this.getContainerStatus();

    if (status.status === "docker_not_installed") {
      throw new Error("Docker is not installed. Please install Docker Desktop first.");
    }
    if (status.status === "docker_not_running") {
      throw new Error("Docker is not running. Please start Docker Desktop.");
    }
    if (status.status === "not_created") {
      await this.pullImage();
      await this.createContainer();
    }

    this._logAction("Starting Agent Zero...");
    return new Promise((resolve, reject) => {
      exec(`docker start ${CONTAINER_NAME}`, { timeout: 30000 }, (err) => {
        if (err) {
          this._logAction(`Start failed: ${err.message}`);
          reject(err);
          return;
        }
        this._logAction("Agent Zero started");
        resolve();
      });
    });
  }

  async stop() {
    this._logAction("Stopping Agent Zero...");
    return new Promise((resolve) => {
      exec(`docker stop ${CONTAINER_NAME}`, { timeout: 15000 }, (err) => {
        if (err) {
          this._logAction(`Stop warning: ${err.message}`);
        } else {
          this._logAction("Agent Zero stopped");
        }
        resolve();
      });
    });
  }

  async remove() {
    await this.stop();
    return new Promise((resolve) => {
      exec(`docker rm ${CONTAINER_NAME}`, { timeout: 10000 }, () => resolve());
    });
  }

  async healthCheck() {
    const containerStatus = await this.getContainerStatus();
    if (containerStatus.status !== "running") {
      return {
        status: containerStatus.status,
        healthy: false,
        url: `http://127.0.0.1:${AGENT_ZERO_PORT}`,
      };
    }

    return new Promise((resolve) => {
      const http = require("http");
      const req = http.get(`http://127.0.0.1:${AGENT_ZERO_PORT}`, { timeout: 5000 }, (res) => {
        resolve({
          status: "running",
          healthy: res.statusCode >= 200 && res.statusCode < 400,
          url: `http://127.0.0.1:${AGENT_ZERO_PORT}`,
        });
      });
      req.on("error", () => resolve({ status: "running", healthy: false, url: `http://127.0.0.1:${AGENT_ZERO_PORT}` }));
      req.on("timeout", () => { req.destroy(); resolve({ status: "running", healthy: false }); });
    });
  }

  getMcpConfig() {
    return {
      type: "remote",
      url: `http://host.docker.internal:${MCP_HOST_PORT}/mcp`,
      description: "Praxo-PICOS Memory Tools",
    };
  }

  getLog() {
    return [...this._log];
  }

  _logAction(message) {
    this._log.push({ timestamp: new Date().toISOString(), message });
    if (this._log.length > 200) this._log = this._log.slice(-100);
  }
}

module.exports = { DockerManager, CONTAINER_NAME, AGENT_ZERO_IMAGE };
