const { describe, it, beforeEach } = require("node:test");
const assert = require("node:assert/strict");
const { DockerManager, CONTAINER_NAME, AGENT_ZERO_IMAGE } = require("../docker-manager");

describe("DockerManager", () => {
  let manager;

  beforeEach(() => {
    manager = new DockerManager({ dataDir: "/tmp/picos-test-agent-zero" });
  });

  it("checks docker installation", () => {
    const result = manager.isDockerInstalled();
    assert.equal(typeof result, "boolean");
  });

  it("returns MCP config with correct host", () => {
    const config = manager.getMcpConfig();
    assert.equal(config.type, "remote");
    assert.ok(config.url.includes("host.docker.internal"));
    assert.ok(config.url.includes("8870"));
  });

  it("logs actions with timestamps", async () => {
    manager._logAction("test action");
    const log = manager.getLog();
    assert.equal(log.length, 1);
    assert.equal(log[0].message, "test action");
    assert.ok(log[0].timestamp);
  });

  it("returns copy of log", () => {
    manager._logAction("test");
    const log1 = manager.getLog();
    const log2 = manager.getLog();
    assert.notEqual(log1, log2);
    assert.deepEqual(log1, log2);
  });

  it("trims log when it gets too large", () => {
    for (let i = 0; i < 250; i++) {
      manager._logAction(`action ${i}`);
    }
    const log = manager.getLog();
    assert.ok(log.length <= 200);
  });

  it("container name is deterministic", () => {
    assert.equal(CONTAINER_NAME, "praxo-picos-agent-zero");
  });

  it("image reference is set", () => {
    assert.ok(AGENT_ZERO_IMAGE.includes("agent-zero"));
  });
});
