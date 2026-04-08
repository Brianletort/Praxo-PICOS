/**
 * First-launch setup: creates Python venv and installs dependencies.
 * Runs once, takes ~30 seconds, then never again.
 */
const { execSync } = require("child_process");
const path = require("path");
const fs = require("fs");
const os = require("os");

function getAppRoot() {
  try {
    const { app } = require("electron");
    if (app.isPackaged) return path.join(process.resourcesPath, "app");
  } catch {}
  return path.resolve(__dirname, "..", "..", "..");
}

function getDataDir() {
  return path.join(os.homedir(), "Library", "Application Support", "Praxo-PICOS");
}

function isSetupComplete() {
  const marker = path.join(getDataDir(), "setup-complete");
  return fs.existsSync(marker);
}

function markSetupComplete() {
  const dataDir = getDataDir();
  fs.mkdirSync(dataDir, { recursive: true });
  fs.writeFileSync(path.join(dataDir, "setup-complete"), new Date().toISOString());
}

function findSystemPython() {
  for (const cmd of ["python3.14", "python3.13", "python3.12", "python3"]) {
    try {
      const version = execSync(`${cmd} --version`, { encoding: "utf8", timeout: 5000 }).trim();
      if (version) return cmd;
    } catch {}
  }
  return null;
}

async function runSetup(onProgress) {
  if (isSetupComplete()) return { status: "already_complete" };

  const root = getAppRoot();
  const dataDir = getDataDir();
  const venvDir = path.join(dataDir, "venv");

  onProgress?.("Checking for Python...");
  const python = findSystemPython();
  if (!python) {
    return {
      status: "error",
      message: "Python 3.12+ is required. Install it from python.org or via Homebrew: brew install python@3.14",
    };
  }

  onProgress?.("Creating Python environment...");
  fs.mkdirSync(venvDir, { recursive: true });

  try {
    execSync(`${python} -m venv "${venvDir}"`, { timeout: 30000, cwd: root });
  } catch (e) {
    return { status: "error", message: `Failed to create venv: ${e.message}` };
  }

  onProgress?.("Installing dependencies (this takes ~30 seconds)...");
  const pip = path.join(venvDir, "bin", "pip");
  try {
    execSync(`"${pip}" install --upgrade pip -q`, { timeout: 60000, cwd: root });
    const pyproject = path.join(root, "pyproject.toml");
    if (fs.existsSync(pyproject)) {
      execSync(`"${pip}" install "${root}" -q`, { timeout: 120000, cwd: root });
    }
  } catch (e) {
    return { status: "error", message: `Failed to install dependencies: ${e.message}` };
  }

  markSetupComplete();
  onProgress?.("Setup complete!");
  return { status: "complete", venvDir };
}

module.exports = { runSetup, isSetupComplete, findSystemPython, getDataDir };
