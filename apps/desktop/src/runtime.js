function getInitialWindowUrl({
  isDev,
  firstRun,
  devUrl = "http://127.0.0.1:3100",
  packagedUrl = "http://127.0.0.1:3777",
}) {
  const baseUrl = isDev ? devUrl : packagedUrl;
  return firstRun ? `${baseUrl}/onboarding` : baseUrl;
}

function getWebServiceEnv({
  apiUrl = "http://127.0.0.1:8865",
  hostname = "127.0.0.1",
  port = "3777",
} = {}) {
  return {
    ELECTRON_RUN_AS_NODE: "1",
    HOSTNAME: hostname,
    PICOS_API_URL: apiUrl,
    PORT: port,
  };
}

async function waitForApiHealth({
  url = "http://127.0.0.1:8865/health",
  maxAttempts = 15,
  intervalMs = 2000,
  fetchFn = globalThis.fetch,
  sleep = (ms) => new Promise((r) => setTimeout(r, ms)),
  log = () => {},
} = {}) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const res = await fetchFn(url);
      if (res.ok) {
        log(`[health] API ready after ${(i + 1) * intervalMs / 1000}s`);
        return true;
      }
    } catch {}
    await sleep(intervalMs);
  }
  log("[health] API did not become ready in time");
  return false;
}

async function startPackagedRuntime({
  isSetupComplete,
  runSetup,
  supervisor,
  healingEngine,
  createWindow,
  initialUrl,
  checkFullDiskAccess,
  requestFullDiskAccess,
  setPromptTimer = setTimeout,
  log = () => {},
  error = () => {},
  fullDiskAccessDelayMs = 5000,
  waitForHealth = waitForApiHealth,
}) {
  if (!isSetupComplete()) {
    log("[setup] Running first-launch setup...");
    const result = await runSetup((message) => log(`[setup] ${message}`));
    if (result.status === "error") {
      error("[setup] Setup failed:", result.message);
    }
  }

  await supervisor.startAll();
  healingEngine.start();

  await waitForHealth({ log });

  createWindow(initialUrl);

  setPromptTimer(() => {
    if (!checkFullDiskAccess()) {
      requestFullDiskAccess();
    }
  }, fullDiskAccessDelayMs);
}

module.exports = {
  getInitialWindowUrl,
  getWebServiceEnv,
  waitForApiHealth,
  startPackagedRuntime,
};
