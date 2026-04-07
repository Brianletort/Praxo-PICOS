const { describe, it, beforeEach } = require("node:test");
const assert = require("node:assert/strict");
const { SelfHealingEngine } = require("../self-healing");

function createMockSupervisor() {
  return {
    _statuses: {
      api: { status: "running", managed: true },
      qdrant: { status: "running", managed: false },
    },
    getStatus() {
      return { ...this._statuses };
    },
    async restart(name) {
      this._statuses[name] = { ...this._statuses[name], status: "running" };
    },
  };
}

describe("SelfHealingEngine", () => {
  let engine;
  let supervisor;

  beforeEach(() => {
    supervisor = createMockSupervisor();
    engine = new SelfHealingEngine(supervisor);
  });

  it("starts and stops cleanly", () => {
    engine.start();
    assert.equal(engine._running, true);
    engine.stop();
    assert.equal(engine._running, false);
  });

  it("logs start and stop actions", () => {
    engine.start();
    engine.stop();
    const log = engine.getLog();
    assert.ok(log.some((e) => e.message.includes("started")));
    assert.ok(log.some((e) => e.message.includes("stopped")));
  });

  it("log entries have timestamps", () => {
    engine.start();
    engine.stop();
    const log = engine.getLog();
    for (const entry of log) {
      assert.ok(entry.timestamp);
      assert.ok(new Date(entry.timestamp).getTime() > 0);
    }
  });

  it("returns a copy of log (not the internal array)", () => {
    engine.start();
    engine.stop();
    const log1 = engine.getLog();
    const log2 = engine.getLog();
    assert.notEqual(log1, log2);
    assert.deepEqual(log1, log2);
  });

  it("detects unhealthy services and logs restart", async () => {
    engine._running = true;
    supervisor._statuses.api = { status: "unhealthy", managed: true };
    await engine._healingLoop();
    const log = engine.getLog();
    assert.ok(log.some((e) => e.message.includes("api") && e.message.includes("restarting")));
  });

  it("resets restart counter when service recovers", async () => {
    engine._running = true;
    supervisor._statuses.api = { status: "unhealthy", managed: true };
    await engine._healingLoop();
    assert.equal(engine._restartAttempts.get("api"), 1);

    supervisor._statuses.api = { status: "running", managed: true };
    await engine._healingLoop();
    assert.equal(engine._restartAttempts.get("api"), 0);
  });

  it("stops restarting after max attempts", async () => {
    engine._running = true;
    engine._restartAttempts.set("api", 5);
    supervisor._statuses.api = { status: "unhealthy", managed: true };
    await engine._healingLoop();
    const log = engine.getLog();
    assert.ok(log.some((e) => e.message.includes("needs attention")));
  });
});
