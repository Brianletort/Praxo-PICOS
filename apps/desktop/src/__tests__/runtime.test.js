const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const {
  getInitialWindowUrl,
  getWebServiceEnv,
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

  describe("startPackagedRuntime", () => {
    it("starts services before creating the window", async () => {
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
        setPromptTimer: (fn, ms) => {
          calls.push(`setPromptTimer:${ms}`);
          fn();
        },
        log: (message) => {
          calls.push(`log:${message}`);
        },
        error: (...args) => {
          calls.push(`error:${args.join(" ")}`);
        },
      });

      assert.deepEqual(calls, [
        "log:[setup] Running first-launch setup...",
        "runSetup",
        "log:[setup] Installing dependencies",
        "startAll",
        "healingStart",
        "createWindow:http://127.0.0.1:3777/onboarding",
        "setPromptTimer:5000",
        "requestFullDiskAccess",
      ]);
    });
  });
});
