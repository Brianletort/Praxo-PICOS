"""Self-healing regression tests using the desktop supervisor module."""
import importlib.util
import os
import sys

import pytest

_DESKTOP_SRC = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "apps", "desktop", "src")
)
if _DESKTOP_SRC not in sys.path:
    sys.path.insert(0, _DESKTOP_SRC)


def _load_desktop_self_healing():
    """Load apps/desktop/src/self_healing.py without colliding with this test package name."""
    path = os.path.join(_DESKTOP_SRC, "self_healing.py")
    spec = importlib.util.spec_from_file_location("picos_desktop_self_healing", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.regression
class TestServiceRecovery:
    def _get_supervisor(self):
        from supervisor import ServiceSupervisor

        return ServiceSupervisor()

    def _get_healing_engine(self, supervisor):
        mod = _load_desktop_self_healing()
        return mod.SelfHealingEngine(supervisor)

    def test_supervisor_dependency_order_never_starts_child_before_parent(self):
        sup = self._get_supervisor()
        order = sup.getStartOrder()
        seen: set[str] = set()
        status = sup.getStatus()
        for name in order:
            svc = status[name]
            _ = svc
            deps: list[str] = []
            from supervisor import SERVICE_GRAPH

            for s in SERVICE_GRAPH:
                if s["name"] == name:
                    deps = s["dependsOn"]
                    break
            for dep in deps:
                assert dep in seen, f"{name} scheduled before its dependency {dep}"
            seen.add(name)

    def test_all_services_start_as_stopped(self):
        sup = self._get_supervisor()
        status = sup.getStatus()
        for name, svc in status.items():
            assert svc["status"] == "stopped", f"{name} should start as stopped"

    def test_healing_engine_logs_actions(self):
        sup = self._get_supervisor()
        mod = _load_desktop_self_healing()
        engine = mod.SelfHealingEngine(sup)
        engine.start()
        engine.stop()
        log = engine.getLog()
        assert len(log) >= 2
        assert any("started" in e["message"] for e in log)
        assert any("stopped" in e["message"] for e in log)
