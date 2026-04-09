const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const {
  getInitialWindowUrl,
  getWebServiceEnv,
  waitForApiHealth,
  startPackagedRuntime,
} = require("../runtime");

describe("desktop runtime helpers", () => {
  describe("getInitialWindowUrl", () => {
    it("returns onboarding route for first run", () => {
      assert.equal(
        getInitialWindowUrl({
          isDev: false,
          firstRun: true,
          devUrl: "http://127.0.0.1:3100",
          packagedUrl: "http://127.0.0.1:3777",
        }),
        "http://127.0.0.1:3777/onboarding",
      );
    });

    it("returns base route after first run", () => {
      assert.equal(
        getInitialWindowUrl({
          isDev: false,
          firstRun: false,
          devUrl: "http://127.0.0.1:3100",
          packagedUrl: "http://127.0.0.1:3777",
        }),
        "http://127.0.0.1:3777",
      );
    });
  });

  describe("getWebServiceEnv", () => {
    it("enables Electron run-as-node mode", () => {
      const env = getWebServiceEnv();
      assert.equal(env.ELECTRON_RUN_AS_NODE, "1");
      assert.equal(env.PORT, "3777");
      assert.equal(env.HOSTNAME, "127.0.0.1");
    });
  });

  describe("waitForApiHealth", () => {
    it("returns true when API responds OK on first attempt", async () => {
      const result = await waitForApiHealth({
        fetchFn: async () => ({ ok: true }),
        sleep: async () => {},
        maxAttempts: 3,
        intervalMs: 1,
      });
      assert.equal(result, true);
    });

    it("retries until API responds OK", async () => {
      let attempt = 0;
      const result = await waitForApiHealth({
        fetchFn: async () => {
          attempt++;
          if (attempt < 3) throw new Error("ECONNREFUSED");
          return { ok: true };
        },
        sleep: async () => {},
        maxAttempts: 5,
        intervalMs: 1,
      });
      assert.equal(result, true);
      assert.equal(attempt, 3);
    });

    it("returns false after exhausting attempts", async () => {
      const result = await waitForApiHealth({
        fetchFn: async () => { throw new Error("ECONNREFUSED"); },
        sleep: async () => {},
        maxAttempts: 3,
        intervalMs: 1,
      });
      assert.equal(result, false);
    });
  });

  describe("startPackagedRuntime", () => {
    it("waits for API health between startAll and createWindow", async () => {
      const calls = [];

      await startPackagedRuntime({
        isSetupComplete: () => false,
        runSetup: async (onProgress) => {
          calls.push("runSetup");
          onProgress("Installing dependencies");
          return { status: "complete" };
        },
        supervisor: {
          startAll: async () => {
            calls.push("startAll");
          },
        },
        healingEngine: {
          start: () => {
            calls.push("healingStart");
          },
        },
        createWindow: (url) => {
          calls.push(`createWindow:${url}`);
        },
        initialUrl: "http://127.0.0.1:3777/onboarding",
        checkFullDiskAccess: () => false,
        requestFullDiskAccess: () => {
          calls.push("requestFullDiskAccess");
        },
        waitForHealth: async () => {
          calls.push("waitForHealth");
          return true;
        },
        setPromptTimer: (fn, ms) => {
          calls.push(`setPromptTimer:${ms}`);
          fn();
        },
        log: () => {},
        error: () => {},
      });

      assert.deepEqual(calls, [
        "runSetup",
        "startAll",
        "healingStart",
        "waitForHealth",
        "createWindow:http://127.0.0.1:3777/onboarding",
        "setPromptTimer:5000",
        "requestFullDiskAccess",
      ]);
    });
  });
});
