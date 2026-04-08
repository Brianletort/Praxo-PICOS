const { describe, it, beforeEach } = require("node:test");
const assert = require("node:assert/strict");
const { ServiceSupervisor, SERVICE_GRAPH } = require("../supervisor");

describe("ServiceSupervisor", () => {
  let supervisor;

  beforeEach(() => {
    supervisor = new ServiceSupervisor();
  });

  describe("getStartOrder", () => {
    it("returns services in dependency order", () => {
      const order = supervisor.getStartOrder();
      const qdrantIdx = order.indexOf("qdrant");
      const apiIdx = order.indexOf("api");
      const workersIdx = order.indexOf("workers");
      const webIdx = order.indexOf("web");

      assert.ok(qdrantIdx < apiIdx, "qdrant must start before api");
      assert.ok(apiIdx < workersIdx, "api must start before workers");
      assert.ok(apiIdx < webIdx, "api must start before web");
    });

    it("includes all services", () => {
      const order = supervisor.getStartOrder();
      assert.equal(order.length, SERVICE_GRAPH.length);
    });
  });

  describe("getStatus", () => {
    it("returns status for all services", () => {
      const status = supervisor.getStatus();
      const names = Object.keys(status);
      assert.ok(names.includes("api"));
      assert.ok(names.includes("qdrant"));
      assert.ok(names.includes("web"));
      assert.ok(names.includes("mcp"));
      assert.ok(names.includes("agent-zero"));
    });

    it("all services start as stopped", () => {
      const status = supervisor.getStatus();
      for (const svc of Object.values(status)) {
        assert.equal(svc.status, "stopped");
      }
    });

    it("reports managed flag correctly", () => {
      const status = supervisor.getStatus();
      assert.equal(status.qdrant.managed, true, "qdrant is managed (bundled)");
      assert.equal(status.api.managed, true, "api is managed");
      assert.equal(status["agent-zero"].managed, false, "agent-zero is not managed");
    });
  });

  describe("SERVICE_GRAPH", () => {
    it("has no circular dependencies", () => {
      const visited = new Set();
      const stack = new Set();

      function hasCycle(name) {
        if (stack.has(name)) return true;
        if (visited.has(name)) return false;
        visited.add(name);
        stack.add(name);
        const svc = SERVICE_GRAPH.find((s) => s.name === name);
        if (svc) {
          for (const dep of svc.dependsOn) {
            if (hasCycle(dep)) return true;
          }
        }
        stack.delete(name);
        return false;
      }

      for (const svc of SERVICE_GRAPH) {
        assert.ok(!hasCycle(svc.name), `Circular dependency involving ${svc.name}`);
      }
    });

    it("all dependencies reference existing services", () => {
      const names = new Set(SERVICE_GRAPH.map((s) => s.name));
      for (const svc of SERVICE_GRAPH) {
        for (const dep of svc.dependsOn) {
          assert.ok(names.has(dep), `${svc.name} depends on unknown service: ${dep}`);
        }
      }
    });
  });
});
