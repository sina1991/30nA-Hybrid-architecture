import os
from pathlib import Path
import subprocess
import sys
import unittest


class DaemonFaultInjectionGuardTests(unittest.TestCase):
    def test_fault_injection_refuses_to_run_without_explicit_opt_in(self):
        repository_root = Path(__file__).resolve().parents[3]
        script = repository_root / "scripts" / "security" / "run_sandbox_daemon_fault_injection.py"
        env = os.environ.copy()
        env.pop("SANDBOX_FAULT_INJECTION_ACK", None)
        env["DOCKER_HOST"] = f"unix:///run/user/{os.getuid()}/docker.sock"
        result = subprocess.run(
            [sys.executable, str(script), "sha256:" + "a" * 64],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Explicit opt-in required", result.stderr)
        self.assertNotIn("SecurityOptions", result.stderr)


if __name__ == "__main__":
    unittest.main()
